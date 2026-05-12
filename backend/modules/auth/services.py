from fastapi import HTTPException
from core.security import get_password_hash, verify_password, create_access_token
from .schemas import UserCreate, UserLogin
from .models import UserDBModel
from bson import ObjectId


async def register_user(db, user_data: UserCreate):
    # Chuẩn hóa email: xóa khoảng trắng 2 đầu và in thường
    clean_email = user_data.email.strip().lower()

    existing_user = await db.users.find_one({"email": clean_email})

    if existing_user:
        raise HTTPException(
            status_code=400,
            detail="Email này đã được đăng ký."
        )

    valid_roles = ["student", "teacher", "admin", "operator", "parent"]

    if user_data.role not in valid_roles:
        raise HTTPException(
            status_code=400,
            detail="Role không hợp lệ."
        )

    user_dict = user_data.dict()
    user_dict["email"] = clean_email
    user_dict["password"] = get_password_hash(user_dict["password"])

    db_user = UserDBModel(**user_dict)

    result = await db.users.insert_one(db_user.dict())

    return {
        "message": "Đăng ký thành công!",
        "user_id": str(result.inserted_id)
    }


async def login_user(db, login_data: UserLogin):

    # Chuẩn hóa email lúc đăng nhập
    clean_email = login_data.email.strip().lower()

    # Tìm user
    user = await db.users.find_one({"email": clean_email})

    # Không tìm thấy tài khoản
    if not user:
        raise HTTPException(
            status_code=404,
            detail="Email không tồn tại. Vui lòng kiểm tra lại."
        )

    # Kiểm tra tài khoản có bị vô hiệu hóa không
    if user.get("is_active") == False:
        raise HTTPException(
            status_code=403,
            detail="Tài khoản đã bị vô hiệu hóa"
        )

    # Kiểm tra mật khẩu
    if not verify_password(login_data.password, user["password"]):
        raise HTTPException(
            status_code=401,
            detail="Sai mật khẩu."
        )

    # Tạo token
    token_data = {
        "sub": str(user["_id"]),
        "role": user["role"]
    }

    access_token = create_access_token(token_data)

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user_info": {
            "id": str(user["_id"]),
            "name": user["name"],
            "email": user["email"],
            "role": user["role"]
        }
    }


async def create_student_by_parent(db, parent_id: str, student_data: UserCreate):

    """Phụ huynh tạo tài khoản cho con và tự động liên kết"""

    # Chuẩn hóa email
    clean_email = student_data.email.strip().lower()

    existing_user = await db.users.find_one({"email": clean_email})

    if existing_user:
        raise HTTPException(
            status_code=400,
            detail="Email này đã được sử dụng."
        )

    student_dict = student_data.dict()

    student_dict["email"] = clean_email
    student_dict["password"] = get_password_hash(student_dict["password"])
    student_dict["role"] = "student"

    db_student = UserDBModel(**student_dict)

    result = await db.users.insert_one(db_student.dict())

    new_student_id = str(result.inserted_id)

    # Liên kết ID
    await db.users.update_one(
        {"_id": ObjectId(parent_id)},
        {"$push": {"student_ids_ref": new_student_id}} 
    )

    await db.gamification_profiles.insert_one({
        "student_id": int(new_student_id) if new_student_id.isdigit() else new_student_id,
        "total_coins": 0,
        "lifetime_coins": 0,
        "rank_level": "Beginner",
        "current_streak": 0
    })

    return {
        "status": "success",
        "message": "Tạo tài khoản và liên kết thành công!",
        "student_id": new_student_id
    }