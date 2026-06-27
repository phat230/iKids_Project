# Backend/modules/tuition/router.py

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Body, Query

from core.database import get_db
from core.security import get_current_user

from .schemas import (
    TuitionEnrollmentCreate,
    TuitionPayInvoiceRequest,
    TuitionManualInvoiceCreate,
    TuitionUpdateInvoiceStatus,
    TuitionCreateNextInvoiceRequest,
    TuitionReminderRunRequest,
)

from .services import (
    list_public_classes_service,
    get_class_tuition_detail_service,
    create_enrollment_service,
    list_parent_enrollments_service,
    list_student_enrollments_service,
    get_invoice_service,
    list_invoices_service,
    create_manual_invoice_service,
    update_invoice_status_service,
    pay_invoice_service,
    list_payments_service,
    create_next_invoice_service,
    run_tuition_reminders_service,
    mark_overdue_invoices_service,
    get_parent_tuition_summary_service,
)


router = APIRouter()


# =========================================================
# HELPER PHÂN QUYỀN
# =========================================================

def get_current_user_id(current_user: dict) -> str:
    return str(
        current_user.get("user_id")
        or current_user.get("_id")
        or current_user.get("id")
        or ""
    )


def get_current_user_role(current_user: dict) -> str:
    return str(current_user.get("role") or "")


def ensure_admin_operator(current_user: dict):
    role = get_current_user_role(current_user)

    if role not in ["admin", "operator"]:
        raise HTTPException(
            status_code=403,
            detail="Chỉ admin hoặc operator mới có quyền thực hiện thao tác này."
        )


def ensure_parent_or_admin(current_user: dict, parent_id: str):
    role = get_current_user_role(current_user)
    user_id = get_current_user_id(current_user)

    if role in ["admin", "operator"]:
        return

    if role == "parent" and str(user_id) == str(parent_id):
        return

    raise HTTPException(
        status_code=403,
        detail="Bạn không có quyền xem hoặc thao tác dữ liệu học phí này."
    )


# =========================================================
# 1. LỚP HỌC CÓ HỌC PHÍ
# =========================================================

@router.get("/classes")
async def list_public_classes(db=Depends(get_db)):
    """
    Phụ huynh xem danh sách lớp public có thể đăng ký.
    """

    items = await list_public_classes_service(db)

    return {
        "status": "success",
        "total": len(items),
        "items": items
    }


@router.get("/classes/{class_id}")
async def get_class_tuition_detail(class_id: str, db=Depends(get_db)):
    """
    Xem chi tiết học phí của một lớp.
    """

    data = await get_class_tuition_detail_service(db, class_id)

    return {
        "status": "success",
        "data": data
    }


# =========================================================
# 2. ĐĂNG KÝ LỚP
# =========================================================

