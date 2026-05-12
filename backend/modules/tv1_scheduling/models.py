from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional

class TeacherRequestCreate(BaseModel):
    teacher_name: str
    class_name: str
    type: str  # Ví dụ: Xin nghỉ dạy, Xin đổi ca 
    reason: str
    date: str

# =========================
# MODEL LỊCH HỌC
# =========================
class ClassScheduleModel(BaseModel):
    class_name: str
    subject: str
    teacher_id: str
    teacher_name: str

    study_date: str      # 2026-05-13
    start_time: str      # 18:00
    end_time: str        # 20:00

    room: Optional[str] = "Online"

    created_by: str
    created_at: datetime = Field(default_factory=datetime.now)

    status: str = "active"