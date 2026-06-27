# Backend/modules/tuition/services.py

from datetime import datetime, date, timedelta
from typing import Optional, Dict, Any, List

from bson import ObjectId
from fastapi import HTTPException


# =========================================================
# HELPER CƠ BẢN
# =========================================================

def to_object_id(raw_id: str, field_name: str = "ID") -> ObjectId:
    try:
        return ObjectId(str(raw_id))
    except Exception:
        raise HTTPException(
            status_code=400,
            detail=f"{field_name} không hợp lệ."
        )


def to_float(value, default: float = 0.0) -> float:
    try:
        if value is None or value == "":
            return default
        return float(value)
    except Exception:
        return default


def today_date() -> date:
    return datetime.now().date()


def parse_date(value: Optional[str]) -> date:
    if not value:
        return today_date()

    value = str(value).strip()

    try:
        return datetime.fromisoformat(value).date()
    except Exception:
        pass

    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except Exception:
        return today_date()


def format_date(value: date) -> str:
    return value.strftime("%Y-%m-%d")


def add_months(source_date: date, months: int) -> date:
    month = source_date.month - 1 + months
    year = source_date.year + month // 12
    month = month % 12 + 1

    days_in_month = [
        31,
        29 if year % 4 == 0 and (year % 100 != 0 or year % 400 == 0) else 28,
        31,
        30,
        31,
        30,
        31,
        31,
        30,
        31,
        30,
        31,
    ]

    day = min(source_date.day, days_in_month[month - 1])
    return date(year, month, day)


def set_billing_day(base_date: date, billing_day: int) -> date:
    safe_day = max(1, min(int(billing_day or 5), 28))
    return date(base_date.year, base_date.month, safe_day)


def serialize_doc(doc: Optional[dict]) -> Optional[dict]:
    if not doc:
        return doc

    result = dict(doc)

    if "_id" in result:
        result["id"] = str(result["_id"])
        del result["_id"]

    for key, value in list(result.items()):
        if isinstance(value, ObjectId):
            result[key] = str(value)
        elif isinstance(value, datetime):
            result[key] = value.isoformat()

    return result


def serialize_many(docs: List[dict]) -> List[dict]:
    return [serialize_doc(doc) for doc in docs]


async def find_doc_by_id(collection, raw_id: str) -> Optional[dict]:
    if not raw_id:
        return None

    try:
        doc = await collection.find_one({"_id": ObjectId(str(raw_id))})
        if doc:
            return doc
    except Exception:
        pass

    return await collection.find_one({"id": str(raw_id)})


async def create_notification(
    db,
    receiver_id: str,
    receiver_role: str,
    title: str,
    message: str,
    notification_type: str = "tuition",
    extra_data: Optional[dict] = None,
):
    try:
        result = await db.notifications.insert_one({
            "receiver_id": str(receiver_id),
            "receiver_role": receiver_role,
            "title": title,
            "message": message,
            "type": notification_type,
            "extra_data": extra_data or {},
            "is_read": False,
            "created_at": datetime.now()
        })

        return str(result.inserted_id)

    except Exception as e:
        print(f"⚠️ Không tạo được notification học phí: {e}")
        return None


# =========================================================
# HELPER USER / CLASS
# =========================================================

async def get_user_or_404(db, user_id: str, label: str = "Người dùng") -> dict:
    user = await db.users.find_one({"_id": to_object_id(user_id, f"{label} ID")})

    if not user:
        raise HTTPException(status_code=404, detail=f"Không tìm thấy {label.lower()}.")

    return user


async def get_class_or_404(db, class_id: str) -> dict:
    class_doc = await find_doc_by_id(db.classes, class_id)

    if not class_doc:
        raise HTTPException(status_code=404, detail="Không tìm thấy lớp học.")

    return class_doc


async def ensure_parent_owns_child(db, parent_id: str, student_id: str) -> bool:
    parent = await get_user_or_404(db, parent_id, "Phụ huynh")

    student_ids_ref = parent.get("student_ids_ref") or []
    student_ids_ref = [str(sid) for sid in student_ids_ref]

    return str(student_id) in student_ids_ref


def get_student_display_name(student: dict) -> str:
    return (
        student.get("full_name")
        or student.get("name")
        or "Học sinh"
    )


