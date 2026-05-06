from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

# --- 1. GAMIFICATION (Học sinh) ---
class GamificationProfile(BaseModel):
    student_id: int
    total_coins: int = 0
    lifetime_coins: int = 0
    rank_level: str = "Beginner"
    current_streak: int = 0
    last_active_date: Optional[datetime] = None

class CoinTransaction(BaseModel):
    student_id: int
    amount: int
    transaction_type: str # 'earn' hoặc 'spend'
    source_action: str 
    reference_id: Optional[int] = None
    created_at: datetime = Field(default_factory=datetime.now)

# --- 2. GÓC KỶ NIỆM (Phụ huynh & Học sinh) ---
class MemoryRecord(BaseModel):
    class_id: int
    teacher_id: int
    media_url: str
    media_type: str 
    description: str
    likes: int = 0
    created_at: datetime = Field(default_factory=datetime.now)

# --- 3. ĐĂNG KÝ KHÓA HỌC & KHUYẾN MÃI (Dành cho Phụ huynh) ---
class CoursePackage(BaseModel):
    package_id: int
    package_name: str
    description: str
    price: float
    promotions: Optional[str] = None # Thông tin khuyến mãi
    is_active: bool = True

class CourseRegistration(BaseModel):
    parent_id: int
    student_id: int
    package_id: int
    status: str = "pending" # pending, approved, rejected
    created_at: datetime = Field(default_factory=datetime.now)

# --- 4. CỔNG LIÊN HỆ & REQUEST (Dành cho Phụ huynh) ---
class ContactMessage(BaseModel):
    sender_id: int # ID của phụ huynh
    receiver_id: int # ID của giáo viên hoặc CSKH (operator)
    subject: str # Loại liên hệ: "Hỏi thăm giáo viên", "Xin nghỉ học", "CSKH"
    content: str
    is_read: bool = False
    created_at: datetime = Field(default_factory=datetime.now)

class ContactMessageCreate(BaseModel):
    sender_id: int
    receiver_id: int # Gửi ID giáo viên, hoặc truyền 0 nếu muốn gửi cho bộ phận Vận hành/Hệ thống
    subject: str     # Ví dụ: "Xin nghỉ học ngày 15/05", "Hỏi bài tập Toán"
    content: str