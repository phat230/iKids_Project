import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from fastapi import APIRouter, Depends, HTTPException, Header
from core.database import get_db
from core.security import get_current_user, verify_password, get_password_hash 
from .schemas import UserCreate, UserLogin, TokenResponse, OTPVerifyRequest
from .services import register_user, login_user, create_student_by_parent, verify_registration_otp
from bson import ObjectId
import random
from datetime import datetime, timedelta

# Hàm gửi Email thực tế đọc từ cấu hình .env
def send_email_otp(target_email: str, otp_code: str) -> bool:
    """Hàm gửi mã OTP qua Gmail SMTP sử dụng cấu hình từ .env"""
    smtp_server = os.getenv("MAIL_SERVER", "smtp.gmail.com")
    smtp_port = int(os.getenv("MAIL_PORT", 587))
    sender_email = os.getenv("MAIL_USERNAME")
    sender_password = os.getenv("MAIL_PASSWORD")
    
    if not sender_email or not sender_password:
        print("❌ Lỗi: Chưa cấu hình MAIL_USERNAME hoặc MAIL_PASSWORD trong file .env")
        return False

    # Tạo bố cục Email
    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = target_email
    msg['Subject'] = "[iKids Learning] Mã OTP Xác Thực"
    
    body = f"""
    Chào bạn,
    
    Bạn đã gửi yêu cầu xác thực trên ứng dụng iKids Learning.
    Mã xác thực OTP của bạn là: {otp_code}
    
    Mã này có hiệu lực trong vòng 5 phút. Vui lòng không chia sẻ mã này cho bất kỳ ai.
    
    Trân trọng,
    Đội ngũ iKids.
    """
    msg.attach(MIMEText(body, 'plain', 'utf-8'))
    
    # Kết nối Server Gmail và gửi
    try:
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls() # Bật bảo mật đường truyền
        server.login(sender_email, sender_password)
        server.sendmail(sender_email, target_email, msg.as_string())
        server.quit()
        print(f"📧 [SMTP] Đã gửi thư chứa OTP thành công tới: {target_email}")
        return True
    except Exception as e:
        print(f"❌ [SMTP] Gửi mail thất bại: {e}")
        return False

# ĐÃ SỬA CHỮA: Bỏ tham số prefix ở đây để không bị nhân đôi đường dẫn
router = APIRouter(tags=["Authentication"])

@router.get("/admin/stats")
async def get_admin_stats(current_admin = Depends(get_current_user)):
    """API giả lập trả về dữ liệu thống kê cho Admin Dashboard"""
    # Kiểm tra quyền Admin
    if current_admin["role"] != "admin":
        raise HTTPException(status_code=403, detail="Chỉ Admin mới xem được thống kê")
        
    # Trả về số liệu ảo tạm thời để Flutter có dữ liệu hiển thị
    return {
        "total_students": 150,
        "total_teachers": 12,
        "active_courses": 5,
        "revenue_this_month": "50,000,000 VND"
    }

async def register(user: UserCreate, db = Depends(get_db)):
    """API Đăng ký tài khoản mới (Giai đoạn 1: Lưu thông tin tạm, kích hoạt gửi OTP)"""
    # Bạn cũng có thể gọi send_email_otp() ở trong services.py của hàm register_user nếu muốn
    return await register_user(db, user)

@router.post("/verify-registration-otp")
async def api_verify_registration_otp(payload: OTPVerifyRequest, db = Depends(get_db)):
    """API Xác thực OTP đăng ký (Giai đoạn 2: Kích hoạt chính thức tài khoản người dùng)"""
    return await verify_registration_otp(db, payload)

@router.post("/login", response_model=TokenResponse)
async def login(user: UserLogin, db = Depends(get_db)):
    """API Đăng nhập và nhận Token (Chỉ cho phép tài khoản đã kích hoạt OTP truy cập)"""
    return await login_user(db, user)

@router.post("/parent/create-student")
async def api_create_student_by_parent(
    student_data: UserCreate, 
    parent_id: str = Header(...),
    db = Depends(get_db)
):
    """API để Phụ huynh tạo tài khoản cho con"""
    return await create_student_by_parent(db, parent_id, student_data)

@router.get("/admin/staff-list")
async def get_staff_list(
    db = Depends(get_db), 
    current_admin = Depends(get_current_user)
):
    if current_admin["role"] != "admin":
        raise HTTPException(status_code=403, detail="Quyền hạn không đủ")
    
    staff = await db.users.find(
        {"role": {"$in": ["teacher", "operator"]}}
    ).to_list(length=100)
    
    for s in staff:
        s["_id"] = str(s["_id"])
        if "subjects" not in s or s["subjects"] is None:
            s["subjects"] = []
        if "password" in s:
            del s["password"] 
    
    return staff

@router.post("/admin/create-staff")
async def create_staff(
    staff_data: UserCreate, 
    db = Depends(get_db), 
    current_admin = Depends(get_current_user)
):
    if current_admin["role"] != "admin":
        raise HTTPException(status_code=403, detail="Chỉ Admin mới có quyền này")
    
    result = await register_user(db, staff_data)
    
    await db.users.update_one(
        {"email": staff_data.email.strip().lower()},
        {"$set": {"is_active": True}, "$unset": {"otp_code": "", "otp_expires_at": ""}}
    )
    
    return {"message": f"Đã tạo tài khoản {staff_data.role} thành công và kích hoạt sẵn."}

