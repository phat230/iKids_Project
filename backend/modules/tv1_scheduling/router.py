from fastapi import APIRouter, Depends, HTTPException
from core.database import get_db
from .models import TeacherRequestCreate
from bson import ObjectId
from datetime import datetime
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
router = APIRouter()

# 1. API tiếp nhận đơn từ Giáo viên
@router.post("/submit-request")
async def submit_teacher_request(request: TeacherRequestCreate, db = Depends(get_db)):
    request_dict = request.model_dump()
    request_dict["status"] = "pending"
    request_dict["created_at"] = datetime.now()
    
    result = await db.teacher_requests.insert_one(request_dict)
    return {"message": "Đã gửi đơn thành công", "id": str(result.inserted_id)}

# 2. API lấy danh sách đơn chờ duyệt cho Admin
@router.get("/pending-requests")
async def get_pending_requests(db = Depends(get_db)):
    cursor = db.teacher_requests.find({"status": "pending"})
    requests_list = []
    async for doc in cursor:
        doc["id"] = str(doc["_id"])
        del doc["_id"]
        requests_list.append(doc)
    return requests_list

# 3. API để Admin phê duyệt đơn
@router.post("/approve/{request_id}")
async def approve_request(request_id: str, db = Depends(get_db)):
    try:
        res = await db.teacher_requests.update_one(
            {"_id": ObjectId(request_id)},
            {"$set": {
                "status": "approved",
                "updated_at": datetime.now()
            }}
        )
        if res.modified_count:
            return {"status": "success", "message": "Đã phê duyệt đơn"}
        raise HTTPException(status_code=404, detail="Không tìm thấy đơn")
    except:
        raise HTTPException(status_code=400, detail="ID không hợp lệ")

# 4. API CHO ADMIN: Lấy lịch sử các đơn ĐÃ XỬ LÝ
@router.get("/request-history")
async def get_request_history(db = Depends(get_db)):
    cursor = db.teacher_requests.find({"status": {"$ne": "pending"}}).sort("updated_at", -1)
    history_list = []
    async for doc in cursor:
        doc["id"] = str(doc["_id"])
        del doc["_id"]
        history_list.append(doc)
    return history_list

# 5. API CHO ADMIN: Từ chối đơn
@router.post("/reject/{request_id}")
async def reject_request(request_id: str, db = Depends(get_db)):
    try:
        res = await db.teacher_requests.update_one(
            {"_id": ObjectId(request_id)},
            {"$set": {
                "status": "rejected",
                "updated_at": datetime.now()
            }}
        )
        if res.modified_count:
            return {"status": "success"}
        raise HTTPException(status_code=404, detail="Không tìm thấy đơn")
    except:
        raise HTTPException(status_code=400, detail="ID không hợp lệ")

# --- QUẢN LÝ NHÂN SỰ & TÀI KHOẢN ---

# 1. API: Lấy danh sách tất cả tài khoản
@router.get("/staff")
async def get_all_staff(db = Depends(get_db)):
    cursor = db.users.find().sort("name", 1)
    staff_list = []
    async for doc in cursor:
        doc["id"] = str(doc["_id"])
        del doc["_id"]
        if "password" in doc:
            del doc["password"]
        staff_list.append(doc)
    return staff_list

# 2. API: Thêm nhân sự mới (Cấp tài khoản & Mã hóa mật khẩu)
@router.post("/staff/add")
async def add_staff(staff_data: dict, db = Depends(get_db)):
    existing_user = await db.users.find_one({"email": staff_data["email"]})
    if existing_user:
        raise HTTPException(status_code=400, detail="Email này đã được cấp tài khoản!")

    if "password" in staff_data:
        staff_data["password"] = pwd_context.hash(staff_data["password"])

    staff_data["created_at"] = datetime.now()
    result = await db.users.insert_one(staff_data)
    return {"status": "success", "id": str(result.inserted_id)}

# 3. API: Xóa tài khoản nhân sự
@router.delete("/staff/{staff_id}")
async def delete_staff(staff_id: str, db = Depends(get_db)):
    await db.users.delete_one({"_id": ObjectId(staff_id)})
    return {"status": "success"}

# 4. API: Cập nhật thông tin cơ bản hoặc trạng thái (Vô hiệu hóa)
@router.put("/staff/{staff_id}")
async def update_staff(staff_id: str, staff_data: dict, db = Depends(get_db)):
    try:
        # Lọc các trường được phép cập nhật
        update_data = {k: v for k, v in staff_data.items() if k in ["name", "role", "email", "phone", "status"]}
        res = await db.users.update_one(
            {"_id": ObjectId(staff_id)},
            {"$set": update_data}
        )
        if res.matched_count:
            return {"status": "success"}
        raise HTTPException(status_code=404, detail="Không tìm thấy tài khoản")
    except Exception:
        raise HTTPException(status_code=400, detail="Lỗi cập nhật")

# 5. API: Đổi mật khẩu (Reset Password)
@router.put("/staff/{staff_id}/password")
async def reset_password(staff_id: str, pwd_data: dict, db = Depends(get_db)):
    try:
        new_pwd = pwd_data.get("password")
        if not new_pwd:
            raise HTTPException(status_code=400, detail="Mật khẩu rỗng")
            
        hashed_password = pwd_context.hash(new_pwd)
        res = await db.users.update_one(
            {"_id": ObjectId(staff_id)},
            {"$set": {"password": hashed_password}}
        )
        if res.matched_count:
            return {"status": "success"}
        raise HTTPException(status_code=404, detail="Không tìm thấy tài khoản")
    except Exception:
        raise HTTPException(status_code=400, detail="Lỗi cập nhật mật khẩu")