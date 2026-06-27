# backend/modules/tv3_community/router.py
import os
import shutil
from fastapi import APIRouter, Depends, HTTPException, File, UploadFile, Form, Body, Request
from core.database import get_db
from .schemas import PurchaseRequest, DepositRequest, ContactMessageCreate
from core.security import get_current_user
from .rule_engine import calculate_exp_reward 
from .services import (
    get_store_products_service, 
    deposit_money_service, 
    purchase_product_service, 
    get_class_memories, 
    like_memory_service,
    submit_contact_request, 
    get_contact_history,
    update_account_profile_service,
    send_forgot_password_email_service,
    verify_otp_and_reset_password_service,
    award_exp_service
)
from bson import ObjectId
from datetime import datetime
from deep_translator import GoogleTranslator
import uuid
import asyncio
import cloudinary.uploader
from core.cloudinary_config import check_cloudinary_config

router = APIRouter()
translator = GoogleTranslator(source='vi', target='en')
# --- 1. CỬA HÀNG (DÀNH CHO NGƯỜI DÙNG) ---
@router.get("/products")
async def api_get_products(db = Depends(get_db)):
    """Lấy danh sách sản phẩm từ MongoDB"""
    return await get_store_products_service(db)

@router.post("/products/purchase")
async def api_purchase_product(req: PurchaseRequest, db = Depends(get_db)):
    """Thực hiện mua hàng trực tiếp"""
    result = await purchase_product_service(db, req.user_id, req.product_id)
    if result["status"] == "failed":
        raise HTTPException(status_code=400, detail=result["message"])
    return result

# --- 2. TÀI CHÍNH & PROFILE ---

@router.post("/account/deposit")
async def api_deposit_money(req: DepositRequest, db = Depends(get_db)):
    result = await deposit_money_service(db, req.user_id, req.amount)
    if result["status"] == "failed":
        raise HTTPException(status_code=404, detail=result["message"])
    return result

# --- 3. QUẢN LÝ SỰ CỐ NẠP TIỀN (ADMIN) ---

@router.get("/admin/deposit-issues")
async def api_get_deposit_issues(db = Depends(get_db)):
    """Admin lấy danh sách sự cố nạp tiền đang chờ duyệt"""
    cursor = db.deposit_issues.find({"status": "pending"}).sort("created_at", -1)
    issues = []
    async for doc in cursor:
        doc["id"] = str(doc["_id"])
        del doc["_id"]
        issues.append(doc)
    return issues

@router.post("/admin/resolve-deposit/{issue_id}")
async def api_resolve_deposit_issue(issue_id: str, db = Depends(get_db)):
    """Admin phê duyệt nạp tiền thủ công"""
    try:
        issue = await db.deposit_issues.find_one({"_id": ObjectId(issue_id)})
        if not issue:
            raise HTTPException(status_code=404, detail="Không tìm thấy yêu cầu.")
        
        user_id = issue.get("sender_id")
        try:
            amount = float(issue.get("amount", 0))
        except (ValueError, TypeError):
            amount = 0.0

        if amount <= 0:
            raise HTTPException(status_code=400, detail=f"Số tiền không hợp lệ")

        deposit_res = await deposit_money_service(db, user_id, amount)
        if deposit_res["status"] == "failed":
            raise HTTPException(status_code=400, detail="Lỗi cập nhật số dư")

        await db.deposit_issues.update_one(
            {"_id": ObjectId(issue_id)},
            {"$set": {
                "status": "resolved", 
                "resolved_at": datetime.now(),
                "admin_note": f"Đã duyệt thủ công số tiền {amount}"
            }}
        )
        return {"status": "success", "message": f"Đã cộng {amount:,.0f} VNĐ thành công."}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Lỗi: {str(e)}")

# --- 4. WEBHOOK PAYOS ---

@router.post("/webhook/payos")
async def payos_webhook(request: Request, db = Depends(get_db)):
    try:
        body = await request.json()
        data = body.get("data", body) 
        description = data.get("description", "").upper()
        amount = float(data.get("amount", 0))
        reference = data.get("reference") or data.get("paymentLinkId")

        if "IKIDS NAP" in description:
            user_suffix = description.split("IKIDS NAP")[-1].strip()
            user = await db.users.find_one({"_id": {"$regex": f"{user_suffix}$"}})
            
            if user:
                user_id = str(user["_id"])
                already_processed = await db.deposit_history.find_one({"reference": reference})
                if already_processed:
                    return {"status": "success"}

                await deposit_money_service(db, user_id, amount)
                await db.deposit_history.insert_one({
                    "user_id": user_id, "amount": amount, "reference": reference,
                    "type": "payos_auto", "created_at": datetime.now()
                })
                return {"status": "success"}
        return {"status": "ignored"}
    except Exception:
        return {"status": "error"}

