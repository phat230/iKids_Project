from fastapi import APIRouter, Depends
from core.database import get_db
from .schemas import UserCreate, UserLogin, TokenResponse
from .services import register_user, login_user

router = APIRouter(prefix="/api/auth", tags=["Authentication"])

@router.post("/register")
async def register(user: UserCreate, db = Depends(get_db)):
    """API Đăng ký tài khoản mới"""
    return await register_user(db, user)

@router.post("/login", response_model=TokenResponse)
async def login(user: UserLogin, db = Depends(get_db)):
    """API Đăng nhập và nhận Token"""
    return await login_user(db, user)