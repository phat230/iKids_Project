from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional, List
from datetime import date
import re

def calculate_age(born_date_str: str) -> int:
    """Hàm helper để tính tuổi từ chuỗi ngày sinh YYYY-MM-DD"""
    try:
        born = date.fromisoformat(born_date_str)
        today = date.today()
        return today.year - born.year - ((today.month, today.day) < (born.month, born.day))
    except ValueError:
        raise ValueError("Định dạng ngày sinh không hợp lệ. Phải là YYYY-MM-DD.")

class UserCreate(BaseModel):
    name: str
    email: EmailStr
    password: str
    role: str
    
    # Bổ sung các trường nâng cao bảo mật
    phone_number: Optional[str] = Field(None, description="Số điện thoại nhận OTP")
    birth_date: Optional[str] = Field(None, description="Ngày sinh định dạng YYYY-MM-DD")
    
    subjects: Optional[List[str]] = None 

    # Ràng buộc điều kiện độ tuổi đầu vào bằng Validator của Pydantic
    @validator('birth_date')
    def validate_age_by_role(cls, v, values):
        role = values.get('role')
        if not v:
            return v
            
        age = calculate_age(v)
        
        # 1. Kiểm tra tuổi của Phụ huynh
        if role == "parent" and age < 18:
            raise ValueError("Phụ huynh đăng ký tài khoản phải từ 18 tuổi trở lên.")
            
        # 2. Kiểm tra giới hạn tuổi của Học sinh (Ví dụ từ 4 đến 16 tuổi)
        if role == "student" and (age < 4 or age > 16):
            raise ValueError("Độ tuổi của học sinh phải nằm trong phạm vi từ 4 đến 16 tuổi.")
            
        return v

    @validator('phone_number')
    def validate_phone_format(cls, v):
        if not v:
            return v
        # Kiểm tra định dạng số điện thoại Việt Nam căn bản (10 chữ số)
        phone_regex = r"^(0[3|5|7|8|9])+([0-9]{8})$"
        if not re.match(phone_regex, v.strip()):
            raise ValueError("Số điện thoại không đúng định dạng Việt Nam (VD: 0912345678).")
        return v.strip()

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_info: dict

# Thêm Schema mới để tiếp nhận dữ liệu khi Form Frontend gửi mã xác thực OTP lên
class OTPVerifyRequest(BaseModel):
    email: EmailStr
    otp_code: str