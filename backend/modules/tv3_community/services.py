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

# IMPORT THÊM HÀM THÔNG BÁO TỪ MODULE NOTIFICATION
from modules.notification.services import create_notification

# --- CẤU HÌNH LƯU TRỮ ---
UPLOAD_DIR = Path("static/avatars")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
OTP_STORE = {} 

# --- 1. QUẢN LÝ SẢN PHẨM (DATABASE THẬT) ---

async def get_store_products_service(db):
    """Lấy danh sách sản phẩm từ MongoDB thay vì list cứng"""
    cursor = db.products.find().sort("created_at", -1)
    products = []
    async for doc in cursor:
        doc["id"] = str(doc["_id"])
        del doc["_id"]
        products.append(doc)
    return products

async def purchase_product_service(db, user_id: str, product_id: str):
    """Xử lý mua sản phẩm từ Database"""
    # 1. Tìm sản phẩm trong DB
    product = await db.products.find_one({"_id": ObjectId(product_id)})
    if not product:
        return {"status": "failed", "message": "Sản phẩm không tồn tại hoặc đã ngừng bán."}
    
    # 2. Kiểm tra ví người dùng
    user = await db.users.find_one({"_id": ObjectId(user_id)})
    if not user:
        return {"status": "failed", "message": "Tài khoản không tồn tại."}

    current_balance = user.get("balance", 0)
    price = float(product.get("price", 0))
    
    if current_balance < price:
        return {"status": "failed", "message": f"Số dư không đủ để mua {product['name']}."}
    
    # 3. Thực hiện trừ tiền và lưu lịch sử mua hàng
    await db.users.update_one({"_id": ObjectId(user_id)}, {"$inc": {"balance": -price}})
    await db.purchase_history.insert_one({
        "user_id": user_id,
        "product_id": product_id,
        "product_name": product["name"],
        "price": price,
        "created_at": datetime.now()
    })
    
    # 4. Gửi thông báo cho con (nếu người mua là phụ huynh)
    child_ids = user.get("student_ids_ref", [])
    if child_ids:
        for child_id in child_ids:
            await create_notification(db, {
                "sender_id": user_id,
                "sender_role": "parent",
                "sender_name": f"Ba/Mẹ {user.get('full_name', user.get('name'))}",
                "receiver_id": str(child_id),
                "receiver_role": "student",
                "type": "finance",
                "title": "🎁 Bạn nhận được quà tặng!",
                "content": f"Ba/Mẹ vừa tặng bạn món quà: {product['name']}. Kiểm tra ngay nhé!"
            })
            
    # 5. Thông báo xác nhận cho người mua
    await create_notification(db, {
        "sender_id": "system",
        "sender_role": "system",
        "sender_name": "Cửa hàng iKids",
        "receiver_id": user_id,
        "receiver_role": user.get("role", "user"),
        "type": "finance",
        "title": "🛍️ Giao dịch thành công",
        "content": f"Bạn đã mua thành công {product['name']}. Số tiền {price:,.0f} VNĐ đã được trừ vào ví."
    })

    return {"status": "success", "message": f"Mua thành công {product['name']}!"}

# --- 2. LOGIC TÀI CHÍNH ---

async def deposit_money_service(db, user_id: str, amount: float):
    result = await db.users.update_one(
        {"_id": ObjectId(user_id)},
        {"$inc": {"balance": amount}, "$set": {"last_deposit": datetime.now()}}
    )
    
    if result.modified_count == 0:
        return {"status": "failed", "message": "Không tìm thấy tài khoản."}
    
    user = await db.users.find_one({"_id": ObjectId(user_id)})
    await create_notification(db, {
        "sender_id": "system",
        "sender_role": "system",
        "sender_name": "Hệ thống iKids",
        "receiver_id": user_id,
        "receiver_role": user.get("role"),
        "type": "finance",
        "title": "💰 Nạp tiền thành công",
        "content": f"Tài khoản đã cộng {amount:,.0f} VNĐ. Số dư: {user.get('balance', 0):,.0f} VNĐ."
    })
    
    return {"status": "success", "message": f"Đã nạp thành công {amount:,.0f} VNĐ."}

async def transfer_to_child_service(db, parent_id: str, child_id: str, amount: float):
    parent = await db.users.find_one({"_id": ObjectId(parent_id)})
    if parent.get("balance", 0) < amount:
        return {"status": "failed", "message": "Số dư ví của bạn không đủ."}
    
    await db.users.update_one({"_id": ObjectId(parent_id)}, {"$inc": {"balance": -amount}})
    await db.users.update_one({"_id": ObjectId(child_id)}, {"$inc": {"balance": amount}})
    
    await create_notification(db, {
        "sender_id": parent_id,
        "sender_role": "parent",
        "sender_name": f"Ba/Mẹ {parent.get('full_name', parent.get('name'))}",
        "receiver_id": child_id,
        "receiver_role": "student",
        "type": "finance",
        "title": "💰 Bạn vừa nhận được tiền!",
        "content": f"Ba/Mẹ đã chuyển {amount:,.0f} VNĐ vào ví của bạn."
    })
    return {"status": "success"}

async def withdraw_from_child_service(db, parent_id: str, child_id: str, amount: float):
    child = await db.users.find_one({"_id": ObjectId(child_id)})
    if child.get("balance", 0) < amount:
        return {"status": "failed", "message": "Số dư ví của bé không đủ."}
    
    await db.users.update_one({"_id": ObjectId(child_id)}, {"$inc": {"balance": -amount}})
    await db.users.update_one({"_id": ObjectId(parent_id)}, {"$inc": {"balance": amount}})
    return {"status": "success"}

# --- 3. GAMIFICATION ---

