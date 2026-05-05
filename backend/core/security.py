from passlib.context import CryptContext
from datetime import datetime, timedelta
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt

# 1. KHAI BÁO HẰNG SỐ LÊN TRÊN CÙNG ĐỂ TRÁNH LỖI KHI GỌI HÀM
SECRET_KEY = "ikids_super_secret_key_2026"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # Token sống trong 24h

# 2. KHỞI TẠO CÔNG CỤ
security = HTTPBearer()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# 3. CÁC HÀM XỬ LÝ MẬT KHẨU VÀ TOKEN
def verify_password(plain_password: str, hashed_password: str):
    # Cắt ngắn mật khẩu lúc kiểm tra cho đồng bộ với lúc tạo
    if len(plain_password) > 72:
        plain_password = plain_password[:72]
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str):
    # Bcrypt chỉ hỗ trợ tối đa 72 bytes. Ta phải cắt ngắn để tránh sập Server.
    if len(password) > 72:
        password = password[:72]
    return pwd_context.hash(password)

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

# 4. LÍNH GÁC BẢO VỆ API
def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Giải mã Token để lấy thông tin user. Nếu Token sai/hết hạn sẽ chặn lại."""
    token = credentials.credentials
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        role: str = payload.get("role")
        if user_id is None or role is None:
            raise HTTPException(status_code=401, detail="Token không hợp lệ")
        return {"user_id": user_id, "role": role}
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token đã hết hạn. Vui lòng đăng nhập lại.")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Xác thực thất bại")