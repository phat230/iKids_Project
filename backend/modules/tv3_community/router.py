# backend/modules/tv3_community/router.py
from fastapi import APIRouter, Depends, HTTPException, File, UploadFile, Form, Body, Request
from core.database import get_db
from .schemas import PurchaseRequest, DepositRequest, ContactMessageCreate
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

router = APIRouter()

# --- 1. CỬA HÀNG ---
@router.get("/products")
async def api_get_products():
    return await get_store_products_service()

@router.post("/products/purchase")
async def api_purchase_product(req: PurchaseRequest, db = Depends(get_db)):
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

# --- WEBHOOK VIETQR.IO (PAYOS): TỰ ĐỘNG CỘNG TIỀN ---
@router.post("/webhook/payos")
async def payos_webhook(request: Request, db = Depends(get_db)):
    """
    Cổng tiếp nhận dữ liệu từ PayOS (VietQR.io) khi có giao dịch chuyển khoản thành công.
    """
    try:
        body = await request.json()
        
        # PayOS gửi dữ liệu giao dịch trong trường 'data'
        data = body.get("data", body) 
        
        # 1. Lấy thông tin nội dung và số tiền
        # PayOS dùng 'description' thay cho 'content'
        description = data.get("description", "").upper()
        amount = float(data.get("amount", 0))
        
        # Lấy mã giao dịch để tránh xử lý trùng (Idempotency)
        reference = data.get("reference") or data.get("paymentLinkId")

        # 2. Kiểm tra cú pháp: "IKIDS NAP <6 ký tự cuối ID>"
        if "IKIDS NAP" in description:
            user_suffix = description.split("IKIDS NAP")[-1].strip()
            
            # 3. Tìm người dùng trong DB có ID kết thúc bằng chuỗi này
            user = await db.users.find_one({"_id": {"$regex": f"{user_suffix}$"}})
            
            if user:
                user_id = str(user["_id"])
                
                # Kiểm tra xem mã giao dịch này đã được xử lý chưa
                already_processed = await db.deposit_history.find_one({"reference": reference})
                if already_processed:
                    return {"status": "success", "message": "Giao dịch đã được xử lý trước đó."}

                # 4. TỰ ĐỘNG GỌI SERVICE CỘNG TIỀN
                await deposit_money_service(db, user_id, amount)
                
                # Lưu vào lịch sử nạp tiền tự động
                await db.deposit_history.insert_one({
                    "user_id": user_id,
                    "amount": amount,
                    "content": description,
                    "reference": reference,
                    "type": "payos_auto",
                    "created_at": datetime.now()
                })
                
                print(f"✅ [PayOS] Đã nạp {amount:,.0f} VNĐ cho User: {user_id}")
                return {"status": "success", "message": "Nạp tiền tự động thành công"}
        
        return {"status": "ignored", "message": "Nội dung không hợp lệ hoặc không phải lệnh nạp tiền"}
    except Exception as e:
        print(f"❌ Webhook Error: {str(e)}")
        return {"status": "error", "message": "Lỗi xử lý Webhook"}

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

# --- 3. KỶ NIỆM ---
@router.get("/memories")
async def api_get_memories(db = Depends(get_db)):
    return await get_class_memories(db)

@router.post("/memories/{memory_id}/like")
async def api_like_memory(memory_id: str, db = Depends(get_db)):
    return await like_memory_service(db, memory_id)

# --- 4. LIÊN HỆ & AUTH ---
@router.post("/contact/submit")
async def api_submit_contact(request_data: ContactMessageCreate, db = Depends(get_db)):
    return await submit_contact_request(db, request_data)

@router.post("/profile/update/{user_id}")
async def api_update_profile(user_id: str, full_name: str = Form(None), avatar_file: UploadFile = File(None), db = Depends(get_db)):
    return await update_account_profile_service(db, user_id, full_name, avatar_file)

@router.post("/auth/forgot-password")
async def forgot_password(payload: dict = Body(...), db=Depends(get_db)):
    return await send_forgot_password_email_service(db, payload.get("email"))

@router.post("/auth/verify-reset")
async def verify_reset(payload: dict = Body(...), db=Depends(get_db)):
    return await verify_otp_and_reset_password_service(db, payload.get("email"), payload.get("otp"), payload.get("new_password"))

# --- 5. GAMIFICATION AWARD ---
@router.post("/gamification/award-exp")
async def api_award_exp(payload: dict = Body(...), db = Depends(get_db)):
    student_id = payload.get("student_id")
    action = payload.get("action")
    amount = calculate_exp_reward(action)
    if amount <= 0: raise HTTPException(status_code=400, detail="Hành động không hợp lệ.")
    return await award_exp_service(db, student_id, amount, action)