async def award_exp_service(db, student_id: str, exp_amount: int, reason: str):
    await db.users.update_one(
        {"_id": ObjectId(student_id)},
        {"$inc": {"exp": exp_amount}, "$set": {"last_active": datetime.now()}}
    )
    student = await db.users.find_one({"_id": ObjectId(student_id)})
    current_exp = student.get("exp", 0)
    
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

# --- 5. QUÊN MẬT KHẨU ---

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
    if not user: return {"status": "failed", "message": "Email này chưa được đăng ký."}
    
    otp = ''.join(random.choices(string.digits, k=6))
    OTP_STORE[email] = {"otp": otp, "expiry": datetime.now() + timedelta(minutes=5)}
    
    message = MessageSchema(
        subject="iKids Portal - Mã OTP đặt lại mật khẩu",
        recipients=[email],
        body=f"Mã OTP của bạn là: {otp}. Hiệu lực trong 5 phút.",
        subtype=MessageType.plain
    )
    fm = FastMail(conf)
    await fm.send_message(message)
    return {"status": "success", "message": "Mã OTP đã được gửi."}

async def verify_otp_and_reset_password_service(db, email, otp, new_password):
    if email not in OTP_STORE: return {"status": "failed", "message": "Yêu cầu không tồn tại."}
    stored_data = OTP_STORE[email]
    if datetime.now() > stored_data["expiry"] or stored_data["otp"] != otp:
        return {"status": "failed", "message": "Mã OTP không chính xác hoặc hết hạn."}
    
    hashed_password = get_password_hash(new_password)
    await db.users.update_one({"email": email}, {"$set": {"password": hashed_password}})
    del OTP_STORE[email]
    return {"status": "success", "message": "Đổi mật khẩu thành công!"}

# --- 6. KỶ NIỆM & LIÊN HỆ & LỊCH SỬ ---

async def get_class_memories(db):
    memories = await db.memories.find().sort("created_at", -1).to_list(length=20)
    for m in memories: m["_id"] = str(m["_id"])
    return memories

async def like_memory_service(db, memory_id: str):
    await db.memories.update_one({"_id": ObjectId(memory_id)}, {"$inc": {"likes": 1}})
    return {"status": "success"}

async def submit_contact_request(db, message_data):
    # Phân loại và lưu tin nhắn
    msg_id = await db.contact_messages.insert_one({
        "sender_id": message_data.sender_id,
        "receiver_id": message_data.receiver_id,
        "subject": message_data.subject,
        "content": message_data.content,
        "created_at": datetime.now()
    })
    return {"status": "success", "id": str(msg_id.inserted_id)}

async def get_contact_history(db, user_id: str):
    """Lấy lịch sử liên hệ (Hàm fix lỗi ImportError)"""
    messages = await db.contact_messages.find({
        "$or": [{"sender_id": user_id}, {"receiver_id": user_id}]
    }).sort("created_at", -1).to_list(length=50)
    for m in messages: m["_id"] = str(m["_id"])
    return messages

async def generate_vietqr_link(amount: int, user_id: str):
    BANK_ID, ACCOUNT_NO, TEMPLATE = "BIDV", "64110001073247", "compact"
    description = f"IKIDS NAP {user_id[-6:]}".upper() 
    qr_url = f"https://img.vietqr.io/image/{BANK_ID}-{ACCOUNT_NO}-{TEMPLATE}.png?amount={amount}&addInfo={description}"
    return qr_url, description
async def transfer_to_child_service(db, parent_id: str, child_id: str, amount: float):
    """Phụ huynh gửi tiền cho con"""
    parent = await db.users.find_one({"_id": ObjectId(parent_id)})
    if parent.get("balance", 0) < amount:
        return {"status": "failed", "message": "Số dư ví của bạn không đủ."}
    
    # 1. Trừ tiền phụ huynh, cộng tiền cho con
    await db.users.update_one({"_id": ObjectId(parent_id)}, {"$inc": {"balance": -amount}})
    await db.users.update_one({"_id": ObjectId(child_id)}, {"$inc": {"balance": amount}})
    
    # 2. Gửi thông báo cho CON
    await create_notification(db, {
        "sender_id": parent_id,
        "sender_role": "parent",
        "sender_name": f"Ba/Mẹ {parent.get('name')}",
        "receiver_id": child_id,
        "receiver_role": "student",
        "type": "finance",
        "title": "💰 Bạn vừa nhận được tiền!",
        "content": f"Ba/Mẹ đã chuyển {amount:,.0f} VNĐ vào ví của bạn. Chăm chỉ học tập nhé!"
    })
    return {"status": "success"}

async def withdraw_from_child_service(db, parent_id: str, child_id: str, amount: float):
    """Phụ huynh rút tiền từ ví của con về ví mình"""
    child = await db.users.find_one({"_id": ObjectId(child_id)})
    if child.get("balance", 0) < amount:
        return {"status": "failed", "message": "Số dư ví của bé không đủ để rút."}
    
    # 1. Trừ tiền con, cộng tiền cho phụ huynh
    await db.users.update_one({"_id": ObjectId(child_id)}, {"$inc": {"balance": -amount}})
    await db.users.update_one({"_id": ObjectId(parent_id)}, {"$inc": {"balance": amount}})
    
    # 2. Gửi thông báo cho CON
    await create_notification(db, {
        "sender_id": parent_id,
        "sender_role": "parent",
        "sender_name": "Hệ thống iKids",
        "receiver_id": child_id,
        "receiver_role": "student",
        "type": "finance",
        "title": "💸 Thông báo biến động số dư",
        "content": f"Ba/Mẹ đã rút {amount:,.0f} VNĐ từ ví của bạn."
    })
    return {"status": "success"}