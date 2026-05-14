from bson import ObjectId
from datetime import datetime

async def create_notification(db, noti_data: dict):
    """Tạo một thông báo mới"""
    noti_data["is_read"] = False
    noti_data["created_at"] = datetime.now()
    
    result = await db.notifications.insert_one(noti_data)
    return str(result.inserted_id)

async def get_notifications(db, user_id: str, user_role: str, limit: int = 50):
    """
    Lấy thông báo cho một người dùng cụ thể.
    Lấy cả thông báo cá nhân (receiver_id = user_id) VÀ thông báo chung của role (receiver_id = "all")
    """
    query = {
        "$and": [
            {"receiver_role": user_role},
            {"$or": [
                {"receiver_id": user_id},
                {"receiver_id": "all"}
            ]}
        ]
    }
    
    cursor = db.notifications.find(query).sort("created_at", -1).limit(limit)
    notifications = await cursor.to_list(length=limit)
    
    # Format lại ID cho Frontend dễ đọc
    for noti in notifications:
        noti["id"] = str(noti["_id"])
        del noti["_id"]
        
    return notifications

async def get_sent_notifications(db, sender_id: str, limit: int = 50):
    """Lấy lịch sử các thông báo đã gửi (Dành cho Admin/Vận hành kiểm tra)"""
    cursor = db.notifications.find({"sender_id": sender_id}).sort("created_at", -1).limit(limit)
    notifications = await cursor.to_list(length=limit)
    for noti in notifications:
        noti["id"] = str(noti["_id"])
        del noti["_id"]
    return notifications

async def mark_notification_as_read(db, noti_id: str):
    """Đánh dấu đã đọc"""
    result = await db.notifications.update_one(
        {"_id": ObjectId(noti_id)},
        {"$set": {"is_read": True}}
    )
    return result.modified_count > 0