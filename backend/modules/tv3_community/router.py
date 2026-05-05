from fastapi import APIRouter, Depends, HTTPException
from core.database import get_db
from .services import add_coins_service
from .recommender import generate_smart_recommendation
from .schemas import RewardRedeem  # Đã khớp với schemas.py ở trên
from datetime import datetime

router = APIRouter()

@router.get("/dashboard/{student_id}")
async def get_parent_dashboard(student_id: int):
    """
    Lấy toàn bộ thông tin cho Dashboard Phụ huynh.[cite: 2]
    """
    db = get_db() # Lấy kết nối từ database.py
    
    # Lấy hồ sơ gamification[cite: 2]
    profile = await db.gamification_profiles.find_one({"student_id": student_id})
    
    # Lấy 5 giao dịch xu gần nhất[cite: 2]
    transactions = await db.coin_transactions.find(
        {"student_id": student_id}
    ).sort("created_at", -1).to_list(length=5)
    
    if not profile:
        raise HTTPException(status_code=404, detail="Hồ sơ học sinh chưa khởi tạo")
        
    return {
        "profile": profile,
        "recent_transactions": transactions
    }

@router.post("/trigger-recommendation/{student_id}")
async def trigger_ai_suggest(student_id: int):
    """
    Kích hoạt hệ thống gợi ý dựa trên dữ liệu TV2.[cite: 2]
    """
    db = get_db()
    result = await generate_smart_recommendation(db, student_id) # Gọi logic từ recommender.py
    return {"status": "success", "data": result}

@router.post("/earn-coins")
async def api_earn_coins(student_id: int, action: str, reference_id: int):
    """
    API dùng để tích hợp chéo với TV1 và TV2.[cite: 2]
    """
    db = get_db()
    result = await add_coins_service(db, student_id, action, reference_id) # Gọi logic từ services.py[cite: 1]
    return result