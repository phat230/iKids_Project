from fastapi import APIRouter, HTTPException, status
from typing import List
import json
import google.generativeai as genai
from pydantic import BaseModel
import os
from datetime import datetime

# Import database từ core
from core.database import database as db
# Import models (đảm bảo ông đã định nghĩa các Class này trong file models.py)
from .models import TeachingJournalModel, VideoAIModel, QuizModel, QuizAssignmentModel

router = APIRouter(prefix="/api/tv2", tags=["TV2 - Academic & Teacher"])

# ================= CẤU HÌNH AI (BACKEND) =================
# Khuyên ông nên để trong file .env, ở đây tui dán tạm theo yêu cầu của ông
GEMINI_API_KEY = "AIzaSyCD2KeHK88MBx2H_A7TOZQZhKGKW4ibCSo"
genai.configure(api_key=GEMINI_API_KEY)

class AIQuizRequest(BaseModel):
    topic: str
    num_questions: int = 5

# ================= API CHỨC NĂNG =================

@router.get("/videos")
async def get_ai_videos():
    """API lấy danh sách video AI thật từ MongoDB"""
    # Đã thêm {"_id": 0} để MongoDB ẩn cái ObjectId đi, giúp FastAPI không bị lỗi
    videos = await db["ai_videos"].find({"is_active": True}, {"_id": 0}).to_list(100)
    return videos

@router.post("/journal", status_code=status.HTTP_201_CREATED)
async def submit_teaching_journal(journal: TeachingJournalModel):
    """API nộp nhật ký giảng dạy và điểm danh vào MongoDB"""
    journal_data = journal.model_dump()
    journal_data["created_at"] = datetime.now()
    
    result = await db["journals"].insert_one(journal_data)
    
    # 2. Chỗ này sau này TV1 và TV3 sẽ viết thêm logic cộng EXP dựa trên nhật ký này
    return {"message": "Đã lưu nhật ký giảng dạy và điểm danh thành công!", "id": str(result.inserted_id)}

@router.post("/generate-quiz")
async def generate_quiz(request: AIQuizRequest):
    """API gọi Gemini AI thật để sinh câu hỏi trắc nghiệm"""
    try:
        model = genai.GenerativeModel('gemini-2.5-flash')
        prompt = f"""
        Bạn là một giáo viên chuyên nghiệp. Hãy soạn {request.num_questions} câu hỏi trắc nghiệm THỰC TẾ về chủ đề: "{request.topic}".
        Trả về DUY NHẤT một mảng JSON, không markdown.
        Cấu trúc: [{{"question": "...", "options": ["A. ", "B. ", "C. ", "D. "], "correct_answer": "..."}}]
        """
        response = model.generate_content(prompt)
        raw_text = response.text.strip()
        
        # Làm sạch chuỗi JSON nếu AI trả về kèm tag ```json
        if "```json" in raw_text:
            raw_text = raw_text.split("```json")[1].split("```")[0].strip()
        
        questions = json.loads(raw_text)
        return {"questions": questions}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi AI: {str(e)}")

@router.post("/quiz", status_code=status.HTTP_201_CREATED)
async def create_quiz(quiz: QuizModel):
    """API lưu bộ Quiz vào MongoDB"""
    quiz_data = quiz.model_dump()
    result = await db["quizzes"].insert_one(quiz_data)
    return {"message": "Đã lưu bộ Quiz thành công!", "id": str(result.inserted_id)}

@router.post("/assign-quiz")
async def assign_quiz(assignment: QuizAssignmentModel):
    """API lưu thông tin giao bài tập vào Database"""
    result = await db["assignments"].insert_one(assignment.model_dump())
    return {"message": f"Đã giao bài tập thành công cho lớp {assignment.class_id}"}
@router.post("/videos", status_code=status.HTTP_201_CREATED)
async def add_video(video_data: dict):
    """API lưu Video AI mới vào MongoDB"""
    import uuid
    # Tạo ID ngẫu nhiên cho video
    video_data["id"] = f"vid_{uuid.uuid4().hex[:8]}"
    
    # Quan trọng: Thêm cờ is_active = True để API GET có thể tìm thấy nó
    video_data["is_active"] = True 
    
    result = await db["ai_videos"].insert_one(video_data)
    return {"message": "Đã lưu Video AI thành công!", "id": str(result.inserted_id)}
@router.get("/quizzes")
async def get_quizzes():
    """API lấy danh sách Quiz từ MongoDB"""
    # Lấy tất cả quiz, bỏ đi trường '_id' mặc định của Mongo để đỡ lỗi JSON
    quizzes = await db["quizzes"].find({}, {"_id": 0}).sort("created_at", -1).to_list(100)
    return quizzes