@router.put("/admin/update-staff/{staff_id}")
async def update_staff(
    staff_id: str,
    staff_data: dict,
    db = Depends(get_db),
    current_admin = Depends(get_current_user)
):
    if current_admin["role"] != "admin":
        raise HTTPException(status_code=403, detail="Chỉ Admin mới có quyền chỉnh sửa thông tin nhân sự")
    
    try:
        update_data = {
            k: v for k, v in staff_data.items() 
            if k in ["name", "role", "email", "phone_number", "birth_date", "is_active", "subjects"]
        }
        
        res = await db.users.update_one(
            {"_id": ObjectId(staff_id)},
            {"$set": update_data}
        )
        if res.matched_count:
            return {"status": "success", "message": "Cập nhật thông tin nhân sự thành công"}
        raise HTTPException(status_code=404, detail="Không tìm thấy tài khoản nhân sự cần sửa")
    except Exception:
        raise HTTPException(status_code=400, detail="Lỗi dữ liệu hoặc định dạng mã định danh ID không hợp lệ")

# ==========================================
# CÁC API DÀNH CHO TRANG CÁ NHÂN (TẤT CẢ USER)
# ==========================================

@router.put("/profile/change-password")
async def change_own_password(
    payload: dict,
    db = Depends(get_db),
    current_user = Depends(get_current_user)
):
    old_password = payload.get("old_password")
    new_password = payload.get("new_password")
    
    if not old_password or not new_password:
        raise HTTPException(status_code=400, detail="Vui lòng điền đầy đủ mật khẩu cũ và mới")
        
    user_in_db = await db.users.find_one({"_id": ObjectId(str(current_user["_id"]))})
    if not user_in_db:
        raise HTTPException(status_code=404, detail="Không tìm thấy thông tin tài khoản")
        
    if not verify_password(old_password, user_in_db["password"]):
        raise HTTPException(status_code=400, detail="Mật khẩu hiện tại không chính xác")
        
    hashed_password = get_password_hash(new_password)
    await db.users.update_one(
        {"_id": ObjectId(str(current_user["_id"]))},
        {"$set": {"password": hashed_password}}
    )
    return {"status": "success", "message": "Đổi mật khẩu thành công"}

@router.put("/profile/update")
async def update_own_profile(
    payload: dict,
    db = Depends(get_db),
    current_user = Depends(get_current_user)
):
    update_data = {
        k: v for k, v in payload.items() 
        if k in ["name", "phone_number", "birth_date", "facebook", "hobbies"]
    }
    
    if not update_data.get("name") or not update_data.get("name").strip():
        raise HTTPException(status_code=400, detail="Họ và tên không được để trống")
        
    await db.users.update_one(
        {"_id": ObjectId(str(current_user["_id"]))},
        {"$set": update_data}
    )
    return {"status": "success", "message": "Cập nhật thông tin cá nhân thành công"}

@router.post("/forgot-password")
async def forgot_password(payload: dict, db = Depends(get_db)):
    """API Bước 1: Tạo mã OTP khôi phục dựa vào Email và gửi Email thật"""
    email = payload.get("email")
    if not email:
        raise HTTPException(status_code=400, detail="Vui lòng cung cấp địa chỉ Email")
        
    user = await db.users.find_one({"email": email})
    if not user:
        raise HTTPException(status_code=404, detail="Email không tồn tại trong hệ thống.")
        
    otp = str(random.randint(100000, 999999))
    expiry = datetime.now() + timedelta(minutes=5)
    
    await db.users.update_one(
        {"email": email},
        {"$set": {"reset_otp": otp, "otp_expiry": expiry}}
    )
    
    # Gọi hàm gửi Email thực tế ở đây
    mail_sent = send_email_otp(email, otp)
    
    if not mail_sent:
        raise HTTPException(status_code=500, detail="Hệ thống không thể gửi email lúc này. Vui lòng kiểm tra lại cấu hình hệ thống.")
    
    return {"status": "success", "message": "Mã OTP khôi phục đã được gửi vào hòm thư của bạn."}

@router.post("/verify-reset")
async def verify_reset(payload: dict, db = Depends(get_db)):
    """API Bước 2: Kiểm tra OTP và tiến hành thay đổi mật khẩu mới"""
    email = payload.get("email")
    otp = payload.get("otp")
    new_password = payload.get("new_password")
    
    if not email or not otp or not new_password:
        raise HTTPException(status_code=400, detail="Thiếu dữ liệu xác thực")
        
    user = await db.users.find_one({"email": email})
    if not user:
        raise HTTPException(status_code=404, detail="Tài khoản không tồn tại.")
        
    if not user.get("reset_otp") or user.get("reset_otp") != str(otp):
        raise HTTPException(status_code=400, detail="Mã OTP sai hoặc đã hết hạn.")
        
    if not user.get("otp_expiry") or datetime.now() > user.get("otp_expiry"):
        raise HTTPException(status_code=400, detail="Mã OTP đã hết hạn.")
        
    hashed_password = get_password_hash(new_password)
    await db.users.update_one(
        {"email": email},
        {
            "$set": {"password": hashed_password},
            "$unset": {"reset_otp": "", "otp_expiry": ""}
        }
    )

    
    return {"status": "success", "message": "Mật khẩu thay đổi thành công!"}