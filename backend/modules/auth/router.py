from fastapi import APIRouter, Depends, HTTPException, Header
from core.database import get_db
from core.security import get_current_user, verify_password, get_password_hash 
from .schemas import UserCreate, UserLogin, TokenResponse, OTPVerifyRequest
from .services import register_user, login_user, create_student_by_parent, verify_registration_otp
from bson import ObjectId # Import để xử lý ép kiểu chuỗi sang ObjectId của MongoDB
import random
from datetime import datetime, timedelta

router = APIRouter(prefix="/api/auth", tags=["Authentication"])

@router.post("/register")
async def register(user: UserCreate, db = Depends(get_db)):
    """API Đăng ký tài khoản mới (Giai đoạn 1: Lưu thông tin tạm, kích hoạt gửi OTP)"""
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
    parent_id: str = Header(...), # Lấy ID phụ huynh từ Header
    db = Depends(get_db)
):
    """API để Phụ huynh tạo tài khoản cho con (Tự động kích hoạt & kiểm tra giới hạn tuổi học sinh)"""
    return await create_student_by_parent(db, parent_id, student_data)

@router.get("/admin/staff-list")
async def get_staff_list(
    db = Depends(get_db), 
    current_admin = Depends(get_current_user)
):
    if current_admin["role"] != "admin":
        raise HTTPException(status_code=403, detail="Quyền hạn không đủ")
    
    # Lấy danh sách user có role là giáo viên hoặc vận hành
    staff = await db.users.find(
        {"role": {"$in": ["teacher", "operator"]}}
    ).to_list(length=100)
    
    # Chuyển đổi ObjectId thành string để trả về JSON
    for s in staff:
        s["_id"] = str(s["_id"])
        # Đảm bảo nếu trường subjects chưa có trong bản ghi cũ thì tự gán mảng rỗng để tránh lỗi Frontend
        if "subjects" not in s or s["subjects"] is None:
            s["subjects"] = []
        if "password" in s:
            del s["password"] # Bảo mật: không trả về mật khẩu
    
    return staff

@router.post("/admin/create-staff")
async def create_staff(
    staff_data: UserCreate, 
    db = Depends(get_db), 
    current_admin = Depends(get_current_user)
):
    if current_admin["role"] != "admin":
        raise HTTPException(status_code=403, detail="Chỉ Admin mới có quyền này")
    
    # Các tài khoản do Admin trực tiếp tạo ra cho nhân sự có thể bỏ qua bước xác thực hoặc tự động kích hoạt
    # Thiết lập mặc định sang student_data để ghi đè hoặc giữ nguyên tùy theo cấu hình nhóm bạn mong muốn
    result = await register_user(db, staff_data)
    
    # Nếu admin tạo hộ thì có thể tự động kích hoạt luôn không bắt nhân viên quét OTP từ đầu
    await db.users.update_one(
        {"email": staff_data.email.strip().lower()},
        {"$set": {"is_active": True}, "$unset": {"otp_code": "", "otp_expires_at": ""}}
    )
    
    return {"message": f"Đã tạo tài khoản {staff_data.role} thành công và kích hoạt sẵn."}

# API cập nhật thông tin nhân sự (Dành cho Admin sửa nhân viên)
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
        # Lọc các trường an toàn được phép cập nhật và bổ sung "subjects", "phone_number", "birth_date"
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
    """API bảo mật cho phép TẤT CẢ các tài khoản tự thay đổi mật khẩu chính mình"""
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
    """API cho phép người dùng tự chỉnh sửa thông tin cá nhân mở rộng công khai"""
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
    """API Bước 1: Tạo mã OTP khôi phục dựa vào Email"""
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
    
    print(f"\n==================================================")
    print(f"📩 [MÃ OTP KHÔI PHỤC iKids] Gửi đến hòm thư: {email}")
    print(f"👉 MÃ XÁC THỰC LÀ: {otp}")
    print(f"==================================================\n")
    
    return {"status": "success", "message": "Mã OTP khôi phục đã được gửi."}

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