from pydantic import BaseModel
from typing import Optional

class TeacherRequestCreate(BaseModel):
    teacher_name: str
    class_name: str
    type: str  # Ví dụ: Xin nghỉ dạy, Xin đổi ca 
    reason: str
    date: str