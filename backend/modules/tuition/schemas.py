# Backend/modules/tuition/schemas.py

from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import datetime


class TuitionEnrollmentCreate(BaseModel):
    """
    Phụ huynh đăng ký lớp cho học sinh và chọn gói học phí.
    billing_plan:
    - monthly: đóng theo tháng
    - cycle: đóng theo chu kỳ
    - yearly: đóng cả năm
    """

    parent_id: str
    student_id: str
    class_id: str

    billing_plan: str = "monthly"
    start_date: Optional[str] = None

    pay_registration_now: bool = False
    pay_first_invoice_now: bool = False

    @validator("billing_plan")
    def validate_billing_plan(cls, v):
        valid_values = ["monthly", "cycle", "yearly"]
        if v not in valid_values:
            raise ValueError("billing_plan phải là monthly, cycle hoặc yearly.")
        return v


class TuitionPayInvoiceRequest(BaseModel):
    """
    Phụ huynh đóng học phí bằng ví balance.
    """

    invoice_id: str
    parent_id: str


class TuitionManualInvoiceCreate(BaseModel):
    """
    Admin/operator tạo hóa đơn học phí thủ công nếu cần.
    """

    parent_id: str
    student_id: str
    class_id: str
    class_name: str

    student_name: Optional[str] = None

    invoice_type: str = "monthly"
    period_label: str
    period_start: Optional[str] = None
    period_end: Optional[str] = None

    amount: float
    currency: str = "VND"
    due_date: str
    note: Optional[str] = None

    @validator("invoice_type")
    def validate_invoice_type(cls, v):
        valid_values = ["registration", "monthly", "cycle", "yearly", "other"]
        if v not in valid_values:
            raise ValueError(
                "invoice_type phải là registration, monthly, cycle, yearly hoặc other."
            )
        return v

    @validator("amount", pre=True, always=True)
    def validate_amount(cls, v):
        value = float(v or 0)
        if value <= 0:
            raise ValueError("Số tiền hóa đơn phải lớn hơn 0.")
        return value


class TuitionUpdateInvoiceStatus(BaseModel):
    """
    Admin/operator cập nhật trạng thái hóa đơn thủ công.
    """

    status: str
    note: Optional[str] = None

    @validator("status")
    def validate_status(cls, v):
        valid_values = ["pending", "paid", "overdue", "cancelled"]
        if v not in valid_values:
            raise ValueError("status phải là pending, paid, overdue hoặc cancelled.")
        return v


class TuitionCreateNextInvoiceRequest(BaseModel):
    """
    Tạo hóa đơn kỳ tiếp theo cho một enrollment.
    """

    enrollment_id: str


class TuitionReminderRunRequest(BaseModel):
    """
    Chạy nhắc học phí.
    dry_run=True thì chỉ xem danh sách sẽ nhắc, không tạo notification.
    """

    dry_run: bool = False


class TuitionInvoiceFilter(BaseModel):
    parent_id: Optional[str] = None
    student_id: Optional[str] = None
    class_id: Optional[str] = None
    status: Optional[str] = None


class TuitionResponse(BaseModel):
    status: str = "success"
    message: Optional[str] = None
    id: Optional[str] = None
    data: Optional[dict] = None


class TuitionListResponse(BaseModel):
    status: str = "success"
    total: int = 0
    items: List[dict] = Field(default_factory=list)


class TuitionReminderResult(BaseModel):
    status: str = "success"
    checked: int = 0
    reminded: int = 0
    overdue_updated: int = 0
    items: List[dict] = Field(default_factory=list)