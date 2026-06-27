from fastapi import APIRouter, Depends, HTTPException, Query
from core.database import get_db
from .models import NotificationCreate
from .services import (
    create_notification,
    get_notifications,
    get_sent_notifications,
    mark_notification_as_read,
    mark_all_notifications_as_read,
    count_unread_notifications,
    delete_notification,
)

# Không đặt prefix ở đây.
# Prefix nên được include trong main.py, ví dụ:
# app.include_router(notification_router, prefix="/api/notifications")
router = APIRouter(tags=["Notifications"])


@router.post("/send")
async def send_notification(
    noti: NotificationCreate,
    db=Depends(get_db)
):
    """
    Gửi thông báo mới.
    Hỗ trợ cả content và message.
    """

    if hasattr(noti, "model_dump"):
        noti_dict = noti.model_dump()
    else:
        noti_dict = noti.dict()

    noti_id = await create_notification(db, noti_dict)

    if noti_id:
        return {
            "status": "success",
            "message": "Gửi thông báo thành công",
            "id": noti_id
        }

    raise HTTPException(
        status_code=400,
        detail="Không thể gửi thông báo"
    )


@router.get("/receive/{user_id}/{user_role}")
async def fetch_my_notifications(
    user_id: str,
    user_role: str,
    limit: int = Query(default=50, ge=1, le=200),
    unread_only: bool = Query(default=False),
    db=Depends(get_db)
):
    """
    Lấy danh sách thông báo của tôi.
    """

    return await get_notifications(
        db=db,
        user_id=user_id,
        user_role=user_role,
        limit=limit,
        unread_only=unread_only
    )


@router.get("/unread-count/{user_id}/{user_role}")
async def fetch_unread_count(
    user_id: str,
    user_role: str,
    db=Depends(get_db)
):
    """
    Đếm số thông báo chưa đọc.
    """

    count = await count_unread_notifications(
        db=db,
        user_id=user_id,
        user_role=user_role
    )

    return {
        "status": "success",
        "count": count
    }


@router.get("/sent/{sender_id}")
async def fetch_sent_history(
    sender_id: str,
    limit: int = Query(default=50, ge=1, le=200),
    db=Depends(get_db)
):
    """
    Lấy lịch sử thông báo tôi đã gửi.
    """

    return await get_sent_notifications(
        db=db,
        sender_id=sender_id,
        limit=limit
    )


@router.put("/{noti_id}/read")
async def mark_as_read(
    noti_id: str,
    db=Depends(get_db)
):
    """
    Đánh dấu một thông báo là đã đọc.
    """

    success = await mark_notification_as_read(db, noti_id)

    if success:
        return {"status": "success"}

    raise HTTPException(
        status_code=404,
        detail="Không tìm thấy thông báo"
    )


@router.put("/read-all/{user_id}/{user_role}")
async def mark_all_as_read(
    user_id: str,
    user_role: str,
    db=Depends(get_db)
):
    """
    Đánh dấu tất cả thông báo của user là đã đọc.
    """

    modified_count = await mark_all_notifications_as_read(
        db=db,
        user_id=user_id,
        user_role=user_role
    )

    return {
        "status": "success",
        "modified_count": modified_count
    }


@router.delete("/{noti_id}")
async def delete_one_notification(
    noti_id: str,
    db=Depends(get_db)
):
    """
    Xóa một thông báo.
    """

    success = await delete_notification(db, noti_id)

    if success:
        return {"status": "success"}

    raise HTTPException(
        status_code=404,
        detail="Không tìm thấy thông báo"
    )