# backend/modules/tv3_community/services.py
from datetime import datetime, timedelta
from bson import ObjectId
from fastapi import HTTPException
import shutil
import random
import string
from pathlib import Path
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig, MessageType
from core.security import get_password_hash

# --- CẤU HÌNH LƯU TRỮ ---
UPLOAD_DIR = Path("static/avatars")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
OTP_STORE = {} 

# --- 1. SẢN PHẨM ---
PRODUCTS_DB = [
    {"id": 1, "name": "Sách Toán Tư Duy Tập 1", "price": 85000, "type": "book", "icon": "📚"},
    {"id": 2, "name": "Bộ Thí Nghiệm Hóa Học Nhí", "price": 250000, "type": "kit", "icon": "🧪"},
    {"id": 3, "name": "Balo iKids Siêu Cấp", "price": 180000, "type": "accessory", "icon": "🎒"},
    {"id": 4, "name": "Sổ Tay Ghi Chép iKids", "price": 45000, "type": "accessory", "icon": "📒"},
]

# --- 2. LOGIC TÀI CHÍNH ---
async def get_store_products_service():
    return PRODUCTS_DB

async def deposit_money_service(db, user_id: str, amount: float):
    # Cập nhật số dư và lưu vết nạp tiền cuối cùng
    result = await db.users.update_one(
        {"_id": ObjectId(user_id)},
        {"$inc": {"balance": amount}, "$set": {"last_deposit": datetime.now()}}
    )
    if result.modified_count == 0:
        return {"status": "failed", "message": "Không tìm thấy tài khoản."}
    return {"status": "success", "message": f"Đã nạp thành công {amount:,.0f} VNĐ."}

async def purchase_product_service(db, user_id: str, product_id: int):
    product = next((p for p in PRODUCTS_DB if p["id"] == product_id), None)
    if not product:
        return {"status": "failed", "message": "Sản phẩm không tồn tại."}
    
    user = await db.users.find_one({"_id": ObjectId(user_id)})
    current_balance = user.get("balance", 0)
    
    if current_balance < product["price"]:
        return {"status": "failed", "message": f"Số dư không đủ để mua {product['name']}."}
    
    # Thực hiện trừ tiền và lưu lịch sử mua hàng
    await db.users.update_one({"_id": ObjectId(user_id)}, {"$inc": {"balance": -product["price"]}})
    await db.purchase_history.insert_one({
        "user_id": user_id,
        "product_name": product["name"],
        "price": product["price"],
        "created_at": datetime.now()
    })
    return {"status": "success", "message": f"Mua thành công {product['name']}!"}

# --- 3. GAMIFICATION ---
async def award_exp_service(db, student_id: str, exp_amount: int, reason: str):
    await db.users.update_one(
        {"_id": ObjectId(student_id)},
        {"$inc": {"exp": exp_amount}, "$set": {"last_active": datetime.now()}}
    )
    student = await db.users.find_one({"_id": ObjectId(student_id)})
    current_exp = student.get("exp", 0)
    
    # Logic xếp hạng (Rank)
    if current_exp >= 5000: new_rank = "Master"
    elif current_exp >= 1500: new_rank = "Explorer"
    else: new_rank = "Beginner"
        
    await db.users.update_one({"_id": ObjectId(student_id)}, {"$set": {"rank": new_rank}})
    return {"status": "success", "exp_total": current_exp, "rank": new_rank}

# --- 4. TÀI KHOẢN & BẢO MẬT ---
async def update_account_profile_service(db, user_id: str, full_name: str = None, avatar_file = None):
    update_data = {}
    if full_name: update_data["full_name"] = full_name
    if avatar_file:
        file_extension = Path(avatar_file.filename).suffix
        file_name = f"avatar_{user_id}{file_extension}"
        file_path = UPLOAD_DIR / file_name
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(avatar_file.file, buffer)
        update_data["avatar_url"] = f"/static/avatars/{file_name}"
        
    if update_data:
        await db.users.update_one({"_id": ObjectId(user_id)}, {"$set": update_data})
        return {"status": "success", "data": update_data}
    return {"status": "no_change"}

# --- 5. QUÊN MẬT KHẨU (Email OTP) ---
conf = ConnectionConfig(
    MAIL_USERNAME="phay123321@gmail.com",
    MAIL_PASSWORD="zuzb mhcn fzui fldc",
    MAIL_FROM="phay123321@gmail.com",
    MAIL_PORT=587,
    MAIL_SERVER="smtp.gmail.com",
    MAIL_STARTTLS=True,
    MAIL_SSL_TLS=False,
    USE_CREDENTIALS=True
)

