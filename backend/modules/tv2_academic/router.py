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
# Lấy API Key từ file .env (Bảo mật, chống khóa Key)
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

class AIQuizRequest(BaseModel):
    topic: str
    num_questions: int = 5

# Schema nhận dữ liệu sửa bộ đề
class QuizUpdateModel(BaseModel):
    title: str
    questions: List[dict]

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

# --- API MỚI BỔ SUNG: LẤY LỊCH SỬ ĐIỂM DANH CHO PHỤ HUYNH ---
@router.get("/attendance/{child_id}")
async def get_student_attendance(child_id: str):
    """API lấy lịch sử điểm danh của một học sinh cụ thể từ bảng journals"""
    # Lấy các nhật ký giảng dạy, sắp xếp mới nhất lên đầu
    cursor = db["journals"].find().sort("created_at", -1)
    history = []
    
    async for journal in cursor:
        att_list = journal.get("attendance", [])
        if not isinstance(att_list, list):
            continue
            
        # Tìm học sinh trong mảng attendance của ca dạy này
        for att in att_list:
            sid = att.get("Mã HS") or att.get("student_id") or att.get("id")
            if sid == child_id:
                # 1. Trích xuất ngày
                created_at = journal.get("created_at")
                if isinstance(created_at, datetime):
                    date_str = created_at.strftime("%d/%m/%Y")
                else:
                    date_str = journal.get("date", datetime.now().strftime("%d/%m/%Y"))
                    
                # 2. Trích xuất môn học/chủ đề
                subject = journal.get("subject") or journal.get("topic") or journal.get("class_name", "Chưa rõ môn học")
                
                # 3. Trích xuất trạng thái
                status = "Có mặt" # Mặc định
                if att.get("Có mặt") is True: status = "Có mặt"
                elif att.get("Vắng") is True or att.get("Vắng mặt") is True: status = "Vắng mặt"
                elif att.get("Đi trễ") is True: status = "Đi trễ"
                elif "status" in att: status = att["status"]
                
                # 4. Trích xuất nhận xét
                remark = att.get("Nhận Xét (Tùy chọn)") or att.get("Nhận Xét") or att.get("remark") or ""
                
                history.append({
                    "Ngày": date_str,
                    "Môn Học": subject,
                    "Trạng Thái": status,
                    "Nhận Xét": remark
                })
                break # Đã tìm thấy học sinh trong ca dạy này thì bỏ qua các dòng khác của ca đó
                
    return history
# -------------------------------------------------------------

@router.post("/generate-quiz")
async def generate_quiz(request: AIQuizRequest):
    """API gọi Gemini AI thật để sinh câu hỏi trắc nghiệm (Đã Bọc Thép Cứng)"""
    if not GEMINI_API_KEY:
        print("❌ LỖI BACKEND: Không tìm thấy GEMINI_API_KEY!")
        raise HTTPException(status_code=500, detail="Chưa có GEMINI_API_KEY trong file .env của Backend!")
        
    try:
        model = genai.GenerativeModel('gemini-2.5-flash')
        prompt = f"""
        Bạn là một giáo viên chuyên nghiệp. Hãy soạn {request.num_questions} câu hỏi trắc nghiệm THỰC TẾ về chủ đề: "{request.topic}".
        Trả về DUY NHẤT một mảng JSON, không markdown, không giải thích thêm.
        Cấu trúc bắt buộc: [{{"question": "...", "options": ["A. ", "B. ", "C. ", "D. "], "correct_answer": "..."}}]
        """
        response = model.generate_content(prompt)
        raw_text = response.text.strip()
        
        # IN RA TERMINAL ĐỂ DEBUG (Cực kỳ quan trọng để biết AI nó phản hồi cái quái gì)
        print(f"\n--- [DEBUG] AI RESPONSE CHO CHỦ ĐỀ '{request.topic}' ---\n{raw_text}\n---------------------------------------------------")
        
        # LÀM SẠCH CHUỖI CỰC MẠNH: Tránh lỗi AI chèn text thừa
        raw_text = raw_text.replace("```json", "").replace("```", "").strip()
        start_idx = raw_text.find('[')
        end_idx = raw_text.rfind(']') + 1
        
        if start_idx == -1 or end_idx == 0:
            raise ValueError("AI không trả về định dạng mảng JSON.")
            
        clean_json_string = raw_text[start_idx:end_idx]
        questions = json.loads(clean_json_string)
        
        return {"questions": questions}
        
    except json.JSONDecodeError as e:
        print(f"❌ LỖI JSON DECODE: {str(e)}")
        raise HTTPException(status_code=500, detail="AI trả về cấu trúc JSON bị lỗi. Vui lòng bấm tạo lại.")
    except Exception as e:
        print(f"❌ LỖI GỌI AI: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Lỗi hệ thống/AI: {str(e)}")