def get_class_display_name(class_doc: dict) -> str:
    return (
        class_doc.get("class_name")
        or class_doc.get("name")
        or "Lớp học"
    )


# =========================================================
# TÍNH TIỀN / KỲ HỌC PHÍ
# =========================================================

def get_plan_config(class_doc: dict, billing_plan: str) -> dict:
    monthly_fee = to_float(class_doc.get("monthly_fee"), 0.0)
    cycle_months = int(class_doc.get("cycle_months") or 3)

    if billing_plan == "monthly":
        amount = monthly_fee
        months = 1
        invoice_type = "monthly"

    elif billing_plan == "cycle":
        amount = to_float(class_doc.get("cycle_fee"), 0.0)
        if amount <= 0:
            amount = monthly_fee * cycle_months

        months = cycle_months
        invoice_type = "cycle"

    elif billing_plan == "yearly":
        amount = to_float(class_doc.get("yearly_fee"), 0.0)
        if amount <= 0:
            amount = monthly_fee * 12

        months = 12
        invoice_type = "yearly"

    else:
        raise HTTPException(status_code=400, detail="Gói học phí không hợp lệ.")

    return {
        "amount": amount,
        "months": months,
        "invoice_type": invoice_type
    }


def build_period_label(invoice_type: str, start_date: date, end_date: date) -> str:
    if invoice_type == "registration":
        return f"Phí đăng ký {start_date.strftime('%m/%Y')}"

    if invoice_type == "monthly":
        return f"Tháng {start_date.strftime('%m/%Y')}"

    if invoice_type == "cycle":
        return (
            f"Chu kỳ {start_date.strftime('%m/%Y')} - "
            f"{end_date.strftime('%m/%Y')}"
        )

    if invoice_type == "yearly":
        return f"Năm học {start_date.year}"

    return f"Học phí {start_date.strftime('%m/%Y')}"


async def create_invoice_doc(
    db,
    enrollment: dict,
    invoice_type: str,
    amount: float,
    period_start: date,
    period_end: date,
    due_date: date,
    note: Optional[str] = None,
) -> Optional[dict]:
    if amount <= 0:
        return None

    period_label = build_period_label(invoice_type, period_start, period_end)

    invoice_doc = {
        "enrollment_id": str(enrollment["_id"]),
        "parent_id": str(enrollment["parent_id"]),
        "student_id": str(enrollment["student_id"]),
        "student_name": enrollment.get("student_name"),
        "class_id": str(enrollment["class_id"]),
        "class_name": enrollment.get("class_name"),
        "invoice_type": invoice_type,
        "period_label": period_label,
        "period_start": format_date(period_start),
        "period_end": format_date(period_end),
        "amount": amount,
        "currency": enrollment.get("currency", "VND"),
        "due_date": format_date(due_date),
        "status": "pending",
        "paid_at": None,
        "payment_id": None,
        "reminder_count": 0,
        "last_reminded_at": None,
        "note": note,
        "created_at": datetime.now(),
        "updated_at": datetime.now(),
    }

    result = await db.tuition_invoices.insert_one(invoice_doc)
    invoice_doc["_id"] = result.inserted_id

    return invoice_doc


# =========================================================
# PUBLIC CLASSES
# =========================================================

async def list_public_classes_service(db):
    cursor = db.classes.find({
        "status": {"$ne": "closed"},
        "is_public": {"$ne": False}
    }).sort("created_at", -1)

    items = []

    async for doc in cursor:
        items.append(serialize_doc(doc))

    return items


async def get_class_tuition_detail_service(db, class_id: str):
    class_doc = await get_class_or_404(db, class_id)
    return serialize_doc(class_doc)


# =========================================================
# ĐĂNG KÝ LỚP + TẠO HÓA ĐƠN
# =========================================================

