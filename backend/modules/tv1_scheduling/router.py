from fastapi import APIRouter, Depends, HTTPException
from core.security import get_current_user
from core.database import get_db
from .models import ClassScheduleModel, TeacherRequestCreate, ClassModel
from bson import ObjectId
from datetime import datetime
from passlib.context import CryptContext
from modules.notification.services import create_notification
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
router = APIRouter()

# 1. API tiếp nhận đơn từ Giáo viên (ĐÃ ĐỒNG BỘ URL VÀ KIỂU DỮ LIỆU ĐỘNG)
@router.post("/requests/create")
async def submit_teacher_request(request_data: dict, db = Depends(get_db)):
    # Nhận dict để linh hoạt xử lý mọi cấu trúc đơn (Xin nghỉ, Đổi lịch, Sự cố...)
    request_data["status"] = "pending"
    
    # Giữ lại thời gian Frontend gửi hoặc tự tạo nếu thiếu
    if "created_at" not in request_data:
        request_data["created_at"] = datetime.now().strftime("%d/%m/%Y %H:%M")
        
    # Xóa ID ảo do Frontend tạo (nếu có) để MongoDB cấp _id chuẩn
    if "id" in request_data:
        del request_data["id"]
        
    result = await db.teacher_requests.insert_one(request_data)
    return {"message": "Đã gửi đơn thành công", "id": str(result.inserted_id)}

# 2. API lấy danh sách đơn chờ duyệt cho Admin
@router.get("/pending-requests")
async def get_pending_requests(db = Depends(get_db)):
    cursor = db.teacher_requests.find({"status": "pending"}).sort("created_at", -1)
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
async def get_all_staff(
    db = Depends(get_db),
    current_user = Depends(get_current_user)
):

    # Chỉ admin được xem
    if current_user["role"] != "admin":
        raise HTTPException(
            status_code=403,
            detail="Chỉ Admin mới có quyền"
        )

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
async def delete_staff(
    staff_id: str,
    db = Depends(get_db),
    current_user = Depends(get_current_user)
):
    # Chỉ Admin mới được xóa
    if current_user["role"] != "admin":
        raise HTTPException(
            status_code=403,
            detail="Chỉ Admin mới có quyền xóa tài khoản"
        )

    user = await db.users.find_one({"_id": ObjectId(staff_id)})

    if not user:
        raise HTTPException(
            status_code=404,
            detail="Không tìm thấy tài khoản"
        )

    # Không cho xóa admin
    if user["role"] == "admin":
        raise HTTPException(
            status_code=403,
            detail="Không thể xóa tài khoản Admin"
        )

    await db.users.delete_one({"_id": ObjectId(staff_id)})

    return {
        "status": "success",
        "message": "Đã xóa tài khoản thành công"
    }

@router.put("/staff/{staff_id}/disable")
async def disable_staff(
    staff_id: str,
    db = Depends(get_db),
    current_user = Depends(get_current_user)
):
    # Chỉ Admin
    if current_user["role"] != "admin":
        raise HTTPException(
            status_code=403,
            detail="Chỉ Admin mới có quyền vô hiệu hóa tài khoản"
        )

    user = await db.users.find_one({"_id": ObjectId(staff_id)})

    if not user:
        raise HTTPException(
            status_code=404,
            detail="Không tìm thấy tài khoản"
        )

    # Không khóa admin
    if user["role"] == "admin":
        raise HTTPException(
            status_code=403,
            detail="Không thể khóa tài khoản Admin"
        )

    await db.users.update_one(
        {"_id": ObjectId(staff_id)},
        {
            "$set": {
                "is_active": False
            }
        }
    )

    return {
        "status": "success",
        "message": "Tài khoản đã bị vô hiệu hóa"
    }

@router.put("/staff/{staff_id}/enable")
async def enable_staff(
    staff_id: str,
    db = Depends(get_db),
    current_user = Depends(get_current_user)
):
    # Chỉ Admin
    if current_user["role"] != "admin":
        raise HTTPException(
            status_code=403,
            detail="Chỉ Admin mới có quyền kích hoạt tài khoản"
        )

    user = await db.users.find_one({"_id": ObjectId(staff_id)})

    if not user:
        raise HTTPException(
            status_code=404,
            detail="Không tìm thấy tài khoản"
        )

    await db.users.update_one(
        {"_id": ObjectId(staff_id)},
        {
            "$set": {
                "is_active": True
            }
        }
    )

    return {
        "status": "success",
        "message": "Đã kích hoạt lại tài khoản"
    }

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
    
# =========================
# QUẢN LÝ XẾP LỊCH HỌC
# =========================

from .models import ClassScheduleModel

