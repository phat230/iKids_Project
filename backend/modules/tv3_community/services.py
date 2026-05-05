from .rule_engine import calculate_reward, update_rank
from datetime import datetime

async def add_coins_service(db, student_id: int, action: str, ref_id: int):
    """Xử lý cộng xu và cập nhật Rank cho học sinh"""
    coins = calculate_reward(action)
    
    # 1. Lưu giao dịch vào lịch sử
    transaction = {
        "student_id": student_id,
        "amount": coins,
        "transaction_type": "earn",
        "source_action": action,
        "reference_id": ref_id,
        "created_at": datetime.now()
    }
    await db.coin_transactions.insert_one(transaction)

    # 2. Cập nhật hồ sơ (Cộng xu và kiểm tra thăng cấp)
    profile = await db.gamification_profiles.find_one({"student_id": student_id})
    new_lifetime = (profile.get('lifetime_coins', 0) if profile else 0) + coins
    new_rank = update_rank(new_lifetime)

    await db.gamification_profiles.update_one(
        {"student_id": student_id},
        {
            "$inc": {"total_coins": coins, "lifetime_coins": coins},
            "$set": {"rank_level": new_rank, "last_active_date": datetime.now()}
        },
        upsert=True
    )
    return {"earned": coins, "current_rank": new_rank}