# --- 5. GAMIFICATION & PROFILE ---

@router.get("/gamification/profile/{user_id}")
async def get_account_profile(user_id: str, db = Depends(get_db)):
    try:
        user = await db.users.find_one({"_id": ObjectId(user_id)})
        if not user:
            return {"user_id": user_id, "balance": 0.0, "exp": 0, "rank": "Beginner"}
        return {
            "user_id": str(user["_id"]),
            "full_name": user.get("full_name", user.get("name", "N/A")),
            "balance": user.get("balance", 0.0),
            "exp": user.get("exp", 0),
            "rank": user.get("rank", "Beginner"),
            "avatar_url": user.get("avatar_url", "")
        }
    except Exception:
        raise HTTPException(status_code=400, detail="ID không hợp lệ.")

# --- 6. KỶ NIỆM ---

@router.get("/memories")
async def api_get_memories(db = Depends(get_db)):
    return await get_class_memories(db)

@router.post("/memories/{memory_id}/like")
async def api_like_memory(memory_id: str, db = Depends(get_db)):
    return await like_memory_service(db, memory_id)

# --- 7. LIÊN HỆ & AUTH ---

@router.post("/contact/submit")
async def api_submit_contact(request_data: ContactMessageCreate, db = Depends(get_db)):
    return await submit_contact_request(db, request_data)

@router.get("/contact/history/{user_id}")
async def api_get_contact_history(user_id: str, db = Depends(get_db)):
    return await get_contact_history(db, user_id)

@router.post("/profile/update/{user_id}")
async def api_update_profile(user_id: str, full_name: str = Form(None), avatar_file: UploadFile = File(None), db = Depends(get_db)):
    return await update_account_profile_service(db, user_id, full_name, avatar_file)

@router.post("/auth/forgot-password")
async def forgot_password(payload: dict = Body(...), db=Depends(get_db)):
    return await send_forgot_password_email_service(db, payload.get("email"))

@router.post("/auth/verify-reset")
async def verify_reset(payload: dict = Body(...), db=Depends(get_db)):
    return await verify_otp_and_reset_password_service(db, payload.get("email"), payload.get("otp"), payload.get("new_password"))

@router.post("/gamification/award-exp")
async def api_award_exp(payload: dict = Body(...), db = Depends(get_db)):
    student_id = payload.get("student_id")
    action = payload.get("action")
    amount = calculate_exp_reward(action)
    if amount <= 0: raise HTTPException(status_code=400, detail="Hành động không hợp lệ.")
    return await award_exp_service(db, student_id, amount, action)

# --- 8. QUẢN LÝ CON ---

@router.get("/parent/my-children")
async def get_my_children(db = Depends(get_db), current_user: dict = Depends(get_current_user)):
    parent = await db.users.find_one({"_id": ObjectId(current_user["user_id"])})
    if not parent or not parent.get("student_ids_ref"):
        return []
    child_ids = [ObjectId(sid) for sid in parent["student_ids_ref"]]
    children = await db.users.find({"_id": {"$in": child_ids}}).to_list(length=20)
    for c in children:
        c["id"] = str(c["_id"])
        del c["_id"]
        if "password" in c: del c["password"]
    return children

@router.post("/parent/transfer-to-child")
async def transfer_to_child(payload: dict = Body(...), db=Depends(get_db), current_user: dict = Depends(get_current_user)):
    child_id = payload.get("child_id")
    amount = float(payload.get("amount", 0))
    parent_id = current_user["user_id"]
    if amount <= 0: return {"status": "failed", "message": "Số tiền không hợp lệ."}
    parent = await db.users.find_one({"_id": ObjectId(parent_id)})
    if parent.get("balance", 0) < amount:
        return {"status": "failed", "message": "Số dư không đủ."}
    await db.users.update_one({"_id": ObjectId(parent_id)}, {"$inc": {"balance": -amount}})
    await db.users.update_one({"_id": ObjectId(child_id)}, {"$inc": {"balance": amount}})
    return {"status": "success", "message": "Đã gửi tiền cho con."}

@router.post("/parent/withdraw-from-child")
async def withdraw_from_child(payload: dict = Body(...), db=Depends(get_db), current_user: dict = Depends(get_current_user)):
    child_id = payload.get("child_id")
    amount = float(payload.get("amount", 0))
    parent_id = current_user["user_id"]
    child = await db.users.find_one({"_id": ObjectId(child_id)})
    if child.get("balance", 0) < amount:
        return {"status": "failed", "message": "Ví của bé không đủ số dư."}
    await db.users.update_one({"_id": ObjectId(child_id)}, {"$inc": {"balance": -amount}})
    await db.users.update_one({"_id": ObjectId(parent_id)}, {"$inc": {"balance": amount}})
    return {"status": "success", "message": "Đã rút tiền từ ví con."}

