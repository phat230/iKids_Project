from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

# Schema cho Hồ sơ Gamification
class GamificationProfileBase(BaseModel):
    student_id: int
    total_coins: int = 0
    rank_level: str = "Beginner"
    current_streak: int = 0

# Đổi tên từ RewardRedeemRequest thành RewardRedeem để khớp với router[cite: 1, 2]
class RewardRedeem(BaseModel):
    student_id: int
    reward_id: int

# Schema cho Góc kỷ niệm (Memories)[cite: 2]
class MemoryCreate(BaseModel):
    class_id: int
    teacher_id: int
    media_url: str
    media_type: str  # 'image' hoặc 'video'[cite: 2]
    description: str