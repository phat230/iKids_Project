import bcrypt
from datetime import datetime, timedelta
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt

SECRET_KEY = "ikids_super_secret_key_2026_secured_version"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24

security = HTTPBearer()

def get_password_hash(password: str):
    """Mã hóa mật khẩu bằng thư viện bcrypt trực tiếp"""
    # Chuyển string sang bytes
    pwd_bytes = password.encode('utf-8')
    # Tạo salt và mã hóa
    salt = bcrypt.gensalt()
    hashed_password = bcrypt.hashpw(pwd_bytes, salt)
    # Trả về string để lưu vào MongoDB
    return hashed_password.decode('utf-8')

def verify_password(plain_password: str, hashed_password: str):
    """Kiểm tra mật khẩu"""
    try:
        pwd_bytes = plain_password.encode('utf-8')
        hashed_bytes = hashed_password.encode('utf-8')
        return bcrypt.checkpw(pwd_bytes, hashed_bytes)
    except Exception:
        return False

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        role: str = payload.get("role")
        if user_id is None or role is None:
            raise HTTPException(status_code=401, detail="Token không hợp lệ")
        return {"user_id": user_id, "role": role}
    except Exception:
        raise HTTPException(status_code=401, detail="Xác thực thất bại hoặc Token hết hạn")