async def create_enrollment_service(db, payload):
    parent_id = payload.parent_id
    student_id = payload.student_id
    class_id = payload.class_id
    billing_plan = payload.billing_plan
    start = parse_date(payload.start_date)

    is_owner = await ensure_parent_owns_child(db, parent_id, student_id)

    if not is_owner:
        raise HTTPException(
            status_code=403,
            detail="Phụ huynh không có quyền đăng ký lớp cho học sinh này."
        )

    parent = await get_user_or_404(db, parent_id, "Phụ huynh")
    student = await get_user_or_404(db, student_id, "Học sinh")
    class_doc = await get_class_or_404(db, class_id)

    if class_doc.get("status") == "closed":
        raise HTTPException(status_code=400, detail="Lớp học này đã đóng.")

    if class_doc.get("is_public") is False:
        raise HTTPException(status_code=400, detail="Lớp học này chưa mở đăng ký.")

    duplicate = await db.tuition_enrollments.find_one({
        "student_id": str(student_id),
        "class_id": str(class_id),
        "status": "active"
    })

    if duplicate:
        raise HTTPException(
            status_code=400,
            detail="Học sinh đã đăng ký lớp này rồi."
        )

    plan_config = get_plan_config(class_doc, billing_plan)

    if plan_config["amount"] <= 0:
        raise HTTPException(
            status_code=400,
            detail="Lớp học chưa cấu hình học phí cho gói này."
        )

    class_name = get_class_display_name(class_doc)
    student_name = get_student_display_name(student)

    billing_day = int(class_doc.get("billing_day") or 5)
    next_base_date = add_months(start, plan_config["months"])
    next_due_date = set_billing_day(next_base_date, billing_day)

    enrollment_doc = {
        "parent_id": str(parent["_id"]),
        "student_id": str(student["_id"]),
        "student_name": student_name,
        "class_id": str(class_doc.get("_id", class_id)),
        "class_name": class_name,
        "subject": class_doc.get("subject"),
        "teacher_id": class_doc.get("teacher_id"),
        "teacher_name": class_doc.get("teacher_name"),
        "billing_plan": billing_plan,
        "start_date": format_date(start),
        "next_due_date": format_date(next_due_date),
        "registration_fee": to_float(class_doc.get("registration_fee"), 0.0),
        "monthly_fee": to_float(class_doc.get("monthly_fee"), 0.0),
        "cycle_fee": to_float(class_doc.get("cycle_fee"), 0.0),
        "cycle_months": int(class_doc.get("cycle_months") or 3),
        "yearly_fee": to_float(class_doc.get("yearly_fee"), 0.0),
        "billing_day": billing_day,
        "currency": class_doc.get("currency", "VND"),
        "auto_create_next_invoice": True,
        "status": "active",
        "created_at": datetime.now(),
        "updated_at": datetime.now(),
    }

    result = await db.tuition_enrollments.insert_one(enrollment_doc)
    enrollment_doc["_id"] = result.inserted_id

    # Thêm học sinh vào lớp để phục vụ điểm danh/quản lý.
    try:
        await db.classes.update_one(
            {"_id": class_doc["_id"]},
            {"$addToSet": {"student_ids": str(student["_id"])}}
        )
    except Exception as e:
        print(f"⚠️ Không cập nhật student_ids vào class: {e}")

    created_invoices = []

    registration_fee = to_float(enrollment_doc.get("registration_fee"), 0.0)

    if registration_fee > 0:
        reg_invoice = await create_invoice_doc(
            db=db,
            enrollment=enrollment_doc,
            invoice_type="registration",
            amount=registration_fee,
            period_start=start,
            period_end=start,
            due_date=start,
            note="Phí đăng ký lớp học"
        )

        if reg_invoice:
            created_invoices.append(reg_invoice)

    first_period_end = add_months(start, plan_config["months"]) - timedelta(days=1)

    first_invoice = await create_invoice_doc(
        db=db,
        enrollment=enrollment_doc,
        invoice_type=plan_config["invoice_type"],
        amount=plan_config["amount"],
        period_start=start,
        period_end=first_period_end,
        due_date=start,
        note="Học phí kỳ đầu"
    )

    if first_invoice:
        created_invoices.append(first_invoice)

    paid_results = []
    payment_errors = []

    if payload.pay_registration_now:
        for inv in created_invoices:
            if inv.get("invoice_type") == "registration":
                try:
                    paid_results.append(
                        await pay_invoice_service(
                            db,
                            invoice_id=str(inv["_id"]),
                            parent_id=parent_id
                        )
                    )
                except Exception as e:
                    payment_errors.append(str(e))

    if payload.pay_first_invoice_now:
        for inv in created_invoices:
            if inv.get("invoice_type") != "registration":
                try:
                    paid_results.append(
                        await pay_invoice_service(
                            db,
                            invoice_id=str(inv["_id"]),
                            parent_id=parent_id
                        )
                    )
                except Exception as e:
                    payment_errors.append(str(e))

    await create_notification(
        db=db,
        receiver_id=str(parent["_id"]),
        receiver_role="parent",
        title="Đăng ký lớp thành công",
        message=(
            f"Bạn đã đăng ký lớp {class_name} cho bé {student_name}. "
            f"Vui lòng kiểm tra hóa đơn học phí."
        ),
        notification_type="tuition_enrollment",
        extra_data={
            "enrollment_id": str(enrollment_doc["_id"]),
            "class_id": str(class_doc.get("_id", class_id)),
            "student_id": str(student["_id"]),
        }
    )

    return {
        "status": "success",
        "message": "Đăng ký lớp thành công.",
        "enrollment": serialize_doc(enrollment_doc),
        "invoices": serialize_many(created_invoices),
        "paid_results": paid_results,
        "payment_errors": payment_errors,
    }


