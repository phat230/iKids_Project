from fastapi import HTTPException
from core.security import get_password_hash, verify_password, create_access_token
from .schemas import UserCreate, UserLogin, OTPVerifyRequest
from .models import UserDBModel
from bson import ObjectId
import random
import httpx
import os
from datetime import datetime, timedelta

async def send_sms_otp(db, phone_number: str, otp_code: str, parent_id: str = None):
    """
    Hàm gửi tin nhắn SMS OTP thực tế.
    Chi phí tin nhắn sẽ được khấu trừ từ ví của người dùng/phụ huynh.
    """
    # 1. Kiểm tra số dư ví trước khi gửi (Ví dụ trừ 500đ phí SMS)
    if parent_id:
        fee = 500
        # Kiểm tra và trừ tiền trong collection gamification_profiles
        result = await db.gamification_profiles.update_one(
            {"parent_id": ObjectId(parent_id), "balance": {"$gte": fee}},
            {"$inc": {"balance": -fee}}
        )
        if result.modified_count == 0:
            raise HTTPException(status_code=402, detail="Số dư ví không đủ để thanh toán phí gửi SMS.")

    # 2. Gọi API nhà mạng thực tế (Ví dụ SpeedSMS)
    api_key = os.getenv("SMS_API_KEY", "your_key")
    url = "https://api.speedsms.vn/index.php/sms/send"
    params = {"access-token": api_key, "to": phone_number, "content": f"iKids Portal: Ma OTP cua ban la {otp_code}.", "type": "2"}
    
    async with httpx.AsyncClient() as client:
        try:
            res = await client.post(url, json=params)
            if res.status_code == 200:
                print(f"[SMS GATEWAY] Gửi thành công tới {phone_number}. Phí đã trừ vào ví.")
                return True
        except:
            pass
            
    raise HTTPException(status_code=500, detail="Lỗi kết nối nhà mạng SMS.")

# ==============================================================================
# CÁC HÀM BÊN DƯỚI ĐƯỢC GIỮ NGUYÊN THEO YÊU CẦU CỦA BẠN
# ==============================================================================

async def register_user(db, user_data: UserCreate):
    # Chuẩn hóa email
    clean_email = user_data.email.strip().lower()

    # 1. Kiểm tra trùng lặp Email
    existing_email = await db.users.find_one({"email": clean_email})
    if existing_email:
        raise HTTPException(status_code=400, detail="Email này đã được đăng ký.")

    # 2. Kiểm tra trùng lặp Số điện thoại (Nếu có điền số điện thoại)
    if user_data.phone_number:
        existing_phone = await db.users.find_one({"phone_number": user_data.phone_number})
        if existing_phone:
            raise HTTPException(status_code=400, detail="Số điện thoại này đã được đăng ký sử dụng.")

    valid_roles = ["student", "teacher", "admin", "operator", "parent"]
    if user_data.role not in valid_roles:
        raise HTTPException(status_code=400, detail="Role không hợp lệ.")

    user_dict = user_data.dict()
    user_dict["email"] = clean_email
    user_dict["password"] = get_password_hash(user_dict["password"])

    # 3. Tạo mã OTP ngẫu nhiên 6 số và thời gian hết hạn (5 phút)
    otp_code = f"{random.randint(100000, 999999)}"
    otp_expires_at = datetime.now() + timedelta(minutes=5)
    
    user_dict["otp_code"] = otp_code
    user_dict["otp_expires_at"] = otp_expires_at
    
    # Tài khoản thông thường tự đăng ký mặc định sẽ chưa được kích hoạt
    user_dict["is_active"] = False

    db_user = UserDBModel(**user_dict)
    result = await db.users.insert_one(db_user.dict())

    # 4. Kích hoạt gửi SMS
    if user_data.phone_number:
        await send_sms_otp(db, user_data.phone_number, otp_code)

    return {
        "message": "Đăng ký thành công bước đầu! Vui lòng nhập mã OTP gửi tới điện thoại của bạn để kích hoạt tài khoản.",
        "user_id": str(result.inserted_id),
        "email": clean_email
    }

