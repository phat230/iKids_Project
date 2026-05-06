# Các quy tắc cộng xu cố định của hệ thống iKids
COIN_RULES = {
    "quiz_correct": 10,     # Làm bài Quiz đúng
    "attendance": 5,        # Đi học đầy đủ đúng giờ
    "streak_7_days": 20,    # Chuỗi học tập 7 ngày liên tiếp
    "teacher_praise": 15,   # Giáo viên gửi lời khen
    "complete_video": 5     # Xem xong 1 video bài giảng AI
}

def calculate_reward(action: str) -> int:
    """Hàm trả về số xu tương ứng với hành động thực tế"""
    return COIN_RULES.get(action, 0)

def update_rank(lifetime_coins: int) -> str:
    """Hàm xác định cấp độ của học viên dựa trên tổng xu đã tích lũy từ trước đến nay"""
    if lifetime_coins >= 1000: 
        return "Master"    # Bậc thầy
    if lifetime_coins >= 300: 
        return "Explorer"  # Nhà thám hiểm
    return "Beginner"      # Người mới bắt đầu