async def list_parent_enrollments_service(db, parent_id: str):
    cursor = db.tuition_enrollments.find({
        "parent_id": str(parent_id)
    }).sort("created_at", -1)

    items = []

    async for doc in cursor:
        items.append(serialize_doc(doc))

    return items


async def list_student_enrollments_service(db, student_id: str):
    cursor = db.tuition_enrollments.find({
        "student_id": str(student_id)
    }).sort("created_at", -1)

    items = []

    async for doc in cursor:
        items.append(serialize_doc(doc))

    return items


# =========================================================
# HÓA ĐƠN
# =========================================================

async def get_invoice_service(db, invoice_id: str):
    invoice = await db.tuition_invoices.find_one({
        "_id": to_object_id(invoice_id, "Invoice ID")
    })

    if not invoice:
        raise HTTPException(status_code=404, detail="Không tìm thấy hóa đơn.")

    return serialize_doc(invoice)


async def list_invoices_service(
    db,
    parent_id: Optional[str] = None,
    student_id: Optional[str] = None,
    class_id: Optional[str] = None,
    status: Optional[str] = None,
):
    query = {}

    if parent_id:
        query["parent_id"] = str(parent_id)

    if student_id:
        query["student_id"] = str(student_id)

    if class_id:
        query["class_id"] = str(class_id)

    if status:
        query["status"] = str(status)

    cursor = db.tuition_invoices.find(query).sort("created_at", -1)

    items = []

    async for doc in cursor:
        items.append(serialize_doc(doc))

    return items


async def create_manual_invoice_service(db, payload):
    invoice_doc = {
        "enrollment_id": None,
        "parent_id": str(payload.parent_id),
        "student_id": str(payload.student_id),
        "student_name": payload.student_name,
        "class_id": str(payload.class_id),
        "class_name": payload.class_name,
        "invoice_type": payload.invoice_type,
        "period_label": payload.period_label,
        "period_start": payload.period_start,
        "period_end": payload.period_end,
        "amount": float(payload.amount),
        "currency": payload.currency or "VND",
        "due_date": payload.due_date,
        "status": "pending",
        "paid_at": None,
        "payment_id": None,
        "reminder_count": 0,
        "last_reminded_at": None,
        "note": payload.note,
        "created_at": datetime.now(),
        "updated_at": datetime.now(),
    }

    result = await db.tuition_invoices.insert_one(invoice_doc)
    invoice_doc["_id"] = result.inserted_id

    await create_notification(
        db=db,
        receiver_id=str(payload.parent_id),
        receiver_role="parent",
        title="Bạn có hóa đơn học phí mới",
        message=(
            f"Hóa đơn {payload.period_label} của lớp {payload.class_name}: "
            f"{float(payload.amount):,.0f} VNĐ."
        ),
        notification_type="tuition_invoice",
        extra_data={"invoice_id": str(result.inserted_id)}
    )

    return serialize_doc(invoice_doc)


