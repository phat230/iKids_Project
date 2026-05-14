from fastapi import APIRouter, Depends, HTTPException
from core.database import get_db
from .models import NotificationCreate
from .services import create_notification, get_notifications, get_sent_notifications, mark_notification_as_read

router = APIRouter(prefix="/api/notifications", tags=["Notifications"])

@router.post("/send")
async def send_notification(noti: NotificationCreate, db = Depends(get_db)):
    """Gửi thông báo mới"""
    noti_dict = noti.model_dump()
    noti_id = await create_notification(db, noti_dict)
    if noti_id:
        return {"status": "success", "message": "Gửi thông báo thành công", "id": noti_id}
    raise HTTPException(status_code=400, detail="Không thể gửi thông báo")

@router.get("/receive/{user_id}/{user_role}")
async def fetch_my_notifications(user_id: str, user_role: str, db = Depends(get_db)):
    """Lấy danh sách thông báo của tôi (Nhận)"""
    return await get_notifications(db, user_id, user_role)

@router.get("/sent/{sender_id}")
async def fetch_sent_history(sender_id: str, db = Depends(get_db)):
    """Lấy lịch sử thông báo tôi đã gửi"""
    return await get_sent_notifications(db, sender_id)

@router.put("/{noti_id}/read")
async def mark_as_read(noti_id: str, db = Depends(get_db)):
    """Đánh dấu 1 thông báo là đã đọc"""
    success = await mark_notification_as_read(db, noti_id)
    if success:
        return {"status": "success"}
    raise HTTPException(status_code=404, detail="Không tìm thấy thông báo")