async def verify_registration_otp(db, verify_data: OTPVerifyRequest):
    """Hàm xử lý kiểm tra mã OTP kích hoạt tài khoản"""
    clean_email = verify_data.email.strip().lower()
    
    user = await db.users.find_one({"email": clean_email})
    if not user:
        raise HTTPException(status_code=404, detail="Không tìm thấy thông tin tài khoản.")
        
    if user.get("is_active") == True:
        return {"message": "Tài khoản này đã được kích hoạt từ trước."}
        
    # Kiểm tra mã OTP
    saved_otp = user.get("otp_code")
    expiry = user.get("otp_expires_at")
    
    if not saved_otp or saved_otp != verify_data.otp_code:
        raise HTTPException(status_code=400, detail="Mã xác thực OTP không chính xác.")
        
    if expiry and datetime.now() > expiry:
        raise HTTPException(status_code=400, detail="Mã OTP đã hết hạn. Vui lòng thực hiện đăng ký lại.")
        
    # Kích hoạt tài khoản chính thức và xóa mã OTP cũ trong DB
    await db.users.update_one(
        {"_id": user["_id"]},
        {
            "$set": {"is_active": True},
            "$unset": {"otp_code": "", "otp_expires_at": ""}
        }
    )
    
    return {"status": "success", "message": "Xác thực kích hoạt tài khoản thành công! Bây giờ bạn đã có thể đăng nhập."}

async def login_user(db, login_data: UserLogin):
    clean_email = login_data.email.strip().lower()
    user = await db.users.find_one({"email": clean_email})

    if not user:
        raise HTTPException(
            status_code=404,
            detail="Email không tồn tại. Vui lòng kiểm tra lại."
        )

    # Chặn đăng nhập nếu tài khoản chưa được kích hoạt kích hoạt qua OTP hoặc bị khóa
    if user.get("is_active") == False:
        raise HTTPException(
            status_code=403,
            detail="Tài khoản chưa được kích hoạt OTP hoặc đã bị vô hiệu hóa. Vui lòng xác thực trước."
        )

    if not verify_password(login_data.password, user["password"]):
        raise HTTPException(
            status_code=401,
            detail="Sai mật khẩu."
        )

    token_data = {
        "sub": str(user["_id"]),
        "role": user["role"]
    }

    access_token = create_access_token(token_data)

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user_info": {
            "id": str(user["_id"]),
            "name": user["name"],
            "email": user["email"],
            "role": user["role"]
        }
    }

async def create_student_by_parent(db, parent_id: str, student_data: UserCreate):
    """Phụ huynh tạo tài khoản cho con (Student) và tự động liên kết"""
    clean_email = student_data.email.strip().lower()

    existing_user = await db.users.find_one({"email": clean_email})
    if existing_user:
        raise HTTPException(
            status_code=400,
            detail="Email này đã được sử dụng."
        )

    # Ép buộc quyền tài khoản con tạo ra phải luôn luôn là student
    student_dict = student_data.dict()
    student_dict["email"] = clean_email
    student_dict["password"] = get_password_hash(student_dict["password"])
    student_dict["role"] = "student"
    
    # Tài khoản con do chính phụ huynh chủ động tạo nên kích hoạt luôn (is_active = True)
    student_dict["is_active"] = True 

    db_student = UserDBModel(**student_dict)
    result = await db.users.insert_one(db_student.dict())
    new_student_id = str(result.inserted_id)

    # Liên kết ID học sinh vào mảng quản lý của Phụ huynh
    await db.users.update_one(
        {"_id": ObjectId(parent_id)},
        {"$push": {"student_ids_ref": new_student_id}} 
    )

    await db.gamification_profiles.insert_one({
        "student_id": int(new_student_id) if new_student_id.isdigit() else new_student_id,
        "total_coins": 0,
        "lifetime_coins": 0,
        "rank_level": "Beginner",
        "current_streak": 0
    })

    return {
        "status": "success",
        "message": "Tạo tài khoản cho con và liên kết thành công!",
        "student_id": new_student_id
    }