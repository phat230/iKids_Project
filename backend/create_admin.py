import asyncio
import bcrypt
from motor.motor_asyncio import AsyncIOMotorClient

# 1. Cấu hình kết nối (Dựa trên thông tin bạn đã cung cấp)
MONGO_DETAILS = "mongodb+srv://phay123321_db_user:2qxBnbR6Brd8mOYu@cluster0.v6iwegp.mongodb.net/"
DATABASE_NAME = "iKids_Project_DB"

async def create_initial_admin():
    client = AsyncIOMotorClient(MONGO_DETAILS)
    db = client[DATABASE_NAME]
    
    # Thông tin tài khoản Admin muốn tạo
    admin_email = "admin@ikids.com" # Bạn có thể đổi email này
    admin_password = "admin123@password" # Bạn nên đổi mật khẩu này
    admin_name = "Tổng Quản Trị iKids"

    # Kiểm tra xem admin đã tồn tại chưa
    existing_admin = await db.users.find_one({"email": admin_email})
    if existing_admin:
        print(f"[-] Tai khoan {admin_email} da ton tai tren he thong.")
        return

    # Mã hóa mật khẩu (Dùng bcrypt trực tiếp như chúng ta đã thống nhất)
    hashed_password = bcrypt.hashpw(admin_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    # Dữ liệu Admin
    admin_user = {
        "name": admin_name,
        "email": admin_email,
        "password": hashed_password,
        "role": "admin", # Quyền cao nhất
        "created_at": None # Hoặc dùng datetime.utcnow()
    }

    # Chèn vào database
    result = await db.users.insert_one(admin_user)
    if result.inserted_id:
        print(f"[+] Tao thanh cong tai khoan Admin!")
        print(f"    Email: {admin_email}")
        print(f"    Mat khau: {admin_password}")
        print("    Bay gio ban co the dung tai khoan nay de dang nhap.")

if __name__ == "__main__":
    asyncio.run(create_initial_admin())