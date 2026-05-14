from pydantic import BaseModel, EmailStr, Field
from datetime import datetime
from typing import Optional, List

# =========================
# 1. MODEL LỚP HỌC (TRUNG TÂM)
# =========================
class ClassModel(BaseModel):
    """
    Dùng cho Table tạo lớp học của nhân viên vận hành.
    Kết nối học sinh, phụ huynh và giáo viên vào một thực thể duy nhất.
    """
    class_name: str
    subject: str
    teacher_id: str
    teacher_name: str
    
    # Danh sách ID học sinh trong lớp để điểm danh và quản lý
    student_ids: List[str] = [] 
    
    # Cho phép hiển thị ở trang lớp học cho phụ huynh đăng ký
    is_public: bool = True 
    
    # Thông tin chi tiết để nhân viên vận hành liên hệ khi cần
    description: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.now)
    status: str = "active" # active, closed

# =========================
# 2. MODEL LỊCH HỌC (LIÊN KẾT LỚP)
# =========================
class ClassScheduleModel(BaseModel):
    class_id: str 
    class_name: str
    subject: str
    teacher_id: str
    teacher_name: str

    study_date: str      
    start_time: str      
    end_time: str        
    
    # THÊM DÒNG NÀY ĐỂ LƯU CÁC NGÀY TRONG TUẦN (VD: ["Thứ 2", "Thứ 4"])
    days_of_week: List[str] = [] 

    room: Optional[str] = "Online"
    created_by: str
    created_at: datetime = Field(default_factory=datetime.now)
    status: str = "active"
# =========================
# 3. MODEL YÊU CẦU TỪ GIÁO VIÊN
# =========================
class TeacherRequestCreate(BaseModel):
    """
    Dùng cho yêu cầu chỉnh sửa, xóa lịch học từ giáo viên.
    """
    teacher_id: str
    teacher_name: str
    class_id: str
    class_name: str
    
    # Loại đơn: Xin nghỉ dạy, Xin đổi ca, v.v.
    type: str  
    reason: str
    date: str
    
    # Liên kết với ID lịch học cụ thể để nhân viên vận hành dễ dàng chỉnh sửa
    target_schedule_id: Optional[str] = None 
    status: str = "pending" # pending, approved, rejected