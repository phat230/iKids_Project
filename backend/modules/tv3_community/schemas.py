from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

# --- 1. TÀI CHÍNH & TÀI KHOẢN (Học sinh & Phụ huynh) ---
class GamificationProfile(BaseModel):
    student_id: str # ID dạng chuỗi từ MongoDB
    balance: float = 0.0 # Số dư tiền mặt VNĐ thay cho total_coins[cite: 6]
    rank_level: str = "Beginner"
    last_active_date: Optional[datetime] = None

class DepositRequest(BaseModel):
    """Yêu cầu nạp tiền vào tài khoản[cite: 6]"""
    user_id: str
    amount: float = Field(..., gt=0) # Số tiền phải lớn hơn 0

class PurchaseRequest(BaseModel):
    """Yêu cầu mua sản phẩm học liệu[cite: 6]"""
    user_id: str  
    product_id: int

# --- 2. GÓC KỶ NIỆM (Phụ huynh & Học sinh) ---
class MemoryRecord(BaseModel):
    class_id: int
    teacher_name: str # Chuyển sang lưu tên để hiển thị nhanh[cite: 7]
    media_url: str
    description: str
    likes: int = 0
    created_at: datetime = Field(default_factory=datetime.now)

# --- 3. ĐĂNG KÝ KHÓA HỌC & KHUYẾN MÃI (Dành cho Phụ huynh) ---
class CoursePackage(BaseModel):
    package_id: int
    package_name: str
    description: str
    price: float
    promotions: Optional[str] = None 
    is_active: bool = True

class CourseRegistration(BaseModel):
    parent_id: str
    student_id: str
    package_id: int
    status: str = "pending" # pending, approved, rejected
    created_at: datetime = Field(default_factory=datetime.now)

# --- 4. CỔNG LIÊN HỆ & REQUEST (Dành cho Phụ huynh) ---
class ContactMessageCreate(BaseModel):
    sender_id: str
    receiver_id: str # Gửi ID giáo viên, hoặc truyền "0" cho Vận hành[cite: 6]
    subject: str     # Ví dụ: "Xin nghỉ học ngày 15/05"[cite: 5]
    content: str

class ContactMessage(ContactMessageCreate):
    is_read: bool = False
    created_at: datetime = Field(default_factory=datetime.now)