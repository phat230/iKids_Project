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


# =========================================================
# HELPER
# =========================================================

def to_object_id(raw_id: str, field_name: str = "ID") -> ObjectId:
    try:
        return ObjectId(str(raw_id))
    except Exception:
        raise HTTPException(status_code=400, detail=f"{field_name} không hợp lệ")


def model_to_dict(model):
    if hasattr(model, "model_dump"):
        return model.model_dump()
    return model.dict()


def serialize_doc(doc: dict) -> dict:
    if not doc:
        return doc

    doc = dict(doc)

    if "_id" in doc:
        doc["id"] = str(doc["_id"])
        del doc["_id"]

    for key, value in list(doc.items()):
        if isinstance(value, ObjectId):
            doc[key] = str(value)
        elif isinstance(value, datetime):
            doc[key] = value.isoformat()

    return doc


def to_float(value, default: float = 0.0) -> float:
    try:
        if value is None or value == "":
            return default
        return float(value)
    except Exception:
        return default


def to_int(value, default: int = 0) -> int:
    try:
        if value is None or value == "":
            return default
        return int(value)
    except Exception:
        return default


def normalize_class_payload(payload: dict) -> dict:
    """
    Chuẩn hóa dữ liệu lớp học, đặc biệt là học phí.
    Dùng cho create/update class.
    """

    payload = dict(payload)

    payload.pop("id", None)
    payload.pop("_id", None)

    payload["class_name"] = str(payload.get("class_name", "")).strip()
    payload["subject"] = str(payload.get("subject", "")).strip() or "Chưa xác định"
    payload["teacher_id"] = str(payload.get("teacher_id", "")).strip()
    payload["teacher_name"] = str(payload.get("teacher_name", "")).strip()

    payload["description"] = payload.get("description") or ""
    payload["status"] = payload.get("status") or "active"
    payload["is_public"] = bool(payload.get("is_public", True))

    payload["tuition_enabled"] = bool(payload.get("tuition_enabled", True))
    payload["registration_fee"] = to_float(payload.get("registration_fee"), 0.0)
    payload["monthly_fee"] = to_float(payload.get("monthly_fee"), 0.0)
    payload["cycle_fee"] = to_float(payload.get("cycle_fee"), 0.0)
    payload["cycle_months"] = to_int(payload.get("cycle_months"), 3)
    payload["yearly_fee"] = to_float(payload.get("yearly_fee"), 0.0)

    payload["allow_registration_fee"] = bool(payload.get("allow_registration_fee", True))
    payload["allow_monthly_payment"] = bool(payload.get("allow_monthly_payment", True))
    payload["allow_cycle_payment"] = bool(payload.get("allow_cycle_payment", True))
    payload["allow_yearly_payment"] = bool(payload.get("allow_yearly_payment", True))

    payload["billing_day"] = to_int(payload.get("billing_day"), 5)
    payload["grace_days"] = to_int(payload.get("grace_days"), 3)

    if payload["cycle_months"] <= 0:
        payload["cycle_months"] = 3

    if payload["billing_day"] < 1:
        payload["billing_day"] = 1
    if payload["billing_day"] > 28:
        payload["billing_day"] = 28

    if payload["grace_days"] < 0:
        payload["grace_days"] = 0

    reminder_days_before = payload.get("reminder_days_before", [7, 3, 0, -1])
    if not isinstance(reminder_days_before, list):
        reminder_days_before = [7, 3, 0, -1]
    payload["reminder_days_before"] = reminder_days_before

    payload["currency"] = payload.get("currency") or "VND"
    payload["tuition_note"] = payload.get("tuition_note") or ""

    if "student_ids" not in payload or not isinstance(payload.get("student_ids"), list):
        payload["student_ids"] = []

    return payload


def ensure_admin_or_operator(current_user: dict):
    if current_user.get("role") not in ["operator", "admin"]:
        raise HTTPException(status_code=403, detail="Bạn không có quyền thực hiện thao tác này")


def ensure_admin(current_user: dict):
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Chỉ Admin mới có quyền")


# =========================================================
# 1. API TIẾP NHẬN ĐƠN TỪ GIÁO VIÊN
# =========================================================

@router.post("/requests/create")
async def submit_teacher_request(request_data: dict, db=Depends(get_db)):
    request_data["status"] = "pending"

    if "created_at" not in request_data:
        request_data["created_at"] = datetime.now().strftime("%d/%m/%Y %H:%M")

    request_data.pop("id", None)
    request_data.pop("_id", None)

    result = await db.teacher_requests.insert_one(request_data)

    return {
        "status": "success",
        "message": "Đã gửi đơn thành công",
        "id": str(result.inserted_id)
    }


