from fastapi import APIRouter, Depends, HTTPException, Header
from core.database import get_db
from core.security import get_current_user 
from .schemas import UserCreate, UserLogin, TokenResponse
from .services import register_user, login_user, create_student_by_parent

router = APIRouter(prefix="/api/auth", tags=["Authentication"])

@router.post("/register")
async def register(user: UserCreate, db = Depends(get_db)):
    """API Đăng ký tài khoản mới"""
    return await register_user(db, user)

@router.post("/login", response_model=TokenResponse)
async def login(user: UserLogin, db = Depends(get_db)):
    """API Đăng nhập và nhận Token"""
    return await login_user(db, user)

@router.post("/parent/create-student")
async def api_create_student_by_parent(
    student_data: UserCreate, 
    parent_id: str = Header(...), # Lấy ID phụ huynh từ Header
    db = Depends(get_db)
):
    """API để Phụ huynh tạo tài khoản cho con"""
    return await create_student_by_parent(db, parent_id, student_data)

# --- API MỚI THÊM ĐỂ FRONTEND QUÉT TOÀN BỘ DATA DỄ DÀNG ---
@router.get("/users")
async def get_all_users(db = Depends(get_db)):
    """API lấy toàn bộ user (Giáo viên, Học sinh...) để Frontend tự do lọc"""
    users = await db.users.find({}).to_list(length=1000)
    for u in users:
        u["_id"] = str(u["_id"])
        if "password" in u:
            del u["password"] # Bảo mật: không bao giờ trả về mật khẩu
    return users

@router.get("/admin/staff-list")
async def get_staff_list(
    db = Depends(get_db), 
    current_admin = Depends(get_current_user)
):
    if current_admin["role"] != "admin":
        raise HTTPException(status_code=403, detail="Quyền hạn không đủ")
    
    # BỎ BỘ LỌC CỨNG: Lấy hết lên rồi lọc bằng Python để bắt được chữ Hoa/Thường và Tiếng Việt
    all_users = await db.users.find({}).to_list(length=1000)
    
    staff = []
    for s in all_users:
        # Chuyển role về chữ thường để so sánh không bị trượt
        role = str(s.get("role", s.get("quyen", ""))).lower()
        
        # Bắt dính tất cả các thể loại role Giáo viên và Vận hành
        if "teacher" in role or "giáo viên" in role or "giao vien" in role or "operator" in role or "vận hành" in role:
            s["_id"] = str(s["_id"])
            if "password" in s:
                del s["password"] # Bảo mật
            staff.append(s)
            
    return staff

@router.post("/admin/create-staff")
async def create_staff(
    staff_data: UserCreate, 
    db = Depends(get_db), 
    current_admin = Depends(get_current_user)
):
    if current_admin["role"] != "admin":
        raise HTTPException(status_code=403, detail="Chỉ Admin mới có quyền này")
    
    # Sử dụng lại logic đăng ký nhưng cho phép chọn Role
    result = await register_user(db, staff_data)
    return {"message": f"Đã tạo tài khoản {staff_data.role} thành công"}