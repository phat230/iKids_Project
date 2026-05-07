from fastapi import APIRouter, Depends, HTTPException, File, UploadFile, Form, Body
from core.database import get_db
from .schemas import PurchaseRequest, DepositRequest, ContactMessageCreate
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
    verify_otp_and_reset_password_service
)

# KHỞI TẠO DUY NHẤT 1 ROUTER (Không để prefix ở đây vì đã để ở main.py)
router = APIRouter()

# --- 1. CỬA HÀNG HỌC LIỆU ---
@router.get("/products")
async def api_get_products():
    return await get_store_products_service()

@router.post("/products/purchase")
async def api_purchase_product(req: PurchaseRequest, db = Depends(get_db)):
    result = await purchase_product_service(db, req.user_id, req.product_id)
    if result["status"] == "failed":
        raise HTTPException(status_code=400, detail=result["message"])
    return result

# --- 2. QUẢN LÝ TÀI CHÍNH ---
@router.post("/account/deposit")
async def api_deposit_money(req: DepositRequest, db = Depends(get_db)):
    return await deposit_money_service(db, req.user_id, req.amount)

@router.get("/gamification/profile/{student_id}")
async def get_account_profile(student_id: str, db = Depends(get_db)):
    profile = await db.gamification_profiles.find_one({"student_id": student_id})
    if not profile:
        return {"student_id": student_id, "balance": 0.0, "rank_level": "Beginner"}
    profile["_id"] = str(profile["_id"])
    return profile

# --- 3. GÓC KỶ NIỆM ---
@router.get("/memories")
async def api_get_memories(db = Depends(get_db)):
    return await get_class_memories(db)

@router.post("/memories/{memory_id}/like")
async def api_like_memory(memory_id: str, db = Depends(get_db)):
    return await like_memory_service(db, memory_id)

# --- 4. LIÊN HỆ & CẬP NHẬT HỒ SƠ ---
@router.post("/contact/submit")
async def api_submit_contact(request_data: ContactMessageCreate, db = Depends(get_db)):
    return await submit_contact_request(db, request_data)

@router.get("/contact/history/{parent_id}")
async def api_get_contact_history(parent_id: str, db = Depends(get_db)):
    return await get_contact_history(db, parent_id)

@router.post("/profile/update/{user_id}")
async def api_update_profile(
    user_id: str, 
    full_name: str = Form(None), 
    avatar_file: UploadFile = File(None), 
    db = Depends(get_db)
):
    return await update_account_profile_service(db, user_id, full_name, avatar_file)

# --- 5. QUÊN MẬT KHẨU (Gộp chung vào router này) ---
@router.post("/auth/forgot-password")
async def forgot_password(payload: dict = Body(...), db=Depends(get_db)):
    email = payload.get("email")
    return await send_forgot_password_email_service(db, email)

@router.post("/auth/verify-reset")
async def verify_reset(payload: dict = Body(...), db=Depends(get_db)):
    email = payload.get("email")
    otp = payload.get("otp")
    new_password = payload.get("new_password")
    return await verify_otp_and_reset_password_service(db, email, otp, new_password)