from bson import ObjectId
from datetime import datetime
from typing import Optional


def serialize_notification(noti: dict) -> dict:
    """
    Chuyển ObjectId/datetime sang dạng frontend/mobile đọc được.
    Đồng thời đảm bảo luôn có cả content và message.
    """

    if not noti:
        return noti

    noti = dict(noti)

    if "_id" in noti:
        noti["id"] = str(noti["_id"])
        del noti["_id"]

    for key, value in list(noti.items()):
        if isinstance(value, ObjectId):
            noti[key] = str(value)
        elif isinstance(value, datetime):
            noti[key] = value.isoformat()

    # Chuẩn hóa nội dung thông báo
    content = noti.get("content") or noti.get("message") or ""
    noti["content"] = content
    noti["message"] = content

    # Chuẩn hóa type
    if not noti.get("type"):
        noti["type"] = noti.get("notification_type", "system")

    if not noti.get("sender_id"):
        noti["sender_id"] = "system"

    if not noti.get("sender_role"):
        noti["sender_role"] = "system"

    if not noti.get("sender_name"):
        noti["sender_name"] = "iKids System"

    if "extra_data" not in noti or noti["extra_data"] is None:
        noti["extra_data"] = {}

    if "is_read" not in noti:
        noti["is_read"] = False

    return noti


def normalize_notification_data(noti_data: dict) -> dict:
    """
    Chuẩn hóa dữ liệu trước khi lưu MongoDB.
    Hỗ trợ cả code cũ dùng content và code mới dùng message.
    """

    noti_data = dict(noti_data)

    content = noti_data.get("content") or noti_data.get("message") or ""

    noti_data["content"] = content
    noti_data["message"] = content

    if not noti_data.get("title"):
        noti_data["title"] = "Thông báo iKids"

    if not noti_data.get("type"):
        noti_data["type"] = noti_data.get("notification_type", "system")

    # Bỏ notification_type để tránh dư field, nhưng vẫn giữ type
    noti_data.pop("notification_type", None)

    if not noti_data.get("sender_id"):
        noti_data["sender_id"] = "system"

    if not noti_data.get("sender_role"):
        noti_data["sender_role"] = "system"

    if not noti_data.get("sender_name"):
        noti_data["sender_name"] = "iKids System"

    if not noti_data.get("receiver_id"):
        noti_data["receiver_id"] = "all"

    if "extra_data" not in noti_data or noti_data["extra_data"] is None:
        noti_data["extra_data"] = {}

    noti_data["is_read"] = bool(noti_data.get("is_read", False))
    noti_data["created_at"] = noti_data.get("created_at") or datetime.now()
    noti_data["updated_at"] = datetime.now()

    return noti_data


async def create_notification(db, noti_data: dict):
    """
    Tạo một thông báo mới.
    Dùng được cho:
    - đổi lịch học
    - học phí
    - nạp tiền
    - yêu cầu mua hàng
    - hệ thống
    """

    try:
        noti_data = normalize_notification_data(noti_data)

        if not noti_data.get("receiver_role"):
            return None

        if not noti_data.get("content"):
            noti_data["content"] = "Bạn có một thông báo mới từ iKids."
            noti_data["message"] = noti_data["content"]

        result = await db.notifications.insert_one(noti_data)

        return str(result.inserted_id)

    except Exception as e:
        print(f"🔥 Lỗi tạo notification: {e}")
        return None


async def get_notifications(
    db,
    user_id: str,
    user_role: str,
    limit: int = 50,
    unread_only: bool = False
):
    """
    Lấy thông báo cho một người dùng cụ thể.
    Bao gồm:
    - thông báo cá nhân: receiver_id = user_id
    - thông báo chung theo role: receiver_id = all
    """

    query = {
        "$and": [
            {"receiver_role": user_role},
            {
                "$or": [
                    {"receiver_id": str(user_id)},
                    {"receiver_id": "all"}
                ]
            }
        ]
    }

    if unread_only:
        query["$and"].append({"is_read": {"$ne": True}})

    cursor = db.notifications.find(query).sort("created_at", -1).limit(limit)
    notifications = await cursor.to_list(length=limit)

    return [serialize_notification(noti) for noti in notifications]


async def get_sent_notifications(db, sender_id: str, limit: int = 50):
    """
    Lấy lịch sử thông báo đã gửi.
    Dành cho admin/operator kiểm tra.
    """

    cursor = db.notifications.find(
        {"sender_id": str(sender_id)}
    ).sort("created_at", -1).limit(limit)

    notifications = await cursor.to_list(length=limit)

    return [serialize_notification(noti) for noti in notifications]


async def count_unread_notifications(db, user_id: str, user_role: str):
    """
    Đếm thông báo chưa đọc.
    """

    query = {
        "$and": [
            {"receiver_role": user_role},
            {"is_read": {"$ne": True}},
            {
                "$or": [
                    {"receiver_id": str(user_id)},
                    {"receiver_id": "all"}
                ]
            }
        ]
    }

    return await db.notifications.count_documents(query)


async def mark_notification_as_read(db, noti_id: str):
    """
    Đánh dấu một thông báo là đã đọc.
    """

    try:
        result = await db.notifications.update_one(
            {"_id": ObjectId(noti_id)},
            {
                "$set": {
                    "is_read": True,
                    "read_at": datetime.now(),
                    "updated_at": datetime.now()
                }
            }
        )

        return result.matched_count > 0

    except Exception:
        return False


async def mark_all_notifications_as_read(db, user_id: str, user_role: str):
    """
    Đánh dấu tất cả thông báo của user là đã đọc.
    """

    query = {
        "$and": [
            {"receiver_role": user_role},
            {
                "$or": [
                    {"receiver_id": str(user_id)},
                    {"receiver_id": "all"}
                ]
            }
        ]
    }

    result = await db.notifications.update_many(
        query,
        {
            "$set": {
                "is_read": True,
                "read_at": datetime.now(),
                "updated_at": datetime.now()
            }
        }
    )

    return result.modified_count


async def delete_notification(db, noti_id: str):
    """
    Xóa một thông báo.
    """

    try:
        result = await db.notifications.delete_one(
            {"_id": ObjectId(noti_id)}
        )

        return result.deleted_count > 0

    except Exception:
        return False