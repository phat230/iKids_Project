from datetime import datetime
from .rule_engine import calculate_reward, update_rank
from bson import ObjectId

async def add_coins_service(db, student_id: int, action: str, ref_id: int = None):
    """Xử lý cộng xu, ghi lịch sử giao dịch và tự động thăng cấp cho học sinh"""
    
    # 1. Tính toán số xu nhận được
    coins = calculate_reward(action)
    if coins == 0:
        return {"status": "failed", "message": "Hành động không hợp lệ hoặc không có thưởng."}
    
    # 2. Lưu giao dịch vào lịch sử để Phụ huynh/Học sinh có thể xem lại
    transaction = {
        "student_id": student_id,
        "amount": coins,
        "transaction_type": "earn",
        "source_action": action,
        "reference_id": ref_id,
        "created_at": datetime.now()
    }
    await db.coin_transactions.insert_one(transaction)
    
    # 3. Lấy hồ sơ hiện tại của học sinh
    profile = await db.gamification_profiles.find_one({"student_id": student_id})
    
    # 4. Tính toán số dư mới và xét duyệt thăng hạng
    current_lifetime = profile.get('lifetime_coins', 0) if profile else 0
    new_lifetime = current_lifetime + coins
    new_rank = update_rank(new_lifetime)
    
    # 5. Cập nhật lại vào Database
    await db.gamification_profiles.update_one(
        {"student_id": student_id},
        {
            "$inc": {"total_coins": coins, "lifetime_coins": coins},
            "$set": {"rank_level": new_rank, "last_active_date": datetime.now()}
        },
        upsert=True
    )
    
    return {
        "status": "success", 
        "earned": coins, 
        "new_total": (profile.get('total_coins', 0) if profile else 0) + coins,
        "current_rank": new_rank
    }

async def submit_contact_request(db, message_data):
    """Xử lý lưu tin nhắn từ Phụ huynh và tự động phân luồng yêu cầu"""
    new_message = {
        "sender_id": message_data.sender_id,
        "receiver_id": message_data.receiver_id,
        "subject": message_data.subject,
        "content": message_data.content,
        "is_read": False,
        "created_at": datetime.now()
    }
    
    # Lưu vào database
    result = await db.contact_messages.insert_one(new_message)
    
    # Nếu tiêu đề có chứa từ khóa "nghỉ học", tự động convert thành Request cho TV1
    if "nghỉ học" in message_data.subject.lower():
        system_alert = {
            "type": "leave_request",
            "parent_id": message_data.sender_id,
            "message_ref": str(result.inserted_id),
            "status": "pending",
            "created_at": datetime.now()
        }
        await db.operator_requests.insert_one(system_alert)
        
    return {
        "status": "success", 
        "message_id": str(result.inserted_id), 
        "message": "Yêu cầu của bạn đã được gửi và đang chờ xử lý!"
    }

async def get_contact_history(db, parent_id: int):
    """Lấy lịch sử các tin nhắn/yêu cầu mà phụ huynh đã gửi"""
    messages = await db.contact_messages.find({"sender_id": parent_id}).sort("created_at", -1).to_list(length=20)
    for msg in messages:
        msg["_id"] = str(msg["_id"]) 
    return messages