from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

class NotificationCreate(BaseModel):
    sender_id: str
    sender_role: str        # admin, operator, teacher, student, parent
    sender_name: str
    
    receiver_id: Optional[str] = "all"  # Truyền "all" nếu muốn gửi cho tất cả người trong 1 role
    receiver_role: str      # admin, operator, teacher, student, parent
    
    # Loại thông báo: 'schedule' (lịch), 'message' (tin nhắn), 'finance' (tiền), 'system' (hệ thống), 'request' (đơn từ)
    type: str               
    title: str
    content: str
    
    # ID liên quan (ví dụ: ID của lịch học, ID của lớp, ID của giao dịch) để frontend làm nút "Xem chi tiết"
    related_id: Optional[str] = None 

class NotificationResponse(NotificationCreate):
    id: str
    is_read: bool = False
    created_at: datetime