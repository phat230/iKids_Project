from fastapi import APIRouter, Depends, HTTPException
from core.database import get_db
from core.security import get_current_user  # Import lính gác
from .services import add_coins_service
from .schemas import RewardRedeem

router = APIRouter()

@router.get("/dashboard")
async def get_my_dashboard(
    db = Depends(get_db), 
    current_user: dict = Depends(get_current_user) # Yêu cầu phải có Token hợp lệ
):
    """Lấy Dashboard của chính User đang đăng nhập"""
    # Chỉ parent và student được xem dashboard này
    if current_user["role"] not in ["student", "parent"]:
        raise HTTPException(status_code=403, detail="Chỉ học sinh và phụ huynh được xem trang này.")
    
    student_id = str(current_user["user_id"])
    
    profile = await db.gamification_profiles.find_one({"student_id": student_id})
    transactions = await db.coin_transactions.find({"student_id": student_id}).sort("created_at", -1).to_list(length=5)
    
    return {"profile": profile, "recent_transactions": transactions}