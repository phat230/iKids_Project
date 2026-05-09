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

# --- WEBHOOK SEPAY: NẠP TIỀN TỰ ĐỘNG (BỔ SUNG MỚI) ---
@router.post("/webhook/sepay")
async def sepay_webhook(request: Request, db = Depends(get_db)):
    """
    Cổng tiếp nhận dữ liệu từ SePay khi có biến động số dư Vietcombank thật.
    Dành cho gói miễn phí để test luồng thực tế.
    """
    try:
        data = await request.json()
        
        # Lấy nội dung chuyển khoản và số tiền thực nhận
        content = data.get("content", "")  
        amount = float(data.get("transferAmount", 0))
        
        # Phân tích nội dung: "IKIDS NAP <6 ký tự cuối ID>"
        if "IKIDS NAP" in content.upper():
            user_suffix = content.upper().split("IKIDS NAP")[-1].strip()
            
            # Tìm người dùng trong DB có ID kết thúc bằng chuỗi này
            user = await db.users.find_one({"_id": {"$regex": f"{user_suffix}$"}})
            
            if user:
                user_id = str(user["_id"])
                # Gọi service nạp tiền thực sự vào ví
                await deposit_money_service(db, user_id, amount)
                
                # Lưu vào lịch sử nạp tiền tự động để đối soát
                await db.deposit_history.insert_one({
                    "user_id": user_id,
                    "amount": amount,
                    "content": content,
                    "type": "sepay_auto",
                    "created_at": datetime.now()
                })
                return {"status": "success", "message": "Nạp tiền tự động thành công"}
        
        return {"status": "ignored", "message": "Nội dung không hợp lệ"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

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