@router.get("/pending-requests")
async def get_pending_requests(db=Depends(get_db)):
    cursor = db.teacher_requests.find({"status": "pending"}).sort("created_at", -1)
    requests_list = []

    async for doc in cursor:
        requests_list.append(serialize_doc(doc))

    return requests_list


@router.post("/approve/{request_id}")
async def approve_request(request_id: str, db=Depends(get_db)):
    req_id = to_object_id(request_id, "Request ID")

    res = await db.teacher_requests.update_one(
        {"_id": req_id},
        {
            "$set": {
                "status": "approved",
                "updated_at": datetime.now()
            }
        }
    )

    if res.modified_count:
        return {"status": "success", "message": "Đã phê duyệt đơn"}

    raise HTTPException(status_code=404, detail="Không tìm thấy đơn")


@router.get("/request-history")
async def get_request_history(db=Depends(get_db)):
    cursor = db.teacher_requests.find({"status": {"$ne": "pending"}}).sort("updated_at", -1)
    history_list = []

    async for doc in cursor:
        history_list.append(serialize_doc(doc))

    return history_list


@router.post("/reject/{request_id}")
async def reject_request(request_id: str, db=Depends(get_db)):
    req_id = to_object_id(request_id, "Request ID")

    res = await db.teacher_requests.update_one(
        {"_id": req_id},
        {
            "$set": {
                "status": "rejected",
                "updated_at": datetime.now()
            }
        }
    )

    if res.modified_count:
        return {"status": "success", "message": "Đã từ chối đơn"}

    raise HTTPException(status_code=404, detail="Không tìm thấy đơn")


# =========================================================
# 2. QUẢN LÝ NHÂN SỰ & TÀI KHOẢN
# =========================================================

@router.get("/staff")
async def get_all_staff(
    db=Depends(get_db),
    current_user=Depends(get_current_user)
):
    ensure_admin(current_user)

    cursor = db.users.find().sort("name", 1)
    staff_list = []

    async for doc in cursor:
        doc = serialize_doc(doc)
        doc.pop("password", None)
        staff_list.append(doc)

    return staff_list


@router.post("/staff/add")
async def add_staff(
    staff_data: dict,
    db=Depends(get_db),
    current_user=Depends(get_current_user)
):
    ensure_admin(current_user)

    email = str(staff_data.get("email", "")).strip().lower()
    if not email:
        raise HTTPException(status_code=400, detail="Email không được trống")

    existing_user = await db.users.find_one({"email": email})
    if existing_user:
        raise HTTPException(status_code=400, detail="Email này đã được cấp tài khoản!")

    staff_data["email"] = email

    if "password" in staff_data and staff_data["password"]:
        staff_data["password"] = pwd_context.hash(staff_data["password"])

    staff_data["created_at"] = datetime.now()
    staff_data["is_active"] = staff_data.get("is_active", True)

    result = await db.users.insert_one(staff_data)

    return {
        "status": "success",
        "id": str(result.inserted_id)
    }


@router.delete("/staff/{staff_id}")
async def delete_staff(
    staff_id: str,
    db=Depends(get_db),
    current_user=Depends(get_current_user)
):
    ensure_admin(current_user)

    user = await db.users.find_one({"_id": to_object_id(staff_id, "Staff ID")})

    if not user:
        raise HTTPException(status_code=404, detail="Không tìm thấy tài khoản")

    if user.get("role") == "admin":
        raise HTTPException(status_code=403, detail="Không thể xóa tài khoản Admin")

    await db.users.delete_one({"_id": user["_id"]})

    return {
        "status": "success",
        "message": "Đã xóa tài khoản thành công"
    }


@router.put("/staff/{staff_id}/disable")
async def disable_staff(
    staff_id: str,
    db=Depends(get_db),
    current_user=Depends(get_current_user)
):
    ensure_admin(current_user)

    user = await db.users.find_one({"_id": to_object_id(staff_id, "Staff ID")})

    if not user:
        raise HTTPException(status_code=404, detail="Không tìm thấy tài khoản")

    if user.get("role") == "admin":
        raise HTTPException(status_code=403, detail="Không thể khóa tài khoản Admin")

    await db.users.update_one(
        {"_id": user["_id"]},
        {"$set": {"is_active": False}}
    )

    return {
        "status": "success",
        "message": "Tài khoản đã bị vô hiệu hóa"
    }


