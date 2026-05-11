from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

# --- 1. TÀI CHÍNH & TÀI KHOẢN (Học sinh & Phụ huynh) ---
class GamificationProfile(BaseModel):
    student_id: str 
    balance: float = 0.0 
    rank_level: str = "Beginner"
    last_active_date: Optional[datetime] = None

class DepositRequest(BaseModel):
    """Yêu cầu nạp tiền trực tiếp"""
    user_id: str
    amount: float = Field(..., gt=0) 

class PurchaseRequest(BaseModel):
    """Yêu cầu mua sản phẩm học liệu"""
    user_id: str  
    product_id: int

# --- 2. GÓC KỶ NIỆM (Phụ huynh & Học sinh) ---
class MemoryRecord(BaseModel):
    class_id: int
    teacher_name: str 
    media_url: str
    description: str
    likes: int = 0
    created_at: datetime = Field(default_factory=datetime.now)

# --- 3. ĐĂNG KÝ KHÓA HỌC & KHUYẾN MÃI ---
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
    status: str = "pending" 
    created_at: datetime = Field(default_factory=datetime.now)

# --- 4. CỔNG LIÊN HỆ & REQUEST (CẬP NHẬT TRƯỜNG AMOUNT) ---
class ContactMessageCreate(BaseModel):
    sender_id: str
    receiver_id: str 
    subject: str     
    content: str
    # QUAN TRỌNG: Thêm trường này để nhận số tiền báo cáo từ Phụ huynh
    amount: Optional[float] = 0.0 

class ContactMessage(ContactMessageCreate):
    is_read: bool = False
    created_at: datetime = Field(default_factory=datetime.now)