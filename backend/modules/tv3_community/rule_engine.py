
EXP_RULES = {
    "quiz_correct": 50,      # Làm bài Quiz đúng
    "attendance": 20,        # Đi học đầy đủ đúng giờ
    "streak_7_days": 100,    # Chuỗi học tập 7 ngày liên tiếp
    "teacher_praise": 40,    # Giáo viên gửi lời khen
    "complete_video": 30     # Xem xong 1 video bài giảng AI
}

def calculate_exp_reward(action: str) -> int:
    """Hàm trả về số điểm kinh nghiệm tương ứng với hành động"""
    return EXP_RULES.get(action, 0)

def update_rank(lifetime_exp: int) -> str:
    """
    Xác định cấp độ của học viên dựa trên tổng EXP tích lũy.
    Giúp học sinh có động lực học tập để 'Khoe' Rank trên Trang cá nhân.
    """
    if lifetime_exp >= 5000: 
        return "Master"     # Bậc thầy
    if lifetime_exp >= 1500: 
        return "Explorer"   # Nhà thám hiểm
    return "Beginner"       # Người mới bắt đầu