async def update_invoice_status_service(db, invoice_id: str, payload):
    invoice = await db.tuition_invoices.find_one({
        "_id": to_object_id(invoice_id, "Invoice ID")
    })

    if not invoice:
        raise HTTPException(status_code=404, detail="Không tìm thấy hóa đơn.")

    update_doc = {
        "status": payload.status,
        "updated_at": datetime.now(),
    }

    if payload.note:
        update_doc["note"] = payload.note

    if payload.status == "paid" and not invoice.get("paid_at"):
        update_doc["paid_at"] = datetime.now()

    await db.tuition_invoices.update_one(
        {"_id": invoice["_id"]},
        {"$set": update_doc}
    )

    invoice.update(update_doc)
    return serialize_doc(invoice)


# =========================================================
# THANH TOÁN HỌC PHÍ
# =========================================================

async def pay_invoice_service(db, invoice_id: str, parent_id: str):
    invoice = await db.tuition_invoices.find_one({
        "_id": to_object_id(invoice_id, "Invoice ID")
    })

    if not invoice:
        raise HTTPException(status_code=404, detail="Không tìm thấy hóa đơn.")

    if str(invoice.get("parent_id")) != str(parent_id):
        raise HTTPException(
            status_code=403,
            detail="Bạn không có quyền thanh toán hóa đơn này."
        )

    if invoice.get("status") == "paid":
        return {
            "status": "success",
            "message": "Hóa đơn đã được thanh toán trước đó.",
            "invoice": serialize_doc(invoice),
        }

    if invoice.get("status") == "cancelled":
        raise HTTPException(
            status_code=400,
            detail="Hóa đơn đã bị hủy, không thể thanh toán."
        )

    parent = await get_user_or_404(db, parent_id, "Phụ huynh")

    amount = to_float(invoice.get("amount"), 0.0)
    balance_before = to_float(parent.get("balance"), 0.0)

    if amount <= 0:
        raise HTTPException(status_code=400, detail="Số tiền hóa đơn không hợp lệ.")

    if balance_before < amount:
        raise HTTPException(
            status_code=400,
            detail="Số dư ví không đủ để đóng học phí."
        )

    balance_after = balance_before - amount

    await db.users.update_one(
        {"_id": parent["_id"]},
        {"$inc": {"balance": -amount}}
    )

    payment_doc = {
        "invoice_id": str(invoice["_id"]),
        "parent_id": str(parent["_id"]),
        "student_id": str(invoice.get("student_id")),
        "class_id": str(invoice.get("class_id")),
        "amount": amount,
        "currency": invoice.get("currency", "VND"),
        "payment_method": "wallet",
        "balance_before": balance_before,
        "balance_after": balance_after,
        "status": "success",
        "transaction_code": f"TUITION-{datetime.now().strftime('%Y%m%d%H%M%S')}",
        "note": f"Thanh toán hóa đơn {invoice.get('period_label')}",
        "created_at": datetime.now(),
    }

    payment_result = await db.tuition_payments.insert_one(payment_doc)
    payment_doc["_id"] = payment_result.inserted_id

    await db.tuition_invoices.update_one(
        {"_id": invoice["_id"]},
        {
            "$set": {
                "status": "paid",
                "paid_at": datetime.now(),
                "payment_id": str(payment_result.inserted_id),
                "updated_at": datetime.now(),
            }
        }
    )

    invoice["status"] = "paid"
    invoice["paid_at"] = datetime.now()
    invoice["payment_id"] = str(payment_result.inserted_id)

    await create_notification(
        db=db,
        receiver_id=str(parent["_id"]),
        receiver_role="parent",
        title="Đóng học phí thành công",
        message=(
            f"Bạn đã thanh toán {amount:,.0f} VNĐ cho hóa đơn "
            f"{invoice.get('period_label')}."
        ),
        notification_type="tuition_paid",
        extra_data={
            "invoice_id": str(invoice["_id"]),
            "payment_id": str(payment_result.inserted_id),
        }
    )

    return {
        "status": "success",
        "message": "Đóng học phí thành công.",
        "invoice": serialize_doc(invoice),
        "payment": serialize_doc(payment_doc),
        "balance_after": balance_after,
    }


async def list_payments_service(
    db,
    parent_id: Optional[str] = None,
    student_id: Optional[str] = None,
):
    query = {}

    if parent_id:
        query["parent_id"] = str(parent_id)

    if student_id:
        query["student_id"] = str(student_id)

    cursor = db.tuition_payments.find(query).sort("created_at", -1)

    items = []

    async for doc in cursor:
        items.append(serialize_doc(doc))

    return items