# --- 9. YÊU CẦU MUA HÀNG (HỌC SINH) ---

@router.post("/store/request-purchase")
async def student_request_purchase(req: dict = Body(...), db = Depends(get_db)):
    student = await db.users.find_one({"_id": ObjectId(req["student_id"])})
    child_name = student.get("name", "Bé") if student else "Bé"
    request_doc = {
        "student_id": req["student_id"],
        "parent_id": req.get("parent_id"),
        "child_name": child_name,
        "product_id": req["product_id"],
        "product_name": req["product_name"],
        "price": float(req["price"]),
        "status": "pending",
        "created_at": datetime.now()
    }
    if not request_doc["parent_id"]:
        parent = await db.users.find_one({"student_ids_ref": req["student_id"]})
        if parent: request_doc["parent_id"] = str(parent["_id"])
    await db.purchase_requests.insert_one(request_doc)
    return {"status": "success", "message": "Đã gửi yêu cầu mua tới Ba Mẹ!"}

@router.get("/parent/purchase-requests")
async def get_parent_purchase_requests(db = Depends(get_db), current_user: dict = Depends(get_current_user)):
    parent_id = current_user["user_id"]
    cursor = db.purchase_requests.find({"parent_id": parent_id, "status": "pending"})
    requests_list = []
    async for req in cursor:
        req["id"] = str(req["_id"])
        del req["_id"]
        requests_list.append(req)
    return requests_list

@router.post("/parent/approve-purchase/{request_id}")
async def parent_approve_purchase(request_id: str, payload: dict = Body(...), db = Depends(get_db)):
    action = payload.get("action")
    req = await db.purchase_requests.find_one({"_id": ObjectId(request_id)})
    if not req: raise HTTPException(status_code=404, detail="Không thấy yêu cầu")
    if action == "reject":
        await db.purchase_requests.update_one({"_id": ObjectId(request_id)}, {"$set": {"status": "rejected"}})
        return {"message": "Đã từ chối"}
    if action == "approve":
        child = await db.users.find_one({"_id": ObjectId(req["student_id"])})
        if child.get("balance", 0) < req["price"]:
            return {"status": "failed", "message": "Ví con không đủ tiền"}
        await db.users.update_one({"_id": ObjectId(req["student_id"])}, {"$inc": {"balance": -req["price"]}})
        await db.purchase_requests.update_one({"_id": ObjectId(request_id)}, {"$set": {"status": "approved"}})
        return {"status": "success"}
# --- 10. QUẢN LÝ NỘI DUNG TRANG CHỦ (CMS ĐA NGÔN NGỮ CHUẨN KIẾN TRÚC) ---

ALLOWED_IMAGE_TYPES = {
    "image/jpeg",
    "image/png",
    "image/webp",
    "image/gif"
}


async def delete_cloudinary_image_safely(public_id: str):
    """
    Xóa ảnh trên Cloudinary nếu có public_id.
    Không raise lỗi để tránh làm hỏng thao tác xóa bài viết/sản phẩm.
    """
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


def get_payload_public_id(payload: dict) -> str:
    """
    Hỗ trợ cả 2 tên:
    - image_public_id
    - public_id

    Vì API upload_image trả về public_id, frontend có thể gửi lên bằng 1 trong 2 tên.
    """
    return payload.get("image_public_id") or payload.get("public_id") or ""


@router.post("/upload_image")
async def upload_image_from_mobile(file: UploadFile = File(...)):
    """
    Upload ảnh lên Cloudinary.
    Không còn lưu vào static/uploads nữa.
    Dùng chung cho:
    - ảnh bài viết CMS
    - ảnh trang giới thiệu
    - ảnh sản phẩm cửa hàng
    """

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
async def get_all_posts(status: str = None, db = Depends(get_db)):
    query = {}

    if status:
        query["status"] = status

    cursor = db.posts.find(query).sort("date", -1)
    posts = []

    async for doc in cursor:
        doc["id"] = str(doc["_id"])
        del doc["_id"]
        posts.append(doc)

    return posts


