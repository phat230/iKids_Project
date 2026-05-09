from pydantic import BaseModel, EmailStr, Field
from datetime import datetime
from typing import Optional, List
from enum import Enum

class UserRole(str, Enum):
    """Định nghĩa 5 role chuẩn của hệ thống iKids"""
    ADMIN = "admin"
    OPERATOR = "operator"
    TEACHER = "teacher"
    PARENT = "parent"
    STUDENT = "student"

class UserDBModel(BaseModel):
    """
    Bản thiết kế đại diện cho 1 Document trong Collection 'users' trên MongoDB.
    """
    name: str
    email: EmailStr
    password: str  # Chứa mật khẩu đã được mã hóa (hashed)
    role: UserRole # Ép kiểu bằng Enum để tránh lỗi nhập sai role
    created_at: datetime = Field(default_factory=datetime.now)
    is_active: bool = True
    
    # Một phụ huynh có thể quản lý nhiều con, và MongoDB dùng str (ObjectId) thay vì int
    student_ids_ref: Optional[List[str]] = None