# 1. TẠO LỊCH HỌC
@router.post("/schedule/create")
async def create_schedule(
    schedule: ClassScheduleModel,
    db = Depends(get_db),
    current_user = Depends(get_current_user)
):

    # Chỉ operator hoặc admin
    if current_user["role"] not in ["operator", "admin"]:
        raise HTTPException(
            status_code=403,
            detail="Bạn không có quyền tạo lịch"
        )

    # =========================
    # KIỂM TRA GIÁO VIÊN BỊ TRÙNG CA
    # =========================
    existing_schedule = await db.class_schedules.find_one({
        "teacher_id": schedule.teacher_id,
        "study_date": schedule.study_date,
        "start_time": schedule.start_time,
        "status": "active"
    })

    if existing_schedule:
        raise HTTPException(
            status_code=400,
            detail="Giáo viên đã có lịch ở khung giờ này"
        )

    schedule_dict = schedule.model_dump()

    result = await db.class_schedules.insert_one(schedule_dict)

    return {
        "status": "success",
        "message": "Tạo lịch học thành công",
        "schedule_id": str(result.inserted_id)
    }
# 2. LẤY DANH SÁCH LỊCH HỌC
@router.get("/schedule/list")
async def get_schedule_list(
    db = Depends(get_db),
    current_user = Depends(get_current_user)
):

    schedules = []

    cursor = db.class_schedules.find().sort("study_date", 1)

    async for doc in cursor:

        doc["id"] = str(doc["_id"])
        del doc["_id"]

        schedules.append(doc)

    return schedules
# 3. SỬA LỊCH HỌC
@router.put("/schedule/{schedule_id}")
async def update_schedule(
    schedule_id: str,
    payload: dict,
    db = Depends(get_db),
    current_user = Depends(get_current_user)
):

    if current_user["role"] not in ["operator", "admin"]:
        raise HTTPException(
            status_code=403,
            detail="Không có quyền"
        )

    await db.class_schedules.update_one(
        {"_id": ObjectId(schedule_id)},
        {
            "$set": payload
        }
    )

    return {
        "status": "success",
        "message": "Đã cập nhật lịch học"
    }
# 4. XÓA LỊCH HỌC
@router.delete("/schedule/{schedule_id}")
async def delete_schedule(
    schedule_id: str,
    db = Depends(get_db),
    current_user = Depends(get_current_user)
):

    if current_user["role"] not in ["operator", "admin"]:
        raise HTTPException(
            status_code=403,
            detail="Không có quyền"
        )

    await db.class_schedules.delete_one({
        "_id": ObjectId(schedule_id)
    })

    return {
        "status": "success",
        "message": "Đã xóa lịch học"
    }
# 5. LẤY DANH SÁCH GIÁO VIÊN
@router.get("/teachers")
async def get_teachers(
    db = Depends(get_db)
):

    teachers = await db.users.find(
        {
            "role": "teacher",
            "is_active": True
        },
        {
            "password": 0
        }
    ).to_list(length=100)

    for t in teachers:
        t["id"] = str(t["_id"])
        del t["_id"]

    return teachers

@router.post("/classes/create")
async def create_new_class(class_data: ClassModel, db = Depends(get_db)):
    """Nhân viên vận hành tạo lớp học mới"""
    doc = class_data.model_dump()
    result = await db.classes.insert_one(doc)
    return {"id": str(result.inserted_id), "message": "Tạo lớp thành công"}

@router.post("/classes/register")
async def register_student_to_class(payload: dict, db = Depends(get_db)):
    """Phụ huynh chọn lớp cho con - Tự động thêm vào danh sách"""
    class_id = payload.get("class_id")
    student_id = payload.get("student_id")
    
    # Thực hiện $push ID học sinh vào mảng student_ids của lớp
    result = await db.classes.update_one(
        {"_id": ObjectId(class_id)},
        {"$push": {"student_ids": student_id}}
    )
    if result.modified_count:
        return {"status": "success", "message": "Đăng ký lớp thành công"}
    raise HTTPException(status_code=400, detail="Không thể đăng ký")

# Lấy tất cả lớp học (Dành cho Nhân viên Vận hành)
@router.get("/classes")
async def get_all_classes(db = Depends(get_db)):
    classes = await db.classes.find({}).to_list(100)
    # Chuyển ObjectId thành chuỗi để Frontend đọc được
    for c in classes:
        c["id"] = str(c["_id"])
        del c["_id"]
    return classes

# Lấy các lớp đang mở (Dành cho trang Chọn lớp của Phụ huynh)
@router.get("/classes/public")
async def get_public_classes(db = Depends(get_db)):
    classes = await db.classes.find({"is_public": True, "status": "active"}).to_list(100)
    for c in classes:
        c["id"] = str(c["_id"])
        del c["_id"]
    return classes