# ================= QUẢN LÝ BỘ ĐỀ QUIZ =================
@router.post("/quizzes", status_code=status.HTTP_201_CREATED)
async def create_quiz(quiz_data: dict):
    """API nhận và lưu bộ Quiz từ Frontend vào MongoDB"""
    import uuid
    # Tự động tạo ID ngẫu nhiên cho bộ đề nếu chưa có
    if "id" not in quiz_data:
        quiz_data["id"] = f"quiz_{uuid.uuid4().hex[:8]}"
        
    result = await db["quizzes"].insert_one(quiz_data)
    return {"message": "Đã lưu bộ Quiz thành công!", "id": str(result.inserted_id)}

@router.get("/quizzes")
async def get_quizzes():
    """API lấy danh sách Quiz từ MongoDB"""
    # Lấy tất cả quiz, bỏ đi trường '_id' mặc định của Mongo để đỡ lỗi JSON
    quizzes = await db["quizzes"].find({}, {"_id": 0}).sort("created_at", -1).to_list(100)
    return quizzes

@router.get("/quizzes/results")
async def get_quiz_results():
    """API lấy kết quả bài tập của học sinh (Fix lỗi 405 Method Not Allowed)"""
    # Tạm thời trả về dữ liệu mẫu để Form Frontend hoạt động
    # Sau này ông code xong chức năng thi thì Query Database ở đây nhé!
    return [
        {"student_name": "Nguyễn Văn An", "quiz_title": "Thì hiện tại đơn", "score": "9/10", "date": "12/05/2026"},
        {"student_name": "Trần Thị Bình", "quiz_title": "Từ vựng Con Vật", "score": "10/10", "date": "13/05/2026"}
    ]

@router.delete("/quizzes/{quiz_id}")
async def delete_quiz(quiz_id: str, author: str):
    """API Xóa đề: Chỉ người tạo mới được xóa"""
    quiz = await db["quizzes"].find_one({"id": quiz_id})
    if not quiz:
        raise HTTPException(status_code=404, detail="Không tìm thấy bộ đề")
    
    # Kiểm tra quyền tác giả
    if quiz.get("author_email") != author and quiz.get("author") != author:
        raise HTTPException(status_code=403, detail="Cảnh báo: Bạn không có quyền xóa bộ đề của giáo viên khác!")
    
    await db["quizzes"].delete_one({"id": quiz_id})
    return {"message": "Đã xóa bộ đề thành công"}

@router.put("/quizzes/{quiz_id}")
async def update_quiz(quiz_id: str, author: str, data: QuizUpdateModel):
    """API Sửa đề: Chỉ người tạo mới được sửa"""
    quiz = await db["quizzes"].find_one({"id": quiz_id})
    if not quiz:
        raise HTTPException(status_code=404, detail="Không tìm thấy bộ đề")
    
    # Kiểm tra quyền tác giả
    if quiz.get("author_email") != author and quiz.get("author") != author:
        raise HTTPException(status_code=403, detail="Cảnh báo: Bạn không có quyền sửa bộ đề của giáo viên khác!")
    
    await db["quizzes"].update_one(
        {"id": quiz_id},
        {"$set": {
            "title": data.title, 
            "questions": data.questions,
            "updated_at": datetime.now()
        }}
    )
    return {"message": "Đã cập nhật bộ đề thành công"}

# ==================================================

@router.post("/assign-quiz")
async def assign_quiz(assignment: QuizAssignmentModel):
    """API lưu thông Đài giao bài tập vào Database"""
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

# Schema nhận dữ liệu từ Frontend
class CommentModel(BaseModel):
    author: str
    text: str

class LikeModel(BaseModel):
    username: str

# Model nhận dữ liệu nộp bài Quiz
class QuizSubmitModel(BaseModel):
    quiz_id: str
    exp_earned: int
    score: float