# =========================================================
# TẠO HÓA ĐƠN KỲ TIẾP THEO
# =========================================================

async def create_next_invoice_service(db, enrollment_id: str):
    enrollment = await db.tuition_enrollments.find_one({
        "_id": to_object_id(enrollment_id, "Enrollment ID")
    })

    if not enrollment:
        raise HTTPException(status_code=404, detail="Không tìm thấy đăng ký lớp.")

    if enrollment.get("status") != "active":
        raise HTTPException(
            status_code=400,
            detail="Đăng ký lớp không còn hoạt động."
        )

    billing_plan = enrollment.get("billing_plan", "monthly")
    monthly_fee = to_float(enrollment.get("monthly_fee"), 0.0)
    cycle_months = int(enrollment.get("cycle_months") or 3)

    if billing_plan == "monthly":
        amount = monthly_fee
        months = 1
        invoice_type = "monthly"
    elif billing_plan == "cycle":
        amount = to_float(enrollment.get("cycle_fee"), 0.0)
        if amount <= 0:
            amount = monthly_fee * cycle_months
        months = cycle_months
        invoice_type = "cycle"
    elif billing_plan == "yearly":
        amount = to_float(enrollment.get("yearly_fee"), 0.0)
        if amount <= 0:
            amount = monthly_fee * 12
        months = 12
        invoice_type = "yearly"
    else:
        raise HTTPException(status_code=400, detail="Gói học phí không hợp lệ.")

    if amount <= 0:
        raise HTTPException(status_code=400, detail="Số tiền học phí không hợp lệ.")

    next_due = parse_date(enrollment.get("next_due_date"))
    period_start = next_due
    period_end = add_months(period_start, months) - timedelta(days=1)

    existing = await db.tuition_invoices.find_one({
        "enrollment_id": str(enrollment["_id"]),
        "invoice_type": invoice_type,
        "period_start": format_date(period_start),
        "period_end": format_date(period_end),
        "status": {"$ne": "cancelled"},
    })

    if existing:
        return {
            "status": "success",
            "message": "Hóa đơn kỳ này đã tồn tại.",
            "invoice": serialize_doc(existing),
        }

    invoice = await create_invoice_doc(
        db=db,
        enrollment=enrollment,
        invoice_type=invoice_type,
        amount=amount,
        period_start=period_start,
        period_end=period_end,
        due_date=next_due,
        note="Hóa đơn kỳ tiếp theo"
    )

    new_next_due = set_billing_day(
        add_months(period_start, months),
        int(enrollment.get("billing_day") or 5)
    )

    await db.tuition_enrollments.update_one(
        {"_id": enrollment["_id"]},
        {
            "$set": {
                "next_due_date": format_date(new_next_due),
                "updated_at": datetime.now()
            }
        }
    )

    await create_notification(
        db=db,
        receiver_id=str(enrollment["parent_id"]),
        receiver_role="parent",
        title="Có hóa đơn học phí mới",
        message=(
            f"Hóa đơn {invoice.get('period_label')} của lớp "
            f"{enrollment.get('class_name')}: {amount:,.0f} VNĐ."
        ),
        notification_type="tuition_invoice",
        extra_data={"invoice_id": str(invoice["_id"])}
    )

    return {
        "status": "success",
        "message": "Đã tạo hóa đơn kỳ tiếp theo.",
        "invoice": serialize_doc(invoice),
    }


# =========================================================
# NHẮC HỌC PHÍ / QUÁ HẠN
# =========================================================

async def mark_overdue_invoices_service(db):
    today = today_date()
    updated = 0

    cursor = db.tuition_invoices.find({
        "status": "pending"
    })

    async for invoice in cursor:
        due = parse_date(invoice.get("due_date"))

        if due < today:
            await db.tuition_invoices.update_one(
                {"_id": invoice["_id"]},
                {
                    "$set": {
                        "status": "overdue",
                        "updated_at": datetime.now()
                    }
                }
            )
            updated += 1

    return {
        "status": "success",
        "overdue_updated": updated,
    }


