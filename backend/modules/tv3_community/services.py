from datetime import datetime, timedelta
from bson import ObjectId
from fastapi import HTTPException
import os
import shutil
from pathlib import Path
import random
import string
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig, MessageType
from core.security import get_password_hash

# --- CẤU HÌNH LƯU TRỮ VÀ BỘ NHỚ TẠM ---
UPLOAD_DIR = Path("static/avatars")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

# Lưu tạm mã OTP trong bộ nhớ (Hết hạn sau 5 phút)
OTP_STORE = {} 

# --- 1. DANH SÁCH SẢN PHẨM HỌC LIỆU ---
PRODUCTS_DB = [
    {"id": 1, "name": "Sách Toán Tư Duy Tập 1", "price": 85000, "type": "book", "icon": "📚"},
    {"id": 2, "name": "Bộ Thí Nghiệm Hóa Học Nhí", "price": 250000, "type": "kit", "icon": "🧪"},
    {"id": 3, "name": "Balo iKids Siêu Cấp", "price": 180000, "type": "accessory", "icon": "🎒"},
    {"id": 4, "name": "Sổ Tay Ghi Chép iKids", "price": 45000, "type": "accessory", "icon": "📒"},
]

# --- 2. LOGIC TÀI CHÍNH & MUA SẮM (DÙNG VNĐ) ---

async def get_store_products_service():
    """Lấy danh sách sản phẩm hiện có trong cửa hàng"""
    return PRODUCTS_DB

async def deposit_money_service(db, user_id: str, amount: float):
    """Xử lý nạp tiền vào tài khoản cho Phụ huynh"""
    await db.gamification_profiles.update_one(
        {"student_id": user_id},
        {"$inc": {"balance": amount}},
        upsert=True
    )
    return {"status": "success", "message": f"Đã nạp thành công {amount:,.0f} VNĐ."}

async def purchase_product_service(db, user_id: str, product_id: int):
    """Xử lý mua hàng bằng số dư VNĐ"""
    product = next((p for p in PRODUCTS_DB if p["id"] == product_id), None)
    if not product:
        return {"status": "failed", "message": "Sản phẩm không tồn tại."}
    
    profile = await db.gamification_profiles.find_one({"student_id": user_id})
    current_balance = profile.get("balance", 0) if profile else 0
    
    if current_balance < product["price"]:
        return {"status": "failed", "message": f"Số dư không đủ. Cần nạp thêm {product['price'] - current_balance:,.0f} VNĐ."}
    
    await db.gamification_profiles.update_one(
        {"student_id": user_id},
        {"$inc": {"balance": -product["price"]}}
    )
    
    await db.purchase_history.insert_one({
        "user_id": user_id,
        "product_name": product["name"],
        "amount": product["price"],
        "created_at": datetime.now()
    })
    
    return {"status": "success", "message": f"Thanh toán thành công {product['name']}!"}

# --- 3. GAMIFICATION: HỆ THỐNG EXP & RANK (THAY THẾ COINS) ---

