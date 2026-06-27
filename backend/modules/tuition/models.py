from pydantic import BaseModel, Field, validator
from datetime import datetime
from typing import Optional, List


# =========================
# 1. MODEL ĐĂNG KÝ LỚP CÓ HỌC PHÍ
# =========================
class TuitionEnrollmentModel(BaseModel):
    """
    Lưu việc phụ huynh đăng ký lớp cho học sinh.
    Sau khi đăng ký, hệ thống có thể tạo hóa đơn học phí theo gói đã chọn.
    """

    parent_id: str
    student_id: str
    student_name: Optional[str] = None

    class_id: str
    class_name: str
    subject: Optional[str] = None
    teacher_id: Optional[str] = None
    teacher_name: Optional[str] = None

    # monthly, cycle, yearly
    billing_plan: str = "monthly"

    # Ngày bắt đầu học/dùng để tính kỳ học phí
    start_date: str

    # Ngày đến hạn tiếp theo
    next_due_date: Optional[str] = None

    # Snapshot học phí tại thời điểm đăng ký.
    # Dù sau này lớp đổi giá, lịch sử đăng ký cũ vẫn giữ đúng giá ban đầu.
    registration_fee: float = 0.0
    monthly_fee: float = 0.0
    cycle_fee: float = 0.0
    cycle_months: int = 3
    yearly_fee: float = 0.0
    billing_day: int = 5
    currency: str = "VND"

    # Có tạo hóa đơn tự động cho kỳ sau hay không
    auto_create_next_invoice: bool = True

    status: str = "active"  # active, cancelled, completed
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

    @validator("billing_plan")
    def validate_billing_plan(cls, v):
        valid_values = ["monthly", "cycle", "yearly"]
        if v not in valid_values:
            raise ValueError("billing_plan phải là monthly, cycle hoặc yearly.")
        return v

    @validator(
        "registration_fee",
        "monthly_fee",
        "cycle_fee",
        "yearly_fee",
        pre=True,
        always=True,
    )
    def validate_fee(cls, v):
        if v is None or v == "":
            return 0.0

        value = float(v)

        if value < 0:
            raise ValueError("Số tiền không được nhỏ hơn 0.")

        return value


# =========================
# 2. MODEL HÓA ĐƠN HỌC PHÍ
# =========================
class TuitionInvoiceModel(BaseModel):
    """
    Mỗi bản ghi là một hóa đơn học phí:
    - phí đăng ký
    - học phí tháng
    - học phí chu kỳ
    - học phí cả năm
    """

    enrollment_id: Optional[str] = None

    parent_id: str
    student_id: str
    student_name: Optional[str] = None

    class_id: str
    class_name: str

    # registration, monthly, cycle, yearly
    invoice_type: str = "monthly"

    # Ví dụ:
    # "Tháng 07/2026"
    # "Chu kỳ 07/2026 - 09/2026"
    # "Năm học 2026"
    period_label: str

    period_start: Optional[str] = None
    period_end: Optional[str] = None

    amount: float
    currency: str = "VND"

    due_date: str

    # pending, paid, overdue, cancelled
    status: str = "pending"

    paid_at: Optional[datetime] = None
    payment_id: Optional[str] = None

    # Đếm số lần đã nhắc phụ huynh
    reminder_count: int = 0
    last_reminded_at: Optional[datetime] = None

    note: Optional[str] = None

    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

    @validator("invoice_type")
    def validate_invoice_type(cls, v):
        valid_values = ["registration", "monthly", "cycle", "yearly"]
        if v not in valid_values:
            raise ValueError("invoice_type phải là registration, monthly, cycle hoặc yearly.")
        return v

    @validator("amount", pre=True, always=True)
    def validate_amount(cls, v):
        if v is None or v == "":
            raise ValueError("Số tiền hóa đơn không được trống.")

        value = float(v)

        if value <= 0:
            raise ValueError("Số tiền hóa đơn phải lớn hơn 0.")

        return value


# =========================
# 3. MODEL THANH TOÁN HỌC PHÍ
# =========================
class TuitionPaymentModel(BaseModel):
    """
    Lưu lịch sử thanh toán học phí.
    Thanh toán nên trừ từ ví phụ huynh.
    """

    invoice_id: str

    parent_id: str
    student_id: str
    class_id: str

    amount: float
    currency: str = "VND"

    # wallet, manual, payos
    payment_method: str = "wallet"

    balance_before: Optional[float] = None
    balance_after: Optional[float] = None

    # success, failed, refunded
    status: str = "success"

    transaction_code: Optional[str] = None
    note: Optional[str] = None

    created_at: datetime = Field(default_factory=datetime.now)

    @validator("amount", pre=True, always=True)
    def validate_payment_amount(cls, v):
        if v is None or v == "":
            raise ValueError("Số tiền thanh toán không được trống.")

        value = float(v)

        if value <= 0:
            raise ValueError("Số tiền thanh toán phải lớn hơn 0.")

        return value


# =========================
# 4. MODEL LOG NHẮC HỌC PHÍ
# =========================
class TuitionReminderLogModel(BaseModel):
    """
    Lưu lịch sử hệ thống đã gửi nhắc học phí.
    Dùng để tránh gửi nhắc trùng quá nhiều lần.
    """

    invoice_id: str
    parent_id: str
    student_id: str
    class_id: str

    # before_due, due_today, overdue
    reminder_type: str

    # 7: trước 7 ngày
    # 3: trước 3 ngày
    # 0: đúng ngày
    # -1: quá hạn 1 ngày
    days_offset: int

    title: str
    message: str

    notification_id: Optional[str] = None

    sent_at: datetime = Field(default_factory=datetime.now)
    created_at: datetime = Field(default_factory=datetime.now)


# =========================
# 5. SCHEMA REQUEST CHỌN GÓI HỌC PHÍ
# =========================
class TuitionEnrollmentCreate(BaseModel):
    parent_id: str
    student_id: str
    class_id: str

    # monthly, cycle, yearly
    billing_plan: str = "monthly"

    start_date: str

    # Có đóng phí đăng ký ngay không
    pay_registration_now: bool = False

    # Có đóng học phí kỳ đầu ngay không
    pay_first_invoice_now: bool = False

    @validator("billing_plan")
    def validate_plan(cls, v):
        valid_values = ["monthly", "cycle", "yearly"]
        if v not in valid_values:
            raise ValueError("billing_plan phải là monthly, cycle hoặc yearly.")
        return v


class TuitionPayInvoiceRequest(BaseModel):
    invoice_id: str
    parent_id: str