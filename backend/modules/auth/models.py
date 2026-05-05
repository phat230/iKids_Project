from pydantic import BaseModel, EmailStr, Field
from datetime import datetime
from typing import Optional

class UserDBModel(BaseModel):
    """
    Bản thiết kế đại diện cho 1 Document trong Collection 'users' trên MongoDB.
    """
    name: str
    email: EmailStr
    password: str  # Chứa mật khẩu đã được mã hóa (hashed)
    role: str      # Chấp nhận: student, teacher, admin, operator, parent
    created_at: datetime = Field(default_factory=datetime.now)
    is_active: bool = True
    
    # Có thể mở rộng sau này (VD: lưu ID của con nếu role là parent)
    student_id_ref: Optional[int] = None