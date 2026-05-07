from fastapi import HTTPException
from core.security import get_password_hash
from .models import UserDBModel
from .schemas import UserCreate

async def admin_create_staff(db, staff_data: UserCreate, admin_user: dict):
    # Kiểm tra quyền (Chỉ Admin mới được dùng hàm này)
    if admin_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Bạn không có quyền thực hiện hành động này")

    clean_email = staff_data.email.strip().lower()
    
    # Kiểm tra trùng email
    existing_user = await db.users.find_one({"email": clean_email})
    if existing_user:
        raise HTTPException(status_code=400, detail="Email này đã tồn tại trong hệ thống")

    user_dict = staff_data.dict()
    user_dict["email"] = clean_email
    user_dict["password"] = get_password_hash(user_dict["password"])
    
    # Ở đây Admin có thể chỉ định role là 'teacher' hoặc 'operator'
    db_user = UserDBModel(**user_dict)
    result = await db.users.insert_one(db_user.dict())
    
    return {"message": f"Đã tạo thành công tài khoản {staff_data.role}", "id": str(result.inserted_id)}