@router.post("/posts")
async def create_new_post(payload: dict = Body(...), db = Depends(get_db)):
    """
    Tạo bài viết mới.
    Ảnh đã được upload qua /upload_image trước,
    API này chỉ lưu image_url và image_public_id vào MongoDB.
    """

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
async def update_post(post_id: str, payload: dict = Body(...), db = Depends(get_db)):
    """
    Sửa bài viết.
    Nếu đổi ảnh mới, hệ thống có thể xóa ảnh cũ trên Cloudinary nếu có image_public_id.
    """

    try:
        old_post = await db.posts.find_one({"_id": ObjectId(post_id)})

        if not old_post:
            raise HTTPException(
                status_code=404,
                detail="Không tìm thấy bài viết cần sửa."
            )

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

        # Nếu frontend gửi image_url rỗng nghĩa là muốn bỏ ảnh
        if "image_url" in payload and not payload.get("image_url"):
            if old_public_id:
                await delete_cloudinary_image_safely(old_public_id)
            new_public_id = ""

        # Nếu đổi sang ảnh Cloudinary mới thì xóa ảnh cũ
        elif new_public_id and old_public_id and new_public_id != old_public_id:
            await delete_cloudinary_image_safely(old_public_id)

        # Nếu không gửi public_id mới thì giữ public_id cũ
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
            {"_id": ObjectId(post_id)},
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
async def delete_post(post_id: str, db = Depends(get_db)):
    try:
        post = await db.posts.find_one({"_id": ObjectId(post_id)})

        if not post:
            raise HTTPException(
                status_code=404,
                detail="Không tìm thấy bài viết cần xóa."
            )

        await delete_cloudinary_image_safely(post.get("image_public_id", ""))

        await db.posts.delete_one({"_id": ObjectId(post_id)})

        return {"status": "success"}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Lỗi xóa bài viết: {str(e)}"
        )


@router.get("/about")
async def get_about(db = Depends(get_db)):
    data = await db.config.find_one({"type": "about"})

    if not data:
        return {}

    data["id"] = str(data["_id"])
    del data["_id"]

    return data


@router.put("/about")
async def update_about(payload: dict = Body(...), db = Depends(get_db)):
    """
    Lưu nội dung giới thiệu.
    images nên là danh sách URL Cloudinary.
    image_public_ids nên là danh sách public_id tương ứng.
    """

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
async def get_contact(db = Depends(get_db)):
    data = await db.config.find_one({"type": "contact"})

    if not data:
        return {}

    data["id"] = str(data["_id"])
    del data["_id"]

    return data


@router.put("/contact")
async def update_contact(payload: dict = Body(...), db = Depends(get_db)):
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


# --- 11. QUẢN LÝ CỬA HÀNG (OPERATOR) ---

@router.post("/products")
async def create_product(payload: dict = Body(...), db = Depends(get_db)):
    """
    Tạo sản phẩm cửa hàng.
    Nếu sản phẩm có ảnh, frontend gửi:
    {
        "image_url": "...",
        "image_public_id": "..."
    }
    """

    try:
        image_public_id = get_payload_public_id(payload)

        product_doc = dict(payload)
        product_doc.pop("public_id", None)

        if image_public_id:
            product_doc["image_public_id"] = image_public_id

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
async def update_product(prod_id: str, payload: dict = Body(...), db = Depends(get_db)):
    """
    Sửa sản phẩm.
    Nếu đổi ảnh mới, ảnh cũ trên Cloudinary sẽ được xóa nếu có image_public_id.
    """

    try:
        old_product = await db.products.find_one({"_id": ObjectId(prod_id)})

        if not old_product:
            raise HTTPException(
                status_code=404,
                detail="Không tìm thấy sản phẩm cần sửa."
            )

        update_doc = dict(payload)

        old_public_id = old_product.get("image_public_id", "")
        new_public_id = get_payload_public_id(update_doc)

        update_doc.pop("public_id", None)

        # Nếu frontend gửi image_url rỗng nghĩa là muốn xóa ảnh sản phẩm
        if "image_url" in update_doc and not update_doc.get("image_url"):
            if old_public_id:
                await delete_cloudinary_image_safely(old_public_id)
            update_doc["image_public_id"] = ""

        # Nếu đổi ảnh mới thì xóa ảnh cũ
        elif new_public_id and old_public_id and new_public_id != old_public_id:
            await delete_cloudinary_image_safely(old_public_id)
            update_doc["image_public_id"] = new_public_id

        elif new_public_id:
            update_doc["image_public_id"] = new_public_id

        update_doc["updated_at"] = datetime.now()

        await db.products.update_one(
            {"_id": ObjectId(prod_id)},
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
async def delete_product(prod_id: str, db = Depends(get_db)):
    """
    Xóa sản phẩm.
    Nếu sản phẩm có image_public_id thì xóa luôn ảnh trên Cloudinary.
    """

    try:
        product = await db.products.find_one({"_id": ObjectId(prod_id)})

        if not product:
            raise HTTPException(
                status_code=404,
                detail="Không tìm thấy sản phẩm cần xóa."
            )

        await delete_cloudinary_image_safely(product.get("image_public_id", ""))

        await db.products.delete_one({"_id": ObjectId(prod_id)})

        return {"status": "success"}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Lỗi xóa sản phẩm: {str(e)}"
        )