@router.put("/staff/{staff_id}/enable")
async def enable_staff(
    staff_id: str,
    db=Depends(get_db),
    current_user=Depends(get_current_user)
):
    ensure_admin(current_user)

    user = await db.users.find_one({"_id": to_object_id(staff_id, "Staff ID")})

    if not user:
        raise HTTPException(status_code=404, detail="Không tìm thấy tài khoản")

    await db.users.update_one(
        {"_id": user["_id"]},
        {"$set": {"is_active": True}}
    )

    return {
        "status": "success",
        "message": "Đã kích hoạt lại tài khoản"
    }


@router.put("/staff/{staff_id}")
async def update_staff(
    staff_id: str,
    staff_data: dict,
    db=Depends(get_db),
    current_user=Depends(get_current_user)
):
    ensure_admin(current_user)

    allowed_fields = [
        "name",
        "role",
        "email",
        "phone",
        "phone_number",
        "status",
        "is_active",
        "subjects",
    ]

    update_data = {
        k: v for k, v in staff_data.items()
        if k in allowed_fields
    }

    if "email" in update_data:
        update_data["email"] = str(update_data["email"]).strip().lower()

    update_data["updated_at"] = datetime.now()

    res = await db.users.update_one(
        {"_id": to_object_id(staff_id, "Staff ID")},
        {"$set": update_data}
    )

    if res.matched_count:
        return {"status": "success"}

    raise HTTPException(status_code=404, detail="Không tìm thấy tài khoản")


@router.put("/staff/{staff_id}/password")
async def reset_password(
    staff_id: str,
    pwd_data: dict,
    db=Depends(get_db),
    current_user=Depends(get_current_user)
):
    ensure_admin(current_user)

    new_pwd = pwd_data.get("password")

    if not new_pwd:
        raise HTTPException(status_code=400, detail="Mật khẩu rỗng")

    hashed_password = pwd_context.hash(new_pwd)

    res = await db.users.update_one(
        {"_id": to_object_id(staff_id, "Staff ID")},
        {"$set": {"password": hashed_password}}
    )

    if res.matched_count:
        return {"status": "success"}

    raise HTTPException(status_code=404, detail="Không tìm thấy tài khoản")


# =========================================================
# 3. QUẢN LÝ XẾP LỊCH HỌC
# =========================================================

@router.post("/schedule/create")
async def create_schedule(
    schedule: ClassScheduleModel,
    db=Depends(get_db),
    current_user=Depends(get_current_user)
):
    ensure_admin_or_operator(current_user)

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

    schedule_dict = model_to_dict(schedule)
    schedule_dict["created_at"] = schedule_dict.get("created_at") or datetime.now()

    result = await db.class_schedules.insert_one(schedule_dict)

    return {
        "status": "success",
        "message": "Tạo lịch học thành công",
        "schedule_id": str(result.inserted_id)
    }


@router.get("/schedule/list")
async def get_schedule_list(
    db=Depends(get_db),
    current_user=Depends(get_current_user)
):
    schedules = []
    cursor = db.class_schedules.find().sort("study_date", 1)

    async for doc in cursor:
        schedules.append(serialize_doc(doc))

    return schedules


@router.put("/schedule/{schedule_id}")
async def update_schedule(
    schedule_id: str,
    payload: dict,
    db=Depends(get_db),
    current_user=Depends(get_current_user)
):
    ensure_admin_or_operator(current_user)

    schedule_obj_id = to_object_id(schedule_id, "Schedule ID")
    payload.pop("id", None)
    payload.pop("_id", None)

    old_schedule = await db.class_schedules.find_one({"_id": schedule_obj_id})

    res = await db.class_schedules.update_one(
        {"_id": schedule_obj_id},
        {
            "$set": {
                **payload,
                "updated_at": datetime.now()
            }
        }
    )

    if res.matched_count == 0:
        raise HTTPException(status_code=404, detail="Không tìm thấy lịch học")

    if old_schedule:
        old_time = f"{old_schedule.get('study_date', '')} {old_schedule.get('start_time', '')}-{old_schedule.get('end_time', '')}"
        new_time = f"{payload.get('study_date', old_schedule.get('study_date', ''))} {payload.get('start_time', old_schedule.get('start_time', ''))}-{payload.get('end_time', old_schedule.get('end_time', ''))}"

        if old_time != new_time:
            try:
                await notify_schedule_change(
                    db=db,
                    class_id=old_schedule.get("class_id"),
                    class_name=old_schedule.get("class_name"),
                    old_time=old_time,
                    new_time=new_time
                )
            except Exception as e:
                print(f"Không gửi được thông báo đổi lịch: {e}")

    return {
        "status": "success",
        "message": "Đã cập nhật lịch học"
    }


