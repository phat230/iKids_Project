# backend/modules/tv3_community/rule_engine.py
from datetime import datetime, timedelta

EXP_RULES = {
    "quiz_correct": 50,      # Làm bài Quiz đúng
    "attendance": 20,        # Đi học đầy đủ
    "streak_7_days": 100,    # Chuỗi 7 ngày liên tiếp
    "teacher_praise": 40,    # Lời khen từ GV
    "complete_video": 30     # Xem xong video AI
}

def calculate_exp_reward(action: str) -> int:
    """Trả về số EXP tương ứng với hành động"""
    return EXP_RULES.get(action, 0)

def update_rank(lifetime_exp: int) -> str:
    """Xác định danh hiệu dựa trên tổng EXP"""
    if lifetime_exp >= 5000: 
        return "Master"     # Bậc thầy
    if lifetime_exp >= 1500: 
        return "Explorer"   # Nhà thám hiểm
    return "Beginner"       # Người mới bắt đầu

async def check_streak_bonus(db, student_id: str):
    """
    Logic kiểm tra học 7 ngày liên tiếp.
    Nếu đủ điều kiện, cộng thêm 100 EXP streak_7_days.
    """
    # Ở đây bạn sẽ truy vấn collection 'attendance' hoặc 'activities' 
    # để đếm số ngày hoạt động liên tiếp gần nhất.
    pass