async def award_exp_service(db, student_id: str, exp_amount: int, reason: str):
    """Tặng EXP cho học sinh và tự động tính toán thăng hạng"""
    # 1. Cập nhật EXP
    await db.gamification_profiles.update_one(
        {"student_id": student_id},
        {
            "$inc": {"exp": exp_amount},
            "$set": {"last_updated": datetime.now()}
        },
        upsert=True
    )
    
    # 2. Lấy profile mới nhất để tính Level/Rank
    profile = await db.gamification_profiles.find_one({"student_id": student_id})
    current_exp = profile.get("exp", 0)
    
    # Logic thăng cấp: Cứ 1000 EXP lên 1 level
    new_level = (current_exp // 1000) + 1
    
    # Xác định Rank dựa trên Level
    new_rank = "Beginner"
    if new_level >= 10: new_rank = "Master"
    elif new_level >= 5: new_rank = "Explorer"
    
    await db.gamification_profiles.update_one(
        {"student_id": student_id},
        {"$set": {"level": new_level, "rank_level": new_rank}}
    )
    
    return {"status": "success", "message": f"Đã tặng {exp_amount} EXP vì: {reason}"}

# --- 4. QUẢN LÝ TÀI KHOẢN (AVATAR THẬT, ĐỔI MẬT KHẨU) ---

async def update_account_profile_service(db, user_id: str, full_name: str = None, avatar_file = None):
    update_data = {}
    if full_name:
        update_data["name"] = full_name
    
    if avatar_file:
        extension = avatar_file.filename.split(".")[-1]
        file_name = f"{user_id}.{extension}"
        file_path = UPLOAD_DIR / file_name
        
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(avatar_file.file, buffer)
        
        update_data["avatar_url"] = f"static/avatars/{file_name}"
        
    if update_data:
        await db.users.update_one({"_id": ObjectId(user_id)}, {"$set": update_data})
        return {
            "status": "success", 
            "message": "Cập nhật thành công.",
            "avatar_url": update_data.get("avatar_url")
        }
    return {"status": "failed", "message": "Không có thay đổi."}

async def change_password_service(db, user_id: str, new_password: str):
    """Đổi mật khẩu trực tiếp (Mã hóa trước khi lưu)"""
    hashed_password = get_password_hash(new_password)
    await db.users.update_one(
        {"_id": ObjectId(user_id)}, 
        {"$set": {"password": hashed_password}} 
    )
    return {"status": "success", "message": "Đổi mật khẩu thành công!"}

# --- 5. KHÔI PHỤC MẬT KHẨU QUA SMTP GMAIL (DUY NHẤT) ---

conf = ConnectionConfig(
    MAIL_USERNAME = "phay123321@gmail.com",
    MAIL_PASSWORD = "zuzb mhcn fzui fldc",
    MAIL_FROM = "phay123321@gmail.com",
    MAIL_PORT = 587,
    MAIL_SERVER = "smtp.gmail.com",
    MAIL_STARTTLS = True,
    MAIL_SSL_TLS = False,
    USE_CREDENTIALS = True,
    VALIDATE_CERTS = True
)

async def send_forgot_password_email_service(db, email: str):
    """Gửi mã OTP THẬT qua Email"""
    user = await db.users.find_one({"email": email})
    if not user:
        return {"status": "failed", "message": "Email không tồn tại."}

    otp = ''.join(random.choices(string.digits, k=6))
    OTP_STORE[email] = {
        "otp": otp,
        "expiry": datetime.now() + timedelta(minutes=5)
    }

    html = f"""
    <div style="font-family: Arial, sans-serif; border: 1px solid #ddd; padding: 20px;">
        <h2 style="color: #1E3A8A;">iKids Portal - Xác nhận đổi mật khẩu</h2>
        <p>Chào bạn,</p>
        <p>Bạn đã yêu cầu khôi phục mật khẩu. Mã xác nhận (OTP) của bạn là:</p>
        <h1 style="color: #00adef; text-align: center; letter-spacing: 5px;">{otp}</h1>
        <p>Mã này có hiệu lực trong <b>5 phút</b>. Nếu bạn không thực hiện yêu cầu này, vui lòng bỏ qua email.</p>
        <hr>
        <p style="font-size: 12px; color: #888;">Đây là email tự động từ hệ thống iKids Portal.</p>
    </div>
    """

    message = MessageSchema(
        subject="iKids Portal - Mã xác nhận OTP",
        recipients=[email],
        body=html,
        subtype=MessageType.html
    )

    fm = FastMail(conf)
    try:
        await fm.send_message(message)
        return {"status": "success", "message": "Mã OTP đã được gửi vào Email của bạn."}
    except Exception as e:
        return {"status": "failed", "message": "Không thể gửi email lúc này."}

async def verify_otp_and_reset_password_service(db, email, otp, new_password):
    if email not in OTP_STORE:
        return {"status": "failed", "message": "Yêu cầu không hợp lệ hoặc đã hết hạn."}

    stored_data = OTP_STORE[email]
    if datetime.now() > stored_data["expiry"]:
        del OTP_STORE[email]
        return {"status": "failed", "message": "Mã OTP đã hết hạn."}

    if stored_data["otp"] != otp:
        return {"status": "failed", "message": "Mã OTP không chính xác."}

    hashed_password = get_password_hash(new_password)
    await db.users.update_one(
        {"email": email}, 
        {"$set": {"password": hashed_password}} 
    )
    
    del OTP_STORE[email]
    return {"status": "success", "message": "Đã thiết lập mật khẩu mới thành công!"}

# --- 6. GÓC KỶ NIỆM & LIÊN HỆ ---

async def get_class_memories(db):
    memories = await db.memories.find().sort("created_at", -1).to_list(length=20)
    for m in memories: m["_id"] = str(m["_id"])
    return memories

async def like_memory_service(db, memory_id: str):
    await db.memories.update_one({"_id": ObjectId(memory_id)}, {"$inc": {"likes": 1}})
    return {"status": "success"}

async def submit_contact_request(db, message_data):
    new_message = {
        "sender_id": message_data.sender_id,
        "receiver_id": message_data.receiver_id,
        "subject": message_data.subject,
        "content": message_data.content,
        "created_at": datetime.now()
    }
    await db.contact_messages.insert_one(new_message)
    
    if "nghỉ học" in message_data.subject.lower():
        await db.operator_requests.insert_one({
            "type": "leave_request",
            "parent_id": message_data.sender_id,
            "status": "pending",
            "created_at": datetime.now()
        })
    return {"status": "success"}

async def get_contact_history(db, parent_id: str):
    messages = await db.contact_messages.find({"sender_id": parent_id}).sort("created_at", -1).to_list(length=20)
    for msg in messages: msg["_id"] = str(msg["_id"]) 
    return messages