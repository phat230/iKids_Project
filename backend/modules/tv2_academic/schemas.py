from pydantic import BaseModel
from typing import List, Optional

# --- CẤU TRÚC CỦA BÀI TẬP (QUIZ) ---
class QuestionSchema(BaseModel):
    question: str
    options: List[str]
    correct_answer: str

class QuizCreate(BaseModel):
    title: str
    questions: List[QuestionSchema]
    created_at: str

# --- CẤU TRÚC CỦA VIDEO AI ---
class VideoCreate(BaseModel):
    title: str
    url: str
    topic: str
    level: str
    likes: int = 0
    comments: List[str] = []