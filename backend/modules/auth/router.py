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
    
    # Sử dụng lại logic đăng ký nhưng cho phép chọn Role
    result = await register_user(db, staff_data)
    return {"message": f"Đã tạo tài khoản {staff_data.role} thành công"}