@router.put("/classes/{class_id}")
async def update_class_info(class_id: str, payload: dict, db = Depends(get_db)):
    # Loại bỏ id khỏi payload nếu có để tránh lỗi MongoDB
    payload.pop("id", None)
    payload.pop("_id", None)
    
    result = await db.classes.update_one(
        {"_id": ObjectId(class_id)},
        {"$set": payload}
    )
    if result.matched_count:
        return {"status": "success", "message": "Cập nhật lớp học thành công"}
    raise HTTPException(status_code=400, detail="Không tìm thấy lớp học")

# API Xóa lớp học
@router.delete("/classes/{class_id}")
async def delete_class_info(class_id: str, db = Depends(get_db)):
    result = await db.classes.delete_one({"_id": ObjectId(class_id)})
    if result.deleted_count:
        return {"status": "success", "message": "Đã xóa lớp học"}
    raise HTTPException(status_code=400, detail="Không thể xóa lớp học")

# API Lấy danh sách học viên thật của một lớp
@router.get("/classes/{class_id}/students/details")
async def get_class_students_details(class_id: str, db = Depends(get_db)):
    # 1. Tìm lớp học
    class_data = await db.classes.find_one({"_id": ObjectId(class_id)})
    if not class_data:
        raise HTTPException(status_code=404, detail="Lớp học không tồn tại")
    
    student_ids = class_data.get("student_ids", [])
    if not student_ids:
        return []
        
    valid_ids = [ObjectId(sid) for sid in student_ids if ObjectId.is_valid(sid)]

    # 2. Lấy thông tin các học sinh từ bảng users
    students = await db.users.find({"_id": {"$in": valid_ids}}).to_list(100)
    
    result = []
    for stu in students:
        stu_id_str = str(stu["_id"])
        
        # 3. QUAN TRỌNG: Tìm Phụ huynh quản lý bé này thông qua mảng student_ids_ref
        parent = await db.users.find_one({"student_ids_ref": stu_id_str})
        
        parent_name = parent.get("name", "Chưa cập nhật") if parent else "Chưa cập nhật"
        parent_phone = parent.get("phone", "Chưa cập nhật") if parent else "Chưa cập nhật"

        result.append({
            "Mã HS": stu_id_str,
            "Tên Học Sinh": stu.get("name", "Chưa cập nhật"),
            "Tên Phụ Huynh": parent_name,
            "SĐT Liên Hệ": parent_phone, # Đã lấy đúng SĐT của Phụ Huynh
            "Tình trạng": "Đang học"
        })
    return result

# API Xóa học sinh khỏi lớp học
@router.delete("/classes/{class_id}/students/{student_id}")
async def remove_student_from_class(class_id: str, student_id: str, db = Depends(get_db)):
    # Sử dụng $pull để lấy student_id ra khỏi mảng
    result = await db.classes.update_one(
        {"_id": ObjectId(class_id)},
        {"$pull": {"student_ids": student_id}}
    )
    if result.modified_count:
        return {"status": "success", "message": "Đã xóa học sinh khỏi lớp"}
    raise HTTPException(status_code=400, detail="Không thể xóa hoặc học sinh không có trong lớp")

# Giả sử sau khi db.class_schedules.update_one thành công:
async def notify_schedule_change(db, class_id, class_name, old_time, new_time):
    # 1. Tìm tất cả học sinh trong lớp này
    course = await db.classes.find_one({"_id": ObjectId(class_id)})
    student_ids = course.get("student_ids", [])

    for s_id in student_ids:
        # 2. Gửi cho Học sinh
        await create_notification(db, {
            "sender_id": "system_operator",
            "sender_role": "operator",
            "sender_name": "Bộ phận Vận hành",
            "receiver_id": s_id,
            "receiver_role": "student",
            "type": "schedule",
            "title": "📅 Thay đổi lịch học!",
            "content": f"Lớp {class_name} đã đổi lịch từ {old_time} sang {new_time}. Nhớ đi học đúng giờ nhé!"
        })

        # 3. Gửi cho Phụ huynh (Tìm phụ huynh của bé này)
        parent = await db.users.find_one({"student_ids_ref": s_id})
        if parent:
            await create_notification(db, {
                "sender_id": "system_operator",
                "sender_role": "operator",
                "sender_name": "Bộ phận Vận hành",
                "receiver_id": str(parent["_id"]),
                "receiver_role": "parent",
                "type": "schedule",
                "title": "🔔 Thông báo đổi lịch học của con",
                "content": f"Kính thưa phụ huynh, lớp {class_name} của bé đã được điều chỉnh lịch học mới. Vui lòng kiểm tra ứng dụng."
            })