async def send_forgot_password_email_service(db, email: str):
    user = await db.users.find_one({"email": email})
    if not user: return {"status": "failed", "message": "Email này chưa được đăng ký trong hệ thống."}
    
    otp = ''.join(random.choices(string.digits, k=6))
    OTP_STORE[email] = {"otp": otp, "expiry": datetime.now() + timedelta(minutes=5)}
    
    message = MessageSchema(
        subject="iKids Learning - Mã xác thực đặt lại mật khẩu",
        recipients=[email],
        body=f"Mã OTP của bạn là: {otp}. Mã có hiệu lực trong 5 phút. Vui lòng không chia sẻ mã này.",
        subtype=MessageType.plain
    )
    fm = FastMail(conf)
    await fm.send_message(message)
    return {"status": "success", "message": "Mã OTP đã được gửi về email của bạn."}

async def verify_otp_and_reset_password_service(db, email, otp, new_password):
    if email not in OTP_STORE: return {"status": "failed", "message": "Không tìm thấy yêu cầu đặt lại mật khẩu."}
    stored_data = OTP_STORE[email]
    
    if datetime.now() > stored_data["expiry"]:
        del OTP_STORE[email]
        return {"status": "failed", "message": "Mã OTP đã hết hạn hiệu lực."}
    
    if stored_data["otp"] != otp: return {"status": "failed", "message": "Mã OTP không chính xác."}
    
    hashed_password = get_password_hash(new_password)
    await db.users.update_one({"email": email}, {"$set": {"password": hashed_password}})
    del OTP_STORE[email]
    return {"status": "success", "message": "Đã đặt lại mật khẩu mới thành công!"}

# --- 6. KỶ NIỆM & LIÊN HỆ (Tối ưu 4.2) ---
async def get_class_memories(db):
    memories = await db.memories.find().sort("created_at", -1).to_list(length=20)
    for m in memories: m["_id"] = str(m["_id"])
    return memories

async def like_memory_service(db, memory_id: str):
    await db.memories.update_one({"_id": ObjectId(memory_id)}, {"$inc": {"likes": 1}})
    return {"status": "success"}

async def submit_contact_request(db, message_data):
    # Lưu vào hội thoại chung
    msg_id = await db.contact_messages.insert_one({
        "sender_id": message_data.sender_id,
        "receiver_id": message_data.receiver_id,
        "subject": message_data.subject,
        "content": message_data.content,
        "created_at": datetime.now()
    })
    
    # 4.2: TỰ ĐỘNG CHUYỂN ĐỔI YÊU CẦU CHO OPERATOR (TV1)
    # Kiểm tra từ khóa "nghỉ" trong cả tiêu đề và nội dung
    keywords = ["nghỉ học", "xin nghỉ", "off", "vắng mặt"]
    full_text = f"{message_data.subject} {message_data.content}".lower()
    
    if any(k in full_text for k in keywords):
        await db.operator_requests.insert_one({
            "type": "leave_request",
            "priority": "high",
            "source_msg_id": str(msg_id.inserted_id),
            "parent_id": message_data.sender_id,
            "details": f"Nội dung: {message_data.content}",
            "status": "pending",
            "is_processed": False,
            "created_at": datetime.now()
        })
    return {"status": "success", "message": "Đã gửi liên hệ thành công."}

async def get_contact_history(db, user_id: str):
    messages = await db.contact_messages.find({
        "$or": [{"sender_id": user_id}, {"receiver_id": user_id}]
    }).sort("created_at", -1).to_list(length=50)
    for m in messages: m["_id"] = str(m["_id"])
    return messages

async def generate_vietqr_link(amount: int, user_id: str):
    """
    Tạo link mã QR ngân hàng BIDV cho TV3
    Cập nhật theo yêu cầu chuyển từ VCB sang BIDV
    """
    BANK_ID = "BIDV" 
    ACCOUNT_NO = "64110001073247"
    TEMPLATE = "compact"
    description = f"IKIDS NAP {user_id[-6:]}".upper() 
    
    qr_url = f"https://img.vietqr.io/image/{BANK_ID}-{ACCOUNT_NO}-{TEMPLATE}.png?amount={amount}&addInfo={description}&accountName=TRAN%20PHAM%20THANH%20MINH"
    return qr_url, description