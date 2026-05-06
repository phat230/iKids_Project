from fastapi import APIRouter, Depends, HTTPException
from core.database import get_db
from .services import add_coins_service
from .schemas import ContactMessageCreate
from .services import submit_contact_request, get_contact_history
router = APIRouter()

@router.post("/earn-coins")
async def api_earn_coins(student_id: int, action: str, reference_id: int = None, db = Depends(get_db)):
    """
    API dùng để tích hợp chéo. 
    Khi TV2 chấm điểm trắc nghiệm xong hoặc TV1 điểm danh xong, sẽ gọi API này để cộng xu.
    """
    result = await add_coins_service(db, student_id, action, reference_id)
    if result.get("status") == "failed":
        raise HTTPException(status_code=400, detail=result.get("message"))
    return result

@router.get("/gamification/profile/{student_id}")
async def get_gamification_profile(student_id: int, db = Depends(get_db)):
    """API để Frontend lấy thông tin Rank và Số dư Xu hiện tại hiển thị lên Dashboard"""
    profile = await db.gamification_profiles.find_one({"student_id": student_id})
    if not profile:
        # Trả về thông tin mặc định nếu chưa có hồ sơ
        return {"student_id": student_id, "total_coins": 0, "rank_level": "Beginner"}
    
    # Xóa _id của MongoDB trước khi trả về để tránh lỗi JSON
    profile["_id"] = str(profile["_id"])
    return profile
@router.post("/contact/submit")
async def api_submit_contact(request_data: ContactMessageCreate, db = Depends(get_db)):
    """
    API: Phụ huynh gửi yêu cầu xin nghỉ hoặc nhắn tin cho Giáo viên / CSKH.
    Hệ thống sẽ tự động chuyển đổi thành Request xử lý lịch nếu là xin nghỉ học.
    """
    return await submit_contact_request(db, request_data)

@router.get("/contact/history/{parent_id}")
async def api_get_contact_history(parent_id: int, db = Depends(get_db)):
    """
    API: Lấy danh sách lịch sử tin nhắn và trạng thái các yêu cầu phụ huynh đã tạo.
    """
    return await get_contact_history(db, parent_id)