@router.delete("/schedule/{schedule_id}")
async def delete_schedule(
    schedule_id: str,
    db=Depends(get_db),
    current_user=Depends(get_current_user)
):
    ensure_admin_or_operator(current_user)

    result = await db.class_schedules.delete_one({
        "_id": to_object_id(schedule_id, "Schedule ID")
    })

    if result.deleted_count:
        return {
            "status": "success",
            "message": "Đã xóa lịch học"
        }

    raise HTTPException(status_code=404, detail="Không tìm thấy lịch học")


@router.get("/teachers")
async def get_teachers(db=Depends(get_db)):
    teachers = await db.users.find(
        {
            "role": "teacher",
            "is_active": {"$ne": False},
            "status": {
                "$nin": [
                    "Nghỉ việc",
                    "Đã nghỉ việc",
                    "Vô hiệu hóa",
                    "Nghi viec",
                    "Vo hieu hoa",
                ]
            }
        },
        {"password": 0}
    ).to_list(length=200)

    return [serialize_doc(t) for t in teachers]


# =========================================================
# 4. QUẢN LÝ LỚP HỌC + HỌC PHÍ
# =========================================================

@router.post("/classes/create")
async def create_new_class(
    class_data: ClassModel,
    db=Depends(get_db),
    current_user=Depends(get_current_user)
):
    """
    Admin/operator tạo lớp học mới.
    Đã hỗ trợ học phí:
    - registration_fee
    - monthly_fee
    - cycle_fee
    - yearly_fee
    - billing_day
    """

    ensure_admin_or_operator(current_user)

    doc = model_to_dict(class_data)
    doc = normalize_class_payload(doc)

    if not doc.get("class_name") or not doc.get("teacher_id"):
        raise HTTPException(
            status_code=400,
            detail="Tên lớp và giáo viên phụ trách không được trống"
        )

    doc["created_at"] = datetime.now()
    doc["updated_at"] = datetime.now()
    doc["created_by"] = str(current_user.get("user_id", ""))

    result = await db.classes.insert_one(doc)

    return {
        "status": "success",
        "id": str(result.inserted_id),
        "message": "Tạo lớp thành công"
    }


@router.post("/classes/register")
async def register_student_to_class(payload: dict, db=Depends(get_db)):
    """
    API cũ: phụ huynh chọn lớp cho con.
    Lưu ý: API học phí mới nên dùng /api/tuition/enrollments.
    Route này giữ lại để không làm hỏng frontend/mobile cũ.
    """

    class_id = payload.get("class_id")
    student_id = payload.get("student_id")

    if not class_id or not student_id:
        raise HTTPException(status_code=400, detail="Thiếu class_id hoặc student_id")

    class_obj_id = to_object_id(class_id, "Class ID")

    result = await db.classes.update_one(
        {"_id": class_obj_id},
        {
            "$addToSet": {
                "student_ids": str(student_id)
            },
            "$set": {
                "updated_at": datetime.now()
            }
        }
    )

    if result.matched_count:
        return {
            "status": "success",
            "message": "Đăng ký lớp thành công"
        }

    raise HTTPException(status_code=404, detail="Không tìm thấy lớp học")


@router.get("/classes")
async def get_all_classes(db=Depends(get_db)):
    classes = await db.classes.find({}).sort("created_at", -1).to_list(300)
    return [serialize_doc(c) for c in classes]


@router.get("/classes/public")
async def get_public_classes(db=Depends(get_db)):
    classes = await db.classes.find({
        "is_public": True,
        "status": "active"
    }).sort("created_at", -1).to_list(300)

    return [serialize_doc(c) for c in classes]


@router.get("/classes/{class_id}")
async def get_class_detail(class_id: str, db=Depends(get_db)):
    class_data = await db.classes.find_one({"_id": to_object_id(class_id, "Class ID")})

    if not class_data:
        raise HTTPException(status_code=404, detail="Không tìm thấy lớp học")

    return serialize_doc(class_data)


