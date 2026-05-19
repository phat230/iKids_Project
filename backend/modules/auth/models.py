from pydantic import BaseModel, EmailStr, Field
from datetime import datetime
from typing import Optional, List
from enum import Enum

class UserRole(str, Enum):
    ADMIN = "admin"
    OPERATOR = "operator"
    TEACHER = "teacher"
    PARENT = "parent"
    STUDENT = "student"

class UserDBModel(BaseModel):
    name: str
    email: EmailStr
    password: str  
    role: UserRole 
    created_at: datetime = Field(default_factory=datetime.now)
    
    # Mặc định ban đầu là False để chờ xác thực OTP qua SĐT (Trừ khi Admin/Operator tạo trực tiếp)
    is_active: bool = False
    
    # Trường bổ sung nâng cao bảo mật và quản lý độ tuổi
    phone_number: Optional[str] = None
    birth_date: Optional[str] = None  # Lưu định dạng chuỗi ISO (YYYY-MM-DD)
    
    # Cấu trúc lưu mã xác thực OTP tin nhắn điện thoại
    otp_code: Optional[str] = None
    otp_expires_at: Optional[datetime] = None
    
    student_ids_ref: Optional[List[str]] = None
    subjects: Optional[List[str]] = None