from fastapi import HTTPException
from core.security import get_password_hash, verify_password, create_access_token
from .schemas import UserCreate, UserLogin
# Bạn có thể import model vào để kiểm tra dữ liệu trước khi lưu (Tùy chọn)
from .models import UserDBModel 

async def register_user(db, user_data: UserCreate):
    # 1. Kiểm tra email đã tồn tại chưa
    existing_user = await db.users.find_one({"email": user_data.email})
    if existing_user:
        raise HTTPException(status_code=400, detail="Email này đã được đăng ký.")

    # 2. CHẶN ROLE TRÁI PHÉP: Chỉ cho phép tự do đăng ký Student và Parent
    public_roles = ["student", "parent"]
    if user_data.role not in public_roles:
        raise HTTPException(
            status_code=403, 
            detail="Bạn không có quyền tạo tài khoản cho chức danh này. Vui lòng liên hệ Admin."
        )

    # 3. Chuẩn bị dữ liệu để lưu vào DB
    user_dict = user_data.dict()
    user_dict["password"] = get_password_hash(user_dict["password"])
    
    db_user = UserDBModel(**user_dict)
    result = await db.users.insert_one(db_user.dict())
    
    return {"message": "Đăng ký thành công!", "user_id": str(result.inserted_id)}    # 1. Kiểm tra email đã tồn tại chưa
    existing_user = await db.users.find_one({"email": user_data.email})
    if existing_user:
        raise HTTPException(status_code=400, detail="Email này đã được đăng ký.")

    # 2. Kiểm tra role hợp lệ (ĐÃ THÊM PARENT)
    valid_roles = ["student", "teacher", "admin", "operator", "parent"]
    if user_data.role not in valid_roles:
        raise HTTPException(status_code=400, detail="Role không hợp lệ.")

    # 3. Chuẩn bị dữ liệu để lưu vào DB
    user_dict = user_data.dict()
    user_dict["password"] = get_password_hash(user_dict["password"])
    
    # Đưa qua UserDBModel để tự động sinh created_at và is_active
    db_user = UserDBModel(**user_dict)
    
    result = await db.users.insert_one(db_user.dict())
    return {"message": "Đăng ký thành công!", "user_id": str(result.inserted_id)}

async def login_user(db, login_data: UserLogin):
    # 1. Tìm user bằng email
    user = await db.users.find_one({"email": login_data.email})
    if not user:
        raise HTTPException(status_code=404, detail="Email không tồn tại.")

    # 2. Kiểm tra mật khẩu
    if not verify_password(login_data.password, user["password"]):
        raise HTTPException(status_code=401, detail="Sai mật khẩu.")

    # 3. Tạo Token chứa id và role
    token_data = {"sub": str(user["_id"]), "role": user["role"]}
    access_token = create_access_token(token_data)

    # 4. Trả về token và thông tin cơ bản
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user_info": {
            "name": user["name"],
            "email": user["email"],
            "role": user["role"]
        }
    }