@router.post("/enrollments")
async def create_enrollment(
    payload: TuitionEnrollmentCreate,
    db=Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Phụ huynh đăng ký lớp cho con.
    Có thể chọn:
    - monthly
    - cycle
    - yearly

    Có thể chọn đóng phí đăng ký/học phí kỳ đầu ngay.
    """

    ensure_parent_or_admin(current_user, payload.parent_id)

    return await create_enrollment_service(db, payload)


@router.get("/parent/{parent_id}/enrollments")
async def list_parent_enrollments(
    parent_id: str,
    db=Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    ensure_parent_or_admin(current_user, parent_id)

    items = await list_parent_enrollments_service(db, parent_id)

    return {
        "status": "success",
        "total": len(items),
        "items": items
    }


@router.get("/student/{student_id}/enrollments")
async def list_student_enrollments(
    student_id: str,
    db=Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Admin/operator có thể xem enrollment của học sinh.
    Parent vẫn nên xem qua /parent/{parent_id}/enrollments.
    """

    role = get_current_user_role(current_user)

    if role not in ["admin", "operator", "teacher", "parent"]:
        raise HTTPException(status_code=403, detail="Không đủ quyền truy cập.")

    items = await list_student_enrollments_service(db, student_id)

    return {
        "status": "success",
        "total": len(items),
        "items": items
    }


# =========================================================
# 3. HÓA ĐƠN HỌC PHÍ
# =========================================================

@router.get("/invoices/{invoice_id}")
async def get_invoice(
    invoice_id: str,
    db=Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    invoice = await get_invoice_service(db, invoice_id)

    role = get_current_user_role(current_user)
    user_id = get_current_user_id(current_user)

    if role not in ["admin", "operator"] and str(invoice.get("parent_id")) != str(user_id):
        raise HTTPException(
            status_code=403,
            detail="Bạn không có quyền xem hóa đơn này."
        )

    return {
        "status": "success",
        "data": invoice
    }


@router.get("/parent/{parent_id}/invoices")
async def list_parent_invoices(
    parent_id: str,
    status: Optional[str] = Query(default=None),
    db=Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    ensure_parent_or_admin(current_user, parent_id)

    items = await list_invoices_service(
        db,
        parent_id=parent_id,
        status=status
    )

    return {
        "status": "success",
        "total": len(items),
        "items": items
    }


@router.get("/student/{student_id}/invoices")
async def list_student_invoices(
    student_id: str,
    status: Optional[str] = Query(default=None),
    db=Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    role = get_current_user_role(current_user)

    if role not in ["admin", "operator", "teacher", "parent"]:
        raise HTTPException(status_code=403, detail="Không đủ quyền truy cập.")

    items = await list_invoices_service(
        db,
        student_id=student_id,
        status=status
    )

    return {
        "status": "success",
        "total": len(items),
        "items": items
    }


@router.get("/admin/invoices")
async def admin_list_invoices(
    parent_id: Optional[str] = Query(default=None),
    student_id: Optional[str] = Query(default=None),
    class_id: Optional[str] = Query(default=None),
    status: Optional[str] = Query(default=None),
    db=Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    ensure_admin_operator(current_user)

    items = await list_invoices_service(
        db,
        parent_id=parent_id,
        student_id=student_id,
        class_id=class_id,
        status=status
    )

    return {
        "status": "success",
        "total": len(items),
        "items": items
    }


@router.post("/admin/invoices")
async def admin_create_invoice(
    payload: TuitionManualInvoiceCreate,
    db=Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    ensure_admin_operator(current_user)

    invoice = await create_manual_invoice_service(db, payload)

    return {
        "status": "success",
        "message": "Đã tạo hóa đơn học phí.",
        "data": invoice
    }


@router.put("/admin/invoices/{invoice_id}/status")
async def admin_update_invoice_status(
    invoice_id: str,
    payload: TuitionUpdateInvoiceStatus,
    db=Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    ensure_admin_operator(current_user)

    invoice = await update_invoice_status_service(db, invoice_id, payload)

    return {
        "status": "success",
        "message": "Đã cập nhật trạng thái hóa đơn.",
        "data": invoice
    }


# =========================================================
# 4. THANH TOÁN HỌC PHÍ
# =========================================================

@router.post("/invoices/pay")
async def pay_invoice(
    payload: TuitionPayInvoiceRequest,
    db=Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Phụ huynh đóng học phí bằng ví.
    """

    ensure_parent_or_admin(current_user, payload.parent_id)

    return await pay_invoice_service(
        db,
        invoice_id=payload.invoice_id,
        parent_id=payload.parent_id
    )


@router.get("/parent/{parent_id}/payments")
async def list_parent_payments(
    parent_id: str,
    db=Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    ensure_parent_or_admin(current_user, parent_id)

    items = await list_payments_service(
        db,
        parent_id=parent_id
    )

    return {
        "status": "success",
        "total": len(items),
        "items": items
    }


@router.get("/student/{student_id}/payments")
async def list_student_payments(
    student_id: str,
    db=Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    role = get_current_user_role(current_user)

    if role not in ["admin", "operator", "teacher", "parent"]:
        raise HTTPException(status_code=403, detail="Không đủ quyền truy cập.")

    items = await list_payments_service(
        db,
        student_id=student_id
    )

    return {
        "status": "success",
        "total": len(items),
        "items": items
    }


# =========================================================
# 5. TẠO HÓA ĐƠN KỲ TIẾP THEO
# =========================================================

@router.post("/admin/create-next-invoice")
async def admin_create_next_invoice(
    payload: TuitionCreateNextInvoiceRequest,
    db=Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    ensure_admin_operator(current_user)

    return await create_next_invoice_service(
        db,
        enrollment_id=payload.enrollment_id
    )


# =========================================================
# 6. NHẮC HỌC PHÍ / QUÁ HẠN
# =========================================================

@router.post("/admin/mark-overdue")
async def admin_mark_overdue(
    db=Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    ensure_admin_operator(current_user)

    return await mark_overdue_invoices_service(db)


@router.post("/admin/run-reminders")
async def admin_run_reminders(
    payload: TuitionReminderRunRequest = Body(default=TuitionReminderRunRequest()),
    db=Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Chạy nhắc học phí thủ công.

    Có thể gọi endpoint này mỗi ngày bằng cron/job.
    """
    ensure_admin_operator(current_user)

    return await run_tuition_reminders_service(
        db,
        dry_run=payload.dry_run
    )


# =========================================================
# 7. TỔNG QUAN HỌC PHÍ PHỤ HUYNH
# =========================================================

@router.get("/parent/{parent_id}/summary")
async def get_parent_tuition_summary(
    parent_id: str,
    db=Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    ensure_parent_or_admin(current_user, parent_id)

    data = await get_parent_tuition_summary_service(db, parent_id)

    return {
        "status": "success",
        "data": data
    }