@router.put("/classes/{class_id}")
async def update_class_info(
    class_id: str,
    payload: dict,
    db=Depends(get_db),
    current_user=Depends(get_current_user)
):
    ensure_admin_or_operator(current_user)

    class_obj_id = to_object_id(class_id, "Class ID")
    payload = normalize_class_payload(payload)
    payload["updated_at"] = datetime.now()

    result = await db.classes.update_one(
        {"_id": class_obj_id},
        {"$set": payload}
    )

    if result.matched_count:
        return {
            "status": "success",
            "message": "Cập nhật lớp học thành công"
        }

    raise HTTPException(status_code=404, detail="Không tìm thấy lớp học")


@router.delete("/classes/{class_id}")
async def delete_class_info(
    class_id: str,
    db=Depends(get_db),
    current_user=Depends(get_current_user)
):
    ensure_admin_or_operator(current_user)

    class_obj_id = to_object_id(class_id, "Class ID")

    result = await db.classes.delete_one({"_id": class_obj_id})

    if result.deleted_count:
        await db.class_schedules.delete_many({"class_id": str(class_id)})

        return {
            "status": "success",
            "message": "Đã xóa lớp học"
        }

    raise HTTPException(status_code=404, detail="Không thể xóa lớp học")


@router.get("/classes/{class_id}/students/details")
async def get_class_students_details(class_id: str, db=Depends(get_db)):
    class_data = await db.classes.find_one({"_id": to_object_id(class_id, "Class ID")})

    if not class_data:
        raise HTTPException(status_code=404, detail="Lớp học không tồn tại")

    student_ids = class_data.get("student_ids", [])

    if not student_ids:
        return []

    valid_ids = []

    for sid in student_ids:
        if ObjectId.is_valid(str(sid)):
            valid_ids.append(ObjectId(str(sid)))

    if not valid_ids:
        return []

    students = await db.users.find(
        {"_id": {"$in": valid_ids}},
        {"password": 0}
    ).to_list(200)

    result = []

    for stu in students:
        stu_id_str = str(stu["_id"])

        parent = await db.users.find_one(
            {"student_ids_ref": stu_id_str},
            {"password": 0}
        )

        parent_name = parent.get("name", "Chưa cập nhật") if parent else "Chưa cập nhật"
        parent_phone = (
            parent.get("phone")
            or parent.get("phone_number")
            or "Chưa cập nhật"
        ) if parent else "Chưa cập nhật"

        result.append({
            "Mã HS": stu_id_str,
            "Tên Học Sinh": stu.get("name", stu.get("full_name", "Chưa cập nhật")),
            "Tên Phụ Huynh": parent_name,
            "SĐT Liên Hệ": parent_phone,
            "Tình trạng": "Đang học"
        })

    return result


@router.delete("/classes/{class_id}/students/{student_id}")
async def remove_student_from_class(
    class_id: str,
    student_id: str,
    db=Depends(get_db),
    current_user=Depends(get_current_user)
):
    ensure_admin_or_operator(current_user)

    result = await db.classes.update_one(
        {"_id": to_object_id(class_id, "Class ID")},
        {
            "$pull": {
                "student_ids": str(student_id)
            },
            "$set": {
                "updated_at": datetime.now()
            }
        }
    )

    if result.modified_count:
        return {
            "status": "success",
            "message": "Đã xóa học sinh khỏi lớp"
        }

    raise HTTPException(
        status_code=400,
        detail="Không thể xóa hoặc học sinh không có trong lớp"
    )


# =========================================================
# 5. THÔNG BÁO ĐỔI LỊCH
# =========================================================

async def notify_schedule_change(db, class_id, class_name, old_time, new_time):
    if not class_id:
        return

    course = await db.classes.find_one({"_id": to_object_id(class_id, "Class ID")})

    if not course:
        return

    student_ids = course.get("student_ids", [])

    for s_id in student_ids:
        await create_notification(db, {
            "sender_id": "system_operator",
            "sender_role": "operator",
            "sender_name": "Bộ phận Vận hành",
            "receiver_id": str(s_id),
            "receiver_role": "student",
            "type": "schedule",
            "title": "📅 Thay đổi lịch học!",
            "content": f"Lớp {class_name} đã đổi lịch từ {old_time} sang {new_time}. Nhớ đi học đúng giờ nhé!"
        })

        parent = await db.users.find_one({"student_ids_ref": str(s_id)})

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