async def run_tuition_reminders_service(db, dry_run: bool = False):
    today = today_date()
    checked = 0
    reminded = 0
    overdue_updated = 0
    items = []

    overdue_result = await mark_overdue_invoices_service(db)
    overdue_updated = overdue_result.get("overdue_updated", 0)

    cursor = db.tuition_invoices.find({
        "status": {"$in": ["pending", "overdue"]}
    })

    reminder_offsets = [7, 3, 0, -1]

    async for invoice in cursor:
        checked += 1

        due = parse_date(invoice.get("due_date"))
        days_left = (due - today).days

        if days_left not in reminder_offsets:
            continue

        log_exists = await db.tuition_reminder_logs.find_one({
            "invoice_id": str(invoice["_id"]),
            "days_offset": days_left
        })

        if log_exists:
            continue

        if days_left > 0:
            reminder_type = "before_due"
            title = "Nhắc học phí sắp đến hạn"
            message = (
                f"Học phí {invoice.get('period_label')} của lớp "
                f"{invoice.get('class_name')} sẽ đến hạn sau {days_left} ngày. "
                f"Số tiền cần đóng: {to_float(invoice.get('amount')):,.0f} VNĐ."
            )
        elif days_left == 0:
            reminder_type = "due_today"
            title = "Học phí đến hạn hôm nay"
            message = (
                f"Học phí {invoice.get('period_label')} của lớp "
                f"{invoice.get('class_name')} đến hạn hôm nay. "
                f"Số tiền cần đóng: {to_float(invoice.get('amount')):,.0f} VNĐ."
            )
        else:
            reminder_type = "overdue"
            title = "Học phí đã quá hạn"
            message = (
                f"Học phí {invoice.get('period_label')} của lớp "
                f"{invoice.get('class_name')} đã quá hạn. "
                f"Số tiền cần đóng: {to_float(invoice.get('amount')):,.0f} VNĐ."
            )

        item = {
            "invoice_id": str(invoice["_id"]),
            "parent_id": invoice.get("parent_id"),
            "student_id": invoice.get("student_id"),
            "class_id": invoice.get("class_id"),
            "days_offset": days_left,
            "title": title,
            "message": message,
        }

        items.append(item)

        if dry_run:
            continue

        notification_id = await create_notification(
            db=db,
            receiver_id=str(invoice.get("parent_id")),
            receiver_role="parent",
            title=title,
            message=message,
            notification_type="tuition_reminder",
            extra_data={"invoice_id": str(invoice["_id"])}
        )

        await db.tuition_reminder_logs.insert_one({
            "invoice_id": str(invoice["_id"]),
            "parent_id": str(invoice.get("parent_id")),
            "student_id": str(invoice.get("student_id")),
            "class_id": str(invoice.get("class_id")),
            "reminder_type": reminder_type,
            "days_offset": days_left,
            "title": title,
            "message": message,
            "notification_id": notification_id,
            "sent_at": datetime.now(),
            "created_at": datetime.now(),
        })

        await db.tuition_invoices.update_one(
            {"_id": invoice["_id"]},
            {
                "$set": {
                    "last_reminded_at": datetime.now(),
                    "updated_at": datetime.now(),
                },
                "$inc": {"reminder_count": 1}
            }
        )

        reminded += 1

    return {
        "status": "success",
        "checked": checked,
        "reminded": reminded,
        "overdue_updated": overdue_updated,
        "items": items,
    }


# =========================================================
# TỔNG QUAN PHỤ HUYNH
# =========================================================

async def get_parent_tuition_summary_service(db, parent_id: str):
    invoices = await list_invoices_service(db, parent_id=parent_id)

    total_pending = 0.0
    total_overdue = 0.0
    total_paid = 0.0

    pending_count = 0
    overdue_count = 0
    paid_count = 0

    for invoice in invoices:
        amount = to_float(invoice.get("amount"), 0.0)
        status = invoice.get("status")

        if status == "paid":
            total_paid += amount
            paid_count += 1
        elif status == "overdue":
            total_overdue += amount
            overdue_count += 1
        elif status == "pending":
            total_pending += amount
            pending_count += 1

    return {
        "parent_id": str(parent_id),
        "total_pending": total_pending,
        "total_overdue": total_overdue,
        "total_paid": total_paid,
        "pending_count": pending_count,
        "overdue_count": overdue_count,
        "paid_count": paid_count,
        "invoice_count": len(invoices),
        "invoices": invoices,
    }