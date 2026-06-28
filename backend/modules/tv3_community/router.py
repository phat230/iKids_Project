# backend/modules/tv3_community/router.py

import uuid
import asyncio
from datetime import datetime
from typing import Optional

import cloudinary.uploader
from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException, File, UploadFile, Form, Body, Request
from deep_translator import GoogleTranslator
from pydantic import BaseModel

from core.database import get_db
from core.security import get_current_user
from core.cloudinary_config import check_cloudinary_config

from .schemas import DepositRequest, ContactMessageCreate
from .rule_engine import calculate_exp_reward
from .services import (
    get_store_products_service,
    deposit_money_service,
    purchase_product_service,
    submit_contact_request,
    get_contact_history,
    update_account_profile_service,
    send_forgot_password_email_service,
    verify_otp_and_reset_password_service,
    award_exp_service,
)

router = APIRouter()
translator = GoogleTranslator(source="vi", target="en")


# =========================================================
# HELPER DÙNG CHUNG
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


def serialize_mongo_doc(doc: dict) -> dict:
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


async def find_doc_by_id(collection, raw_id: str) -> Optional[dict]:
    if not raw_id:
        return None

    try:
        doc = await collection.find_one({"_id": ObjectId(str(raw_id))})
        if doc:
            return doc
    except Exception:
        pass

    doc = await collection.find_one({"id": str(raw_id)})
    return doc


async def create_notification(
    db,
    receiver_id: str,
    receiver_role: str,
    title: str,
    message: str,
    notification_type: str = "system",
    extra_data: Optional[dict] = None,
):
    try:
        result = await db.notifications.insert_one({
            "sender_id": "system",
            "sender_role": "system",
            "sender_name": "iKids System",
            "receiver_id": str(receiver_id),
            "receiver_role": receiver_role,
            "title": title,
            "content": message,
            "message": message,
            "type": notification_type,
            "extra_data": extra_data or {},
            "is_read": False,
            "created_at": datetime.now()
        })
        return str(result.inserted_id)
    except Exception as e:
        print(f"⚠️ Không thể tạo notification: {e}")
        return None


async def ensure_parent_owns_child(db, parent_id: str, child_id: str) -> bool:
    parent = await db.users.find_one({"_id": to_object_id(parent_id, "Parent ID")})

    if not parent:
        return False

    student_ids_ref = parent.get("student_ids_ref") or []

    return str(child_id) in [str(sid) for sid in student_ids_ref]


def get_payload_public_id(payload: dict) -> str:
    return payload.get("image_public_id") or payload.get("public_id") or ""


async def delete_cloudinary_image_safely(public_id: str):
    if not public_id:
        return

    try:
        await asyncio.to_thread(
            cloudinary.uploader.destroy,
            public_id,
            resource_type="image"
        )
    except Exception as e:
        print(f"⚠️ Không thể xóa ảnh Cloudinary {public_id}: {str(e)}")


def normalize_memory_payload(data: dict) -> dict:
    media_url = data.get("media_url") or data.get("image_url") or ""

    data["media_url"] = media_url
    data["image_url"] = data.get("image_url") or media_url
    data["image_public_id"] = data.get("image_public_id") or data.get("public_id") or ""

    data["title"] = data.get("title") or "Kỷ niệm lớp học"
    data["description"] = data.get("description") or ""
    data["teacher_name"] = data.get("teacher_name") or "Giáo viên iKids"

    data["class_id"] = str(data.get("class_id") or "")
    data["class_name"] = data.get("class_name") or ""
    data["class_subject"] = data.get("class_subject") or ""

    data["type"] = data.get("type") or "image"
    data["status"] = data.get("status") or "published"
    data["likes"] = int(data.get("likes") or 0)

    created_at = data.get("created_at")
    if created_at:
        try:
            data["created_at"] = datetime.fromisoformat(str(created_at).replace("Z", ""))
        except Exception:
            data["created_at"] = datetime.now()
    else:
        data["created_at"] = datetime.now()

    data["updated_at"] = datetime.now()

    return data


# =========================================================
# REQUEST MODELS
# =========================================================

class MemoryCreateRequest(BaseModel):
    title: Optional[str] = "Kỷ niệm lớp học"
    description: str

    media_url: str
    image_url: Optional[str] = None
    image_public_id: Optional[str] = ""

    teacher_id: str
    teacher_name: Optional[str] = "Giáo viên iKids"

    class_id: Optional[str] = ""
    class_name: Optional[str] = ""
    class_subject: Optional[str] = ""

    type: Optional[str] = "image"
    status: Optional[str] = "published"
    likes: Optional[int] = 0
    created_at: Optional[str] = None


# =========================================================
# 1. CỬA HÀNG DÀNH CHO NGƯỜI DÙNG
# =========================================================

@router.get("/products")
async def api_get_products(db=Depends(get_db)):
    return await get_store_products_service(db)


