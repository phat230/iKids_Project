# Quy tắc cộng xu từ tài liệu iKids[cite: 3]
COIN_RULES = {
    "quiz_correct": 10,     # Làm bài đúng[cite: 3]
    "attendance": 5,        # Đi học đầy đủ[cite: 3]
    "streak_7_days": 20,    # Streak 7 ngày[cite: 3]
    "teacher_praise": 15    # Giáo viên khen[cite: 3]
}

def calculate_reward(action: str) -> int:
    """Trả về số xu dựa trên hành động thực tế[cite: 3]"""
    return COIN_RULES.get(action, 0)

def update_rank(lifetime_coins: int) -> str:
    """Xác định cấp độ Beginner -> Explorer -> Master[cite: 3]"""
    if lifetime_coins > 1000: return "Master"
    if lifetime_coins > 300: return "Explorer"
    return "Beginner"