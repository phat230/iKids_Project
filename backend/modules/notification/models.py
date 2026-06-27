from pydantic import BaseModel
from typing import Optional, Any, Dict
from datetime import datetime


class NotificationCreate(BaseModel):
    sender_id: Optional[str] = "system"
    sender_role: Optional[str] = "system"
    sender_name: Optional[str] = "iKids System"

    receiver_id: Optional[str] = "all"
    receiver_role: str


    type: Optional[str] = "system"

    title: str

    content: Optional[str] = None
    message: Optional[str] = None

    related_id: Optional[str] = None

    extra_data: Optional[Dict[str, Any]] = None


class NotificationResponse(BaseModel):
    id: str

    sender_id: Optional[str] = "system"
    sender_role: Optional[str] = "system"
    sender_name: Optional[str] = "iKids System"

    receiver_id: Optional[str] = "all"
    receiver_role: str

    type: Optional[str] = "system"
    title: str
    content: str
    message: Optional[str] = None

    related_id: Optional[str] = None
    extra_data: Optional[Dict[str, Any]] = None

    is_read: bool = False
    created_at: datetime