async def purchase_product_for_child(
    db,
    payer_id: str,
    product_id: str,
    target_student_id: str,
):
    payer = await db.users.find_one({"_id": to_object_id(payer_id, "User ID")})
    if not payer:
        raise HTTPException(status_code=404, detail="Không tìm thấy người thanh toán.")

    product = await find_doc_by_id(db.products, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Không tìm thấy sản phẩm.")

    is_parent_owner = await ensure_parent_owns_child(db, payer_id, target_student_id)
    if not is_parent_owner:
        raise HTTPException(
            status_code=403,
            detail="Bạn không có quyền mua/tặng sản phẩm cho học sinh này."
        )

    price = to_float(product.get("price"), 0.0)
    if price <= 0:
        raise HTTPException(status_code=400, detail="Giá sản phẩm không hợp lệ.")

    current_balance = to_float(payer.get("balance"), 0.0)

    if current_balance < price:
        raise HTTPException(status_code=400, detail="Số dư ví không đủ để mua sản phẩm.")

    balance_after = current_balance - price

    await db.users.update_one(
        {"_id": payer["_id"]},
        {"$inc": {"balance": -price}}
    )

    purchase_doc = {
        "payer_id": str(payer["_id"]),
        "target_student_id": str(target_student_id),
        "product_id": str(product.get("_id", product_id)),
        "product_name": product.get("name", "Sản phẩm"),
        "price": price,
        "payment_method": "wallet",
        "balance_before": current_balance,
        "balance_after": balance_after,
        "status": "success",
        "type": "parent_gift",
        "created_at": datetime.now()
    }

    result = await db.purchase_history.insert_one(purchase_doc)

    await create_notification(
        db=db,
        receiver_id=target_student_id,
        receiver_role="student",
        title="Bạn vừa được tặng quà 🎁",
        message="Phụ huynh đã mua/tặng cho bạn một phần quà trong cửa hàng iKids.",
        notification_type="store_gift",
        extra_data={
            "product_id": str(product.get("_id", product_id)),
            "purchase_id": str(result.inserted_id)
        }
    )

    return {
        "status": "success",
        "message": "Mua/tặng sản phẩm thành công.",
        "purchase_id": str(result.inserted_id),
        "balance_after": balance_after
    }


@router.post("/products/purchase")
async def api_purchase_product(payload: dict = Body(...), db=Depends(get_db)):
    user_id = payload.get("user_id")
    product_id = payload.get("product_id")
    target_student_id = payload.get("target_student_id")

    if not user_id or not product_id:
        raise HTTPException(
            status_code=400,
            detail="Thiếu user_id hoặc product_id."
        )

    if target_student_id:
        return await purchase_product_for_child(
            db=db,
            payer_id=user_id,
            product_id=product_id,
            target_student_id=target_student_id
        )

    result = await purchase_product_service(db, user_id, product_id)

    if result.get("status") == "failed":
        raise HTTPException(
            status_code=400,
            detail=result.get("message", "Mua hàng thất bại.")
        )

    return result


# =========================================================
# 2. TÀI CHÍNH & PROFILE
# =========================================================

@router.post("/account/deposit")
async def api_deposit_money(req: DepositRequest, db=Depends(get_db)):
    result = await deposit_money_service(db, req.user_id, req.amount)

    if result["status"] == "failed":
        raise HTTPException(status_code=404, detail=result["message"])

    return result


# =========================================================
# 3. QUẢN LÝ SỰ CỐ NẠP TIỀN ADMIN
# =========================================================

@router.get("/admin/deposit-issues")
async def api_get_deposit_issues(db=Depends(get_db)):
    cursor = db.deposit_issues.find({"status": "pending"}).sort("created_at", -1)

    issues = []

    async for doc in cursor:
        issues.append(serialize_mongo_doc(doc))

    return issues


@router.post("/admin/resolve-deposit/{issue_id}")
async def api_resolve_deposit_issue(issue_id: str, db=Depends(get_db)):
    try:
        issue = await db.deposit_issues.find_one({"_id": to_object_id(issue_id, "Issue ID")})

        if not issue:
            raise HTTPException(status_code=404, detail="Không tìm thấy yêu cầu.")

        user_id = issue.get("sender_id")
        amount = to_float(issue.get("amount"), 0.0)

        if amount <= 0:
            raise HTTPException(status_code=400, detail="Số tiền không hợp lệ.")

        deposit_res = await deposit_money_service(db, user_id, amount)

        if deposit_res["status"] == "failed":
            raise HTTPException(status_code=400, detail="Lỗi cập nhật số dư.")

        await db.deposit_issues.update_one(
            {"_id": issue["_id"]},
            {
                "$set": {
                    "status": "resolved",
                    "resolved_at": datetime.now(),
                    "admin_note": f"Đã duyệt thủ công số tiền {amount}"
                }
            }
        )

        await db.deposit_history.insert_one({
            "user_id": str(user_id),
            "amount": amount,
            "type": "manual_admin_resolve",
            "issue_id": str(issue["_id"]),
            "created_at": datetime.now()
        })

        await create_notification(
            db=db,
            receiver_id=str(user_id),
            receiver_role="parent",
            title="Nạp tiền thành công",
            message=f"Tài khoản của bạn đã được cộng {amount:,.0f} VNĐ.",
            notification_type="deposit"
        )

        return {
            "status": "success",
            "message": f"Đã cộng {amount:,.0f} VNĐ thành công."
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Lỗi: {str(e)}")


# =========================================================
# 4. WEBHOOK PAYOS
# =========================================================

@router.post("/webhook/payos")
async def payos_webhook(request: Request, db=Depends(get_db)):
    try:
        body = await request.json()

        data = body.get("data", body)
        description = str(data.get("description", "")).upper()
        amount = to_float(data.get("amount"), 0.0)
        reference = data.get("reference") or data.get("paymentLinkId")

        if amount <= 0:
            return {"status": "ignored", "reason": "amount_invalid"}

        if "IKIDS NAP" not in description:
            return {"status": "ignored", "reason": "description_not_match"}

        user_suffix = description.split("IKIDS NAP")[-1].strip()

        matched_user = None
        users = await db.users.find({}, {"_id": 1, "role": 1}).to_list(length=5000)

        for u in users:
            if str(u["_id"]).endswith(user_suffix):
                matched_user = u
                break

        if not matched_user:
            return {"status": "ignored", "reason": "user_not_found"}

        user_id = str(matched_user["_id"])

        if reference:
            already_processed = await db.deposit_history.find_one({"reference": reference})
            if already_processed:
                return {"status": "success", "message": "already_processed"}

        await deposit_money_service(db, user_id, amount)

        await db.deposit_history.insert_one({
            "user_id": user_id,
            "amount": amount,
            "reference": reference,
            "type": "payos_auto",
            "created_at": datetime.now()
        })

        await create_notification(
            db=db,
            receiver_id=user_id,
            receiver_role=matched_user.get("role", "parent"),
            title="Nạp tiền thành công",
            message=f"Tài khoản của bạn đã được cộng {amount:,.0f} VNĐ.",
            notification_type="deposit",
            extra_data={"reference": reference}
        )

        return {"status": "success"}

    except Exception as e:
        print(f"Webhook PayOS error: {e}")
        return {"status": "error"}


# =========================================================
# 5. GAMIFICATION & PROFILE
# =========================================================

@router.get("/gamification/profile/{user_id}")
async def get_account_profile(user_id: str, db=Depends(get_db)):
    try:
        user = await db.users.find_one({"_id": to_object_id(user_id, "User ID")})

        if not user:
            return {
                "user_id": user_id,
                "balance": 0.0,
                "exp": 0,
                "rank": "Beginner"
            }

        return {
            "user_id": str(user["_id"]),
            "id": str(user["_id"]),
            "full_name": user.get("full_name", user.get("name", "N/A")),
            "name": user.get("name", user.get("full_name", "N/A")),
            "email": user.get("email", ""),
            "role": user.get("role", ""),
            "balance": to_float(user.get("balance"), 0.0),
            "exp": user.get("exp", 0),
            "rank": user.get("rank", "Beginner"),
            "avatar_url": user.get("avatar_url", "")
        }

    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=400, detail="ID không hợp lệ.")


@router.post("/gamification/award-exp")
async def api_award_exp(payload: dict = Body(...), db=Depends(get_db)):
    student_id = payload.get("student_id")
    action = payload.get("action")

    amount = calculate_exp_reward(action)

    if amount <= 0:
        raise HTTPException(status_code=400, detail="Hành động không hợp lệ.")

    return await award_exp_service(db, student_id, amount, action)


# =========================================================
# 6. KỶ NIỆM LỚP HỌC
# =========================================================

@router.get("/memories")
async def api_get_memories(class_id: Optional[str] = None, db=Depends(get_db)):
    query = {
        "status": {"$ne": "deleted"}
    }

    if class_id:
        query["class_id"] = str(class_id)

    cursor = db.memories.find(query).sort("created_at", -1)

    memories = []

    async for doc in cursor:
        memories.append(serialize_mongo_doc(doc))

    return memories


@router.post("/memories")
async def api_create_memory(
    payload: MemoryCreateRequest,
    db=Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    try:
        current_role = current_user.get("role", "")
        current_user_id = current_user.get("user_id", "")

        if current_role not in ["teacher", "admin", "operator"]:
            raise HTTPException(
                status_code=403,
                detail="Bạn không có quyền đăng kỷ niệm."
            )

        data = normalize_memory_payload(payload.dict())

        if not data.get("description"):
            raise HTTPException(
                status_code=400,
                detail="Mô tả kỷ niệm không được trống."
            )

        if not data.get("media_url"):
            raise HTTPException(
                status_code=400,
                detail="Ảnh kỷ niệm không được trống."
            )

        # Ưu tiên user đang đăng nhập để tránh giả mạo teacher_id
        data["teacher_id"] = str(current_user_id or data.get("teacher_id", ""))

        if not data.get("teacher_name"):
            data["teacher_name"] = current_user.get("full_name") or current_user.get("name") or "Giáo viên iKids"

        result = await db.memories.insert_one(data)
        created = await db.memories.find_one({"_id": result.inserted_id})

        # Gửi thông báo nhẹ cho phụ huynh/học sinh nếu có class_id
        if data.get("class_id"):
            await create_notification(
                db=db,
                receiver_id="all",
                receiver_role="parent",
                title="Có kỷ niệm lớp học mới 📸",
                message=f"Lớp {data.get('class_name', '')} vừa có ảnh kỷ niệm mới.",
                notification_type="memory",
                extra_data={
                    "memory_id": str(result.inserted_id),
                    "class_id": data.get("class_id"),
                    "class_name": data.get("class_name")
                }
            )

            await create_notification(
                db=db,
                receiver_id="all",
                receiver_role="student",
                title="Có kỷ niệm lớp học mới 📸",
                message=f"Lớp {data.get('class_name', '')} vừa có ảnh kỷ niệm mới.",
                notification_type="memory",
                extra_data={
                    "memory_id": str(result.inserted_id),
                    "class_id": data.get("class_id"),
                    "class_name": data.get("class_name")
                }
            )

        return {
            "status": "success",
            "message": "Đăng kỷ niệm thành công.",
            "data": serialize_mongo_doc(created)
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Lỗi đăng kỷ niệm: {str(e)}"
        )


@router.delete("/memories/{memory_id}")
async def api_delete_memory(
    memory_id: str,
    db=Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    try:
        memory = await db.memories.find_one({"_id": to_object_id(memory_id, "Memory ID")})

        if not memory:
            raise HTTPException(status_code=404, detail="Không tìm thấy kỷ niệm.")

        current_role = current_user.get("role", "")
        current_user_id = str(current_user.get("user_id", ""))

        is_owner = str(memory.get("teacher_id", "")) == current_user_id
        is_manager = current_role in ["admin", "operator"]

        if not is_owner and not is_manager:
            raise HTTPException(
                status_code=403,
                detail="Bạn không có quyền xóa kỷ niệm này."
            )

        await delete_cloudinary_image_safely(memory.get("image_public_id", ""))

        await db.memories.delete_one({"_id": memory["_id"]})

        return {
            "status": "success",
            "message": "Đã xóa kỷ niệm."
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Lỗi xóa kỷ niệm: {str(e)}"
        )


@router.post("/memories/{memory_id}/like")
@router.put("/memories/{memory_id}/like")
async def api_like_memory(memory_id: str, db=Depends(get_db)):
    try:
        memory = await db.memories.find_one({"_id": to_object_id(memory_id, "Memory ID")})

        if not memory:
            raise HTTPException(status_code=404, detail="Không tìm thấy kỷ niệm.")

        await db.memories.update_one(
            {"_id": memory["_id"]},
            {
                "$inc": {"likes": 1},
                "$set": {"updated_at": datetime.now()}
            }
        )

        updated = await db.memories.find_one({"_id": memory["_id"]})

        return {
            "status": "success",
            "likes": updated.get("likes", 0),
            "data": serialize_mongo_doc(updated)
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Lỗi thả tim kỷ niệm: {str(e)}"
        )


# =========================================================
# 7. LIÊN HỆ & AUTH PHỤ
# =========================================================

@router.post("/contact/submit")
async def api_submit_contact(request_data: ContactMessageCreate, db=Depends(get_db)):
    return await submit_contact_request(db, request_data)


@router.post("/contact")
async def api_submit_contact_alias(payload: dict = Body(...), db=Depends(get_db)):
    """
    Alias cho frontend/pages/parent/lien_he.py nếu trang đó đang gọi POST /api/tv3/contact.
    """
    try:
        req = ContactMessageCreate(**payload)
        return await submit_contact_request(db, req)
    except Exception:
        doc = dict(payload)
        doc["created_at"] = datetime.now()
        doc["updated_at"] = datetime.now()
        result = await db.contact_requests.insert_one(doc)

        return {
            "status": "success",
            "id": str(result.inserted_id)
        }


@router.get("/contact/history/{user_id}")
async def api_get_contact_history(user_id: str, db=Depends(get_db)):
    return await get_contact_history(db, user_id)


@router.post("/profile/update/{user_id}")
async def api_update_profile(
    user_id: str,
    full_name: str = Form(None),
    avatar_file: UploadFile = File(None),
    db=Depends(get_db)
):
    return await update_account_profile_service(db, user_id, full_name, avatar_file)


@router.post("/auth/forgot-password")
async def forgot_password(payload: dict = Body(...), db=Depends(get_db)):
    return await send_forgot_password_email_service(db, payload.get("email"))


@router.post("/auth/verify-reset")
async def verify_reset(payload: dict = Body(...), db=Depends(get_db)):
    return await verify_otp_and_reset_password_service(
        db,
        payload.get("email"),
        payload.get("otp"),
        payload.get("new_password")
    )


# =========================================================
# 8. QUẢN LÝ CON
# =========================================================

@router.get("/parent/my-children")
async def get_my_children(
    db=Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    parent_id = current_user.get("user_id")

    parent = await db.users.find_one({"_id": to_object_id(parent_id, "Parent ID")})

    if not parent or not parent.get("student_ids_ref"):
        return []

    child_object_ids = []

    for sid in parent.get("student_ids_ref", []):
        try:
            child_object_ids.append(ObjectId(str(sid)))
        except Exception:
            pass

    if not child_object_ids:
        return []

    children = await db.users.find(
        {"_id": {"$in": child_object_ids}}
    ).to_list(length=50)

    result = []

    for child in children:
        if "password" in child:
            del child["password"]

        result.append(serialize_mongo_doc(child))

    return result


@router.post("/parent/transfer-to-child")
async def transfer_to_child(
    payload: dict = Body(...),
    db=Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    child_id = payload.get("child_id")
    amount = to_float(payload.get("amount"), 0.0)
    parent_id = current_user.get("user_id")

    if amount <= 0:
        return {"status": "failed", "message": "Số tiền không hợp lệ."}

    is_owner = await ensure_parent_owns_child(db, parent_id, child_id)
    if not is_owner:
        raise HTTPException(status_code=403, detail="Bạn không có quyền thao tác với tài khoản này.")

    parent = await db.users.find_one({"_id": to_object_id(parent_id, "Parent ID")})

    if not parent:
        raise HTTPException(status_code=404, detail="Không tìm thấy phụ huynh.")

    if to_float(parent.get("balance"), 0.0) < amount:
        return {"status": "failed", "message": "Số dư không đủ."}

    await db.users.update_one(
        {"_id": parent["_id"]},
        {"$inc": {"balance": -amount}}
    )

    await db.users.update_one(
        {"_id": to_object_id(child_id, "Child ID")},
        {"$inc": {"balance": amount}}
    )

    await db.wallet_transfers.insert_one({
        "parent_id": str(parent["_id"]),
        "child_id": str(child_id),
        "amount": amount,
        "type": "parent_to_child",
        "created_at": datetime.now()
    })

    await create_notification(
        db=db,
        receiver_id=str(child_id),
        receiver_role="student",
        title="Bạn vừa nhận tiền từ phụ huynh",
        message=f"Ví của bạn vừa được cộng {amount:,.0f} VNĐ.",
        notification_type="wallet"
    )

    return {"status": "success", "message": "Đã gửi tiền cho con."}


@router.post("/parent/withdraw-from-child")
async def withdraw_from_child(
    payload: dict = Body(...),
    db=Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    child_id = payload.get("child_id")
    amount = to_float(payload.get("amount"), 0.0)
    parent_id = current_user.get("user_id")

    if amount <= 0:
        return {"status": "failed", "message": "Số tiền không hợp lệ."}

    is_owner = await ensure_parent_owns_child(db, parent_id, child_id)
    if not is_owner:
        raise HTTPException(status_code=403, detail="Bạn không có quyền thao tác với tài khoản này.")

    child = await db.users.find_one({"_id": to_object_id(child_id, "Child ID")})

    if not child:
        raise HTTPException(status_code=404, detail="Không tìm thấy tài khoản của bé.")

    if to_float(child.get("balance"), 0.0) < amount:
        return {"status": "failed", "message": "Ví của bé không đủ số dư."}

    await db.users.update_one(
        {"_id": child["_id"]},
        {"$inc": {"balance": -amount}}
    )

    await db.users.update_one(
        {"_id": to_object_id(parent_id, "Parent ID")},
        {"$inc": {"balance": amount}}
    )

    await db.wallet_transfers.insert_one({
        "parent_id": str(parent_id),
        "child_id": str(child["_id"]),
        "amount": amount,
        "type": "child_to_parent",
        "created_at": datetime.now()
    })

    return {"status": "success", "message": "Đã rút tiền từ ví con."}


# =========================================================
# 9. YÊU CẦU MUA HÀNG HỌC SINH
# =========================================================

@router.post("/store/request-purchase")
async def student_request_purchase(req: dict = Body(...), db=Depends(get_db)):
    student_id = req.get("student_id")
    product_id = req.get("product_id")
    product_name = req.get("product_name", "Sản phẩm")
    price = to_float(req.get("price"), 0.0)

    if not student_id or not product_id:
        raise HTTPException(status_code=400, detail="Thiếu student_id hoặc product_id.")

    student = await db.users.find_one({"_id": to_object_id(student_id, "Student ID")})
    child_name = student.get("name", student.get("full_name", "Bé")) if student else "Bé"

    parent_id = req.get("parent_id")

    if not parent_id:
        parent = await db.users.find_one({"student_ids_ref": str(student_id)})

        if not parent:
            try:
                parent = await db.users.find_one({"student_ids_ref": ObjectId(str(student_id))})
            except Exception:
                parent = None

        if parent:
            parent_id = str(parent["_id"])

    if not parent_id:
        raise HTTPException(status_code=404, detail="Không tìm thấy phụ huynh của học sinh này.")

    request_doc = {
        "student_id": str(student_id),
        "parent_id": str(parent_id),
        "child_name": child_name,
        "product_id": str(product_id),
        "product_name": product_name,
        "price": price,
        "status": "pending",
        "created_at": datetime.now()
    }

    result = await db.purchase_requests.insert_one(request_doc)

    await create_notification(
        db=db,
        receiver_id=str(parent_id),
        receiver_role="parent",
        title="Yêu cầu mua hàng từ bé",
        message=f"{child_name} muốn xin mua: {product_name} ({price:,.0f} VNĐ).",
        notification_type="purchase_request",
        extra_data={
            "request_id": str(result.inserted_id),
            "student_id": str(student_id),
            "product_id": str(product_id)
        }
    )

    return {
        "status": "success",
        "message": "Đã gửi yêu cầu mua tới Ba Mẹ!",
        "request_id": str(result.inserted_id)
    }


@router.get("/parent/purchase-requests")
async def get_parent_purchase_requests(
    db=Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    parent_id = current_user.get("user_id")

    cursor = db.purchase_requests.find({
        "parent_id": str(parent_id),
        "status": "pending"
    }).sort("created_at", -1)

    requests_list = []

    async for req in cursor:
        requests_list.append(serialize_mongo_doc(req))

    return requests_list


@router.post("/parent/approve-purchase/{request_id}")
async def parent_approve_purchase(
    request_id: str,
    payload: dict = Body(...),
    db=Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    action = payload.get("action")
    parent_id = current_user.get("user_id")

    req = await db.purchase_requests.find_one({"_id": to_object_id(request_id, "Request ID")})

    if not req:
        raise HTTPException(status_code=404, detail="Không thấy yêu cầu mua hàng.")

    if str(req.get("parent_id")) != str(parent_id):
        raise HTTPException(status_code=403, detail="Bạn không có quyền duyệt yêu cầu này.")

    if action == "reject":
        await db.purchase_requests.update_one(
            {"_id": req["_id"]},
            {"$set": {"status": "rejected", "updated_at": datetime.now()}}
        )

        await create_notification(
            db=db,
            receiver_id=req["student_id"],
            receiver_role="student",
            title="Yêu cầu mua hàng đã bị từ chối",
            message=f"Yêu cầu mua {req.get('product_name', 'sản phẩm')} đã bị từ chối.",
            notification_type="purchase_request"
        )

        return {"status": "success", "message": "Đã từ chối yêu cầu."}

    if action == "approve":
        parent = await db.users.find_one({"_id": to_object_id(parent_id, "Parent ID")})

        if not parent:
            raise HTTPException(status_code=404, detail="Không tìm thấy phụ huynh.")

        price = to_float(req.get("price"), 0.0)

        if to_float(parent.get("balance"), 0.0) < price:
            return {"status": "failed", "message": "Ví phụ huynh không đủ tiền."}

        await db.users.update_one(
            {"_id": parent["_id"]},
            {"$inc": {"balance": -price}}
        )

        await db.purchase_requests.update_one(
            {"_id": req["_id"]},
            {
                "$set": {
                    "status": "approved",
                    "approved_at": datetime.now(),
                    "updated_at": datetime.now()
                }
            }
        )

        await db.purchase_history.insert_one({
            "payer_id": str(parent["_id"]),
            "target_student_id": str(req["student_id"]),
            "product_id": str(req["product_id"]),
            "product_name": req.get("product_name", "Sản phẩm"),
            "price": price,
            "payment_method": "wallet",
            "type": "parent_approved_request",
            "request_id": str(req["_id"]),
            "status": "success",
            "created_at": datetime.now()
        })

        await create_notification(
            db=db,
            receiver_id=req["student_id"],
            receiver_role="student",
            title="Ba mẹ đã duyệt mua quà 🎁",
            message=f"Yêu cầu mua {req.get('product_name', 'sản phẩm')} đã được duyệt.",
            notification_type="purchase_request"
        )

        return {"status": "success", "message": "Đã duyệt yêu cầu mua hàng."}

    raise HTTPException(status_code=400, detail="Hành động không hợp lệ.")


# =========================================================
# 10. QUẢN LÝ NỘI DUNG TRANG CHỦ CMS + CLOUDINARY
# =========================================================

ALLOWED_IMAGE_TYPES = {
    "image/jpeg",
    "image/png",
    "image/webp",
    "image/gif"
}


@router.post("/upload_image")
async def upload_image_from_mobile(file: UploadFile = File(...)):
    try:
        check_cloudinary_config()

        if file.content_type not in ALLOWED_IMAGE_TYPES:
            raise HTTPException(
                status_code=400,
                detail="Chỉ cho phép upload ảnh JPG, PNG, WEBP hoặc GIF."
            )

        public_id = f"img_{uuid.uuid4().hex[:12]}"

        upload_result = await asyncio.to_thread(
            cloudinary.uploader.upload,
            file.file,
            folder="ikids/uploads",
            public_id=public_id,
            resource_type="image",
            overwrite=False
        )

        image_url = upload_result.get("secure_url")
        image_public_id = upload_result.get("public_id")

        if not image_url:
            raise HTTPException(
                status_code=500,
                detail="Cloudinary không trả về URL ảnh."
            )

        return {
            "status": "success",
            "image_url": image_url,
            "image_public_id": image_public_id,
            "public_id": image_public_id
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"🔥 LỖI UPLOAD ẢNH CLOUDINARY: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Lỗi upload ảnh Cloudinary: {str(e)}"
        )


@router.get("/posts")
async def get_all_posts(status: str = None, db=Depends(get_db)):
    query = {}

    if status:
        query["status"] = status

    cursor = db.posts.find(query).sort("created_at", -1)
    posts = []

    async for doc in cursor:
        posts.append(serialize_mongo_doc(doc))

    return posts


@router.post("/posts")
async def create_new_post(payload: dict = Body(...), db=Depends(get_db)):
    try:
        title_vi = payload.get("title", "").strip()
        content_vi = payload.get("content", "").strip()

        if not title_vi or not content_vi:
            raise HTTPException(
                status_code=400,
                detail="Tiêu đề và nội dung không được trống."
            )

        core_translator = GoogleTranslator(source="vi", target="en")

        try:
            translated_title = core_translator.translate(title_vi)
            translated_content = core_translator.translate(content_vi)
        except Exception:
            translated_title = title_vi
            translated_content = content_vi

        multilang_post = {
            "title": {
                "vi": title_vi,
                "en": translated_title if translated_title else title_vi
            },
            "content": {
                "vi": content_vi,
                "en": translated_content if translated_content else content_vi
            },
            "image_url": payload.get("image_url", ""),
            "image_public_id": get_payload_public_id(payload),
            "layout": payload.get("layout", "left"),
            "img_width": payload.get("img_width", 400),
            "status": payload.get("status", "published"),
            "date": payload.get("date", datetime.now().strftime("%d/%m/%Y")),
            "created_at": datetime.now(),
            "updated_at": datetime.now()
        }

        result = await db.posts.insert_one(multilang_post)

        return {
            "status": "success",
            "id": str(result.inserted_id)
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Lỗi tạo bài viết: {str(e)}"
        )


@router.put("/posts/{post_id}")
async def update_post(post_id: str, payload: dict = Body(...), db=Depends(get_db)):
    try:
        old_post = await db.posts.find_one({"_id": to_object_id(post_id, "Post ID")})

        if not old_post:
            raise HTTPException(status_code=404, detail="Không tìm thấy bài viết cần sửa.")

        title_vi = payload.get("title", "").strip()
        content_vi = payload.get("content", "").strip()

        if not title_vi or not content_vi:
            raise HTTPException(
                status_code=400,
                detail="Tiêu đề và nội dung không được trống."
            )

        core_translator = GoogleTranslator(source="vi", target="en")

        try:
            translated_title = core_translator.translate(title_vi)
            translated_content = core_translator.translate(content_vi)
        except Exception:
            translated_title = title_vi
            translated_content = content_vi

        old_public_id = old_post.get("image_public_id", "")
        new_public_id = get_payload_public_id(payload)
        new_image_url = payload.get("image_url", old_post.get("image_url", ""))

        if "image_url" in payload and not payload.get("image_url"):
            if old_public_id:
                await delete_cloudinary_image_safely(old_public_id)
            new_public_id = ""

        elif new_public_id and old_public_id and new_public_id != old_public_id:
            await delete_cloudinary_image_safely(old_public_id)

        if not new_public_id and new_image_url:
            new_public_id = old_public_id

        update_doc = {
            "title": {
                "vi": title_vi,
                "en": translated_title if translated_title else title_vi
            },
            "content": {
                "vi": content_vi,
                "en": translated_content if translated_content else content_vi
            },
            "image_url": new_image_url,
            "image_public_id": new_public_id,
            "layout": payload.get("layout", "left"),
            "img_width": payload.get("img_width", 400),
            "status": payload.get("status", "published"),
            "updated_at": datetime.now()
        }

        await db.posts.update_one(
            {"_id": old_post["_id"]},
            {"$set": update_doc}
        )

        return {"status": "success"}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Lỗi sửa bài viết: {str(e)}"
        )


@router.delete("/posts/{post_id}")
async def delete_post(post_id: str, db=Depends(get_db)):
    try:
        post = await db.posts.find_one({"_id": to_object_id(post_id, "Post ID")})

        if not post:
            raise HTTPException(status_code=404, detail="Không tìm thấy bài viết cần xóa.")

        await delete_cloudinary_image_safely(post.get("image_public_id", ""))
        await db.posts.delete_one({"_id": post["_id"]})

        return {"status": "success"}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Lỗi xóa bài viết: {str(e)}"
        )


@router.get("/about")
async def get_about(db=Depends(get_db)):
    data = await db.config.find_one({"type": "about"})

    if not data:
        return {}

    return serialize_mongo_doc(data)


@router.put("/about")
async def update_about(payload: dict = Body(...), db=Depends(get_db)):
    try:
        content_vi = payload.get("content", "").strip()

        core_translator = GoogleTranslator(source="vi", target="en")

        try:
            translated_content = core_translator.translate(content_vi) if content_vi else ""
        except Exception:
            translated_content = content_vi

        multilang_about = {
            "type": "about",
            "title": payload.get("title", "Giới thiệu"),
            "content": {
                "vi": content_vi,
                "en": translated_content
            },
            "images": payload.get("images", []),
            "image_public_ids": payload.get("image_public_ids", []),
            "layout": payload.get("layout", "left"),
            "img_width": payload.get("img_width", 500),
            "updated_at": datetime.now()
        }

        await db.config.update_one(
            {"type": "about"},
            {"$set": multilang_about},
            upsert=True
        )

        return {"status": "success"}

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Lỗi cập nhật giới thiệu: {str(e)}"
        )


@router.get("/contact")
async def get_contact(db=Depends(get_db)):
    data = await db.config.find_one({"type": "contact"})

    if not data:
        return {}

    return serialize_mongo_doc(data)


@router.put("/contact")
async def update_contact(payload: dict = Body(...), db=Depends(get_db)):
    try:
        address_vi = payload.get("address", "").strip()
        description_vi = payload.get("description", "").strip()

        core_translator = GoogleTranslator(source="vi", target="en")

        try:
            translated_address = core_translator.translate(address_vi) if address_vi else ""
            translated_description = core_translator.translate(description_vi) if description_vi else ""
        except Exception:
            translated_address = address_vi
            translated_description = description_vi

        multilang_contact = {
            "type": "contact",
            "address": {
                "vi": address_vi,
                "en": translated_address
            },
            "description": {
                "vi": description_vi,
                "en": translated_description
            },
            "phone": payload.get("phone", ""),
            "email": payload.get("email", ""),
            "updated_at": datetime.now()
        }

        await db.config.update_one(
            {"type": "contact"},
            {"$set": multilang_contact},
            upsert=True
        )

        return {"status": "success"}

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Lỗi cập nhật liên hệ: {str(e)}"
        )


# =========================================================
# 11. QUẢN LÝ CỬA HÀNG OPERATOR
# =========================================================

@router.post("/products")
async def create_product(payload: dict = Body(...), db=Depends(get_db)):
    try:
        image_public_id = get_payload_public_id(payload)

        product_doc = dict(payload)
        product_doc.pop("public_id", None)

        if image_public_id:
            product_doc["image_public_id"] = image_public_id

        product_doc["price"] = to_float(product_doc.get("price"), 0.0)
        product_doc["created_at"] = datetime.now()
        product_doc["updated_at"] = datetime.now()

        result = await db.products.insert_one(product_doc)

        return {
            "status": "success",
            "id": str(result.inserted_id)
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Lỗi tạo sản phẩm: {str(e)}"
        )


@router.put("/products/{prod_id}")
async def update_product(prod_id: str, payload: dict = Body(...), db=Depends(get_db)):
    try:
        old_product = await db.products.find_one({"_id": to_object_id(prod_id, "Product ID")})

        if not old_product:
            raise HTTPException(status_code=404, detail="Không tìm thấy sản phẩm cần sửa.")

        update_doc = dict(payload)

        old_public_id = old_product.get("image_public_id", "")
        new_public_id = get_payload_public_id(update_doc)

        update_doc.pop("public_id", None)

        if "image_url" in update_doc and not update_doc.get("image_url"):
            if old_public_id:
                await delete_cloudinary_image_safely(old_public_id)
            update_doc["image_public_id"] = ""

        elif new_public_id and old_public_id and new_public_id != old_public_id:
            await delete_cloudinary_image_safely(old_public_id)
            update_doc["image_public_id"] = new_public_id

        elif new_public_id:
            update_doc["image_public_id"] = new_public_id

        if "price" in update_doc:
            update_doc["price"] = to_float(update_doc.get("price"), 0.0)

        update_doc["updated_at"] = datetime.now()

        await db.products.update_one(
            {"_id": old_product["_id"]},
            {"$set": update_doc}
        )

        return {"status": "success"}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Lỗi sửa sản phẩm: {str(e)}"
        )


@router.delete("/products/{prod_id}")
async def delete_product(prod_id: str, db=Depends(get_db)):
    try:
        product = await db.products.find_one({"_id": to_object_id(prod_id, "Product ID")})

        if not product:
            raise HTTPException(status_code=404, detail="Không tìm thấy sản phẩm cần xóa.")

        await delete_cloudinary_image_safely(product.get("image_public_id", ""))

        await db.products.delete_one({"_id": product["_id"]})

        return {"status": "success"}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Lỗi xóa sản phẩm: {str(e)}"
        )