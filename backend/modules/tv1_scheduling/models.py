from pydantic import BaseModel, Field, validator
from datetime import datetime
from typing import Optional, List


# =========================
# 1. MODEL LỚP HỌC TRUNG TÂM
# =========================
class ClassModel(BaseModel):
    """
    Dùng cho bảng tạo lớp học của nhân viên vận hành/admin.
    Kết nối học sinh, phụ huynh và giáo viên vào một thực thể duy nhất.

    ĐÃ BỔ SUNG:
    - Phí đăng ký lớp
    - Học phí tháng
    - Học phí theo chu kỳ
    - Học phí cả năm
    - Ngày đến hạn đóng tiền
    - Cấu hình nhắc học phí
    """

    class_name: str
    subject: str
    teacher_id: str
    teacher_name: str

    # Danh sách ID học sinh trong lớp để điểm danh và quản lý
    student_ids: List[str] = Field(default_factory=list)

    # Cho phép hiển thị ở trang lớp học cho phụ huynh đăng ký
    is_public: bool = True

    # Thông tin chi tiết để nhân viên vận hành liên hệ khi cần
    description: Optional[str] = None

    # =========================
    # CẤU HÌNH HỌC PHÍ
    # =========================

    # Bật/tắt chức năng học phí cho lớp này
    tuition_enabled: bool = True

    # Tiền phí đăng ký/ghi danh ban đầu
    registration_fee: float = 0.0

    # Học phí theo tháng
    monthly_fee: float = 0.0

    # Học phí theo chu kỳ, ví dụ 3 tháng/kỳ
    cycle_fee: float = 0.0

    # Số tháng trong 1 chu kỳ
    cycle_months: int = 3

    # Học phí cả năm
    yearly_fee: float = 0.0

    # Cho phép phụ huynh chọn từng hình thức đóng
    allow_registration_fee: bool = True
    allow_monthly_payment: bool = True
    allow_cycle_payment: bool = True
    allow_yearly_payment: bool = True

    # Ngày đến hạn đóng học phí hằng tháng
    # Ví dụ: 5 nghĩa là ngày 05 mỗi tháng
    billing_day: int = 5

    # Số ngày được trễ hạn trước khi đánh dấu quá hạn nghiêm trọng
    grace_days: int = 3

    # Các mốc nhắc trước/ngay/sau hạn:
    # 7: trước 7 ngày
    # 3: trước 3 ngày
    # 0: đúng ngày đến hạn
    # -1: quá hạn 1 ngày
    reminder_days_before: List[int] = Field(default_factory=lambda: [7, 3, 0, -1])

    currency: str = "VND"
    tuition_note: Optional[str] = None

    created_at: datetime = Field(default_factory=datetime.now)
    status: str = "active"  # active, closed

    @validator(
        "registration_fee",
        "monthly_fee",
        "cycle_fee",
        "yearly_fee",
        pre=True,
        always=True,
    )
    def validate_fee_not_negative(cls, v):
        if v is None or v == "":
            return 0.0

        try:
            value = float(v)
        except Exception:
            raise ValueError("Học phí phải là số hợp lệ.")

        if value < 0:
            raise ValueError("Học phí không được nhỏ hơn 0.")

        return value

    @validator("cycle_months", pre=True, always=True)
    def validate_cycle_months(cls, v):
        if v is None or v == "":
            return 3

        value = int(v)

        if value <= 0:
            raise ValueError("Số tháng trong chu kỳ phải lớn hơn 0.")

        return value

    @validator("billing_day", pre=True, always=True)
    def validate_billing_day(cls, v):
        if v is None or v == "":
            return 5

        value = int(v)

        if value < 1 or value > 28:
            raise ValueError("Ngày đến hạn học phí nên nằm trong khoảng từ 1 đến 28.")

        return value

    @validator("grace_days", pre=True, always=True)
    def validate_grace_days(cls, v):
        if v is None or v == "":
            return 3

        value = int(v)

        if value < 0:
            raise ValueError("Số ngày gia hạn không được nhỏ hơn 0.")

        return value


# =========================
# 2. MODEL LỊCH HỌC LIÊN KẾT LỚP
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

    # Lưu các ngày trong tuần, ví dụ: ["Thứ 2", "Thứ 4"]
    days_of_week: List[str] = Field(default_factory=list)

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

    # Loại đơn: xin nghỉ dạy, xin đổi ca, v.v.
    type: str
    reason: str
    date: str

    # Liên kết với ID lịch học cụ thể để nhân viên vận hành dễ dàng chỉnh sửa
    target_schedule_id: Optional[str] = None

    status: str = "pending"  # pending, approved, rejected