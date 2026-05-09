from fastapi import APIRouter, HTTPException, status
from typing import List
from .models import TeachingJournalModel, VideoAIModel

router = APIRouter(prefix="/academic", tags=["TV2 - Academic & Teacher"])

@router.get("/videos", response_model=List[VideoAIModel])
async def get_ai_videos():
    """API lấy danh sách video AI trong kho học liệu"""
    # TODO: await db["videos"].find({"is_active": True}).to_list(100)
    return []

@router.post("/journal", status_code=status.HTTP_201_CREATED)
async def submit_teaching_journal(journal: TeachingJournalModel):
    """
    API nộp nhật ký giảng dạy và điểm danh sau buổi học.
    Khi nộp thành công, hệ thống cần trigger event cộng EXP cho học sinh (bên TV3).
    """
    # 1. Lưu nhật ký vào DB
    # result = await db["journals"].insert_one(journal.model_dump())
    
    # 2. Gọi logic hoặc Notification đẩy qua TV3 để cộng EXP cho học sinh đi học đầy đủ
    # ... logic gửi thông báo ...

    return {"message": "Đã lưu nhật ký giảng dạy và điểm danh thành công!"}
# Thêm vào backend/modules/tv2_academic/router.py
from pydantic import BaseModel

class AIQuizRequest(BaseModel):
    topic: str
    num_questions: int = 5

@router.post("/generate-quiz")
async def generate_quiz(request: AIQuizRequest):
    """
    API giả lập AI sinh câu hỏi. 
    Trong thực tế, bạn sẽ ném request.topic vào prompt của ChatGPT/Gemini tại đây.
    """
    # MOCK DATA giả lập kết quả trả về từ AI
    mock_questions = []
    for i in range(1, request.num_questions + 1):
        mock_questions.append({
            "question": f"Câu hỏi AI {i} về chủ đề: {request.topic}",
            "options": ["Đáp án A (Đúng)", "Đáp án B", "Đáp án C", "Đáp án D"],
            "correct_answer": "Đáp án A (Đúng)"
        })
    
    return {"questions": mock_questions}

from .models import QuizModel
@router.post("/quiz", status_code=status.HTTP_201_CREATED)
async def create_quiz(quiz: QuizModel):
    """API lưu bộ câu hỏi vào Database"""
    # result = await db["quizzes"].insert_one(quiz.model_dump())
    return {"message": "Đã lưu bộ Quiz thành công!"}
@router.post("/assign-quiz")
async def assign_quiz(assignment: QuizAssignmentModel):
    """API lưu thông tin giao bài tập cho một lớp cụ thể"""
    # result = await db["assignments"].insert_one(assignment.model_dump())
    return {"message": f"Đã giao bài tập thành công cho lớp {assignment.class_id}"}