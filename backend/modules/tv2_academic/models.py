from pydantic import BaseModel, Field
from datetime import datetime
from typing import List, Optional

# 1. Kho học liệu Video AI
class VideoAIModel(BaseModel):
    title: str
    url: str
    tags: List[str]  # Ví dụ: ["Tiếng Anh", "Lớp 3", "Động vật"]
    likes: int = 0
    created_at: datetime = Field(default_factory=datetime.now)

# 2. Bộ câu hỏi Quiz
class QuizQuestion(BaseModel):
    question: str
    options: List[str]
    correct_answer: str

class QuizModel(BaseModel):
    video_id: Optional[str] = None # Quiz có thể gắn kèm video
    title: str
    questions: List[QuizQuestion]
    created_by: str # ID của Giáo viên tạo
    created_at: datetime = Field(default_factory=datetime.now)

# 3. Nhật ký giảng dạy & Điểm danh
class AttendanceRecord(BaseModel):
    student_id: str
    is_present: bool
    score: Optional[float] = None
    teacher_comment: Optional[str] = None
    emoji_feedback: Optional[str] = None # Đánh giá nhanh bằng Emoji

class TeachingJournalModel(BaseModel):
    class_id: str # Lấy từ module TV1 (Lịch dạy)
    teacher_id: str
    date: datetime = Field(default_factory=datetime.now)
    content_taught: str
    video_used_id: Optional[str] = None
    attendance: List[AttendanceRecord]
class QuizAssignmentModel(BaseModel):
    quiz_id: str
    class_id: str
    teacher_id: str
    deadline: datetime
    assigned_at: datetime = Field(default_factory=datetime.now)
    status: str = "active" # active, closed