@router.post("/videos/{video_id}/comments")
async def add_video_comment(video_id: str, comment: CommentModel):
    """API Lưu bình luận mới vào MongoDB"""
    await db["ai_videos"].update_one(
        {"id": video_id},
        {"$push": {"comments": comment.model_dump()}}
    )
    return {"message": "Đã thêm bình luận thành công"}

@router.post("/videos/{video_id}/like")
async def toggle_video_like(video_id: str, payload: LikeModel):
    """API Xử lý Like/Hủy Like: 1 user chỉ được 1 lần"""
    video = await db["ai_videos"].find_one({"id": video_id})
    if not video:
        return {"message": "Không tìm thấy video"}
    
    liked_by = video.get("liked_by", [])
    if payload.username in liked_by:
        # Nếu đã Like rồi -> Kéo tên ra khỏi danh sách & Trừ 1 Like
        await db["ai_videos"].update_one(
            {"id": video_id},
            {"$pull": {"liked_by": payload.username}, "$inc": {"likes": -1}}
        )
    else:
        # Nếu chưa Like -> Thêm tên vào danh sách & Cộng 1 Like
        await db["ai_videos"].update_one(
            {"id": video_id},
            {"$push": {"liked_by": payload.username}, "$inc": {"likes": 1}}
        )
    return {"message": "Đã cập nhật lượt thích"}

# ================= CÁC API MỚI CHO TRẠM QUIZ AI =================

@router.get("/student/{username}/profile")
async def get_student_profile(username: str):
    """Lấy thông tin profile học sinh (EXP, bài đã làm) từ DB"""
    profile = await db["students"].find_one({"username": username}, {"_id": 0})
    if not profile:
        return {"username": username, "exp": 0, "completed_tasks": []}
    return profile

@router.post("/student/{username}/submit-quiz")
async def submit_quiz(username: str, payload: QuizSubmitModel):
    """Lưu kết quả làm bài và cộng EXP vĩnh viễn vào DB"""
    # Cập nhật Profile: Cộng EXP và Thêm mã bài vào mảng đã làm (upsert=True để tự tạo nếu user chưa có trong bảng)
    await db["students"].update_one(
        {"username": username},
        {
            "$push": {"completed_tasks": payload.quiz_id},
            "$inc": {"exp": payload.exp_earned}
        },
        upsert=True 
    )
    
    # Lưu vào lịch sử điểm số (tùy chọn để mốt thống kê)
    await db["quiz_results"].insert_one({
        "username": username,
        "quiz_id": payload.quiz_id,
        "score": payload.score,
        "exp_earned": payload.exp_earned,
        "created_at": datetime.now()
    })
    
    return {"message": "Lưu kết quả thành công!"}

# Model nhận dữ liệu hoàn thành Video
class VideoCompleteModel(BaseModel):
    video_id: str
    exp_earned: int

@router.post("/student/{username}/complete-video")
async def complete_video(username: str, payload: VideoCompleteModel):
    """Lưu kết quả xem video và cộng EXP vĩnh viễn vào DB"""
    await db["students"].update_one(
        {"username": username},
        {
            "$push": {"completed_tasks": payload.video_id},
            "$inc": {"exp": payload.exp_earned}
        },
        upsert=True 
    )
    return {"message": "Đã lưu kết quả xem video!"}
# ================= API QUẢN LÝ ĐIỂM SỐ THỰC TẾ =================

@router.post("/grades")
async def save_student_grades(payload: dict):
    """API lưu điểm từ Giáo viên vào Database (Sử dụng Upsert để cập nhật hoặc tạo mới)"""
    class_id = payload.get("class_id")
    grades = payload.get("grades", [])
    
    for g in grades:
        student_id = g.get("student_id")
        # Upsert: Nếu học sinh đã có điểm ở lớp này rồi thì ghi đè, chưa có thì tạo mới
        await db["grades"].update_one(
            {"class_id": class_id, "student_id": student_id},
            {"$set": g},
            upsert=True
        )
    return {"message": "Đã lưu điểm thành công!"}

@router.get("/grades/{student_id}")
async def get_student_grades(student_id: str):
    """API cho Phụ huynh lấy bảng điểm thực tế của học sinh"""
    grades = await db["grades"].find({"student_id": student_id}, {"_id": 0}).to_list(100)
    return grades