from fastapi import APIRouter, Depends
from core.database import get_db
from .schemas import UserCreate, UserLogin, TokenResponse
from .services import register_user, login_user
from .services import create_student_by_parent
from fastapi import Header
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