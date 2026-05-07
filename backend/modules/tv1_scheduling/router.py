from fastapi import APIRouter, Depends, HTTPException
from core.database import get_db
from .models import TeacherRequestCreate
from bson import ObjectId
from datetime import datetime

router = APIRouter()

# 1. API tiếp nhận đơn từ Giáo viên
@router.post("/submit-request")
async def submit_teacher_request(request: TeacherRequestCreate, db = Depends(get_db)):
    request_dict = request.model_dump() # Pydantic v2 dùng model_dump thay vì dict
    request_dict["status"] = "pending" # Mặc định chờ Admin duyệt
    request_dict["created_at"] = datetime.now() # Ghi lại thời gian gửi đơn
    
    # Lưu vào collection 'teacher_requests' trong MongoDB của bạn
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

# 3. API để Admin phê duyệt đơn (Có lưu thời gian thực)
@router.post("/approve/{request_id}")
async def approve_request(request_id: str, db = Depends(get_db)):
    try:
        res = await db.teacher_requests.update_one(
            {"_id": ObjectId(request_id)},
            {"$set": {
                "status": "approved",
                "updated_at": datetime.now() # Ghi nhận thời gian xử lý
            }}
        )
        if res.modified_count:
            return {"status": "success", "message": "Đã phê duyệt đơn"}
        raise HTTPException(status_code=404, detail="Không tìm thấy đơn")
    except:
        raise HTTPException(status_code=400, detail="ID không hợp lệ")

# 4. API CHO ADMIN: Lấy lịch sử các đơn ĐÃ XỬ LÝ (Duyệt hoặc Từ chối)
@router.get("/request-history")
async def get_request_history(db = Depends(get_db)):
    # Tìm các đơn có status KHÁC 'pending', sắp xếp mới nhất lên đầu
    cursor = db.teacher_requests.find({"status": {"$ne": "pending"}}).sort("updated_at", -1)
    history_list = []
    async for doc in cursor:
        doc["id"] = str(doc["_id"])
        del doc["_id"]
        history_list.append(doc)
    return history_list

# 5. API CHO ADMIN: Từ chối đơn (Có lưu thời gian thực)
@router.post("/reject/{request_id}")
async def reject_request(request_id: str, db = Depends(get_db)):
    try:
        res = await db.teacher_requests.update_one(
            {"_id": ObjectId(request_id)},
            {"$set": {
                "status": "rejected",
                "updated_at": datetime.now() # Ghi nhận thời gian xử lý
            }}
        )
        if res.modified_count:
            return {"status": "success"}
        raise HTTPException(status_code=404, detail="Không tìm thấy đơn")
    except:
        raise HTTPException(status_code=400, detail="ID không hợp lệ")

# --- QUẢN LÝ NHÂN SỰ ---

# 1. API: Lấy danh sách tất cả nhân sự
@router.get("/staff")
async def get_all_staff(db = Depends(get_db)):
    cursor = db.staff.find().sort("name", 1)
    staff_list = []
    async for doc in cursor:
        doc["id"] = str(doc["_id"])
        del doc["_id"]
        staff_list.append(doc)
    return staff_list

# 2. API: Thêm nhân sự mới
@router.post("/staff/add")
async def add_staff(staff_data: dict, db = Depends(get_db)):
    # staff_data gồm: name, role, email, phone, status
    result = await db.staff.insert_one(staff_data)
    return {"status": "success", "id": str(result.inserted_id)}

# 3. API: Xóa nhân sự
@router.delete("/staff/{staff_id}")
async def delete_staff(staff_id: str, db = Depends(get_db)):
    await db.staff.delete_one({"_id": ObjectId(staff_id)})
    return {"status": "success"}