# backend/modules/tv3_community/router.py
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

# --- 3. QUẢN LÝ SỰ CỐ NẠP TIỀN (PHẦN MỚI TÁCH) ---

@router.get("/admin/deposit-issues")
async def api_get_deposit_issues(db = Depends(get_db)):
    """API cho Admin lấy danh sách sự cố nạp tiền đang chờ duyệt (status=pending)"""
    cursor = db.deposit_issues.find({"status": "pending"}).sort("created_at", -1)
    issues = []
    async for doc in cursor:
        doc["id"] = str(doc["_id"])
        del doc["_id"]
        issues.append(doc)
    return issues

@router.post("/admin/resolve-deposit/{issue_id}")
async def api_resolve_deposit_issue(issue_id: str, db = Depends(get_db)):
    try:
        # 1. Tìm thông tin sự cố
        issue = await db.deposit_issues.find_one({"_id": ObjectId(issue_id)})
        if not issue:
            raise HTTPException(status_code=404, detail="Không tìm thấy yêu cầu.")
        
        user_id = issue.get("sender_id")
        
        # 2. Ép kiểu dữ liệu nghiêm ngặt để đảm bảo phép cộng tiền thực hiện được ($inc)
        try:
            # Lấy amount từ DB, nếu là string "50000" nó sẽ chuyển thành số 50000.0
            amount = float(issue.get("amount", 0))
        except (ValueError, TypeError):
            amount = 0.0

        if amount <= 0:
            raise HTTPException(status_code=400, detail=f"Số tiền không hợp lệ: {amount}")

        # 3. Thực hiện cộng tiền vào ví người dùng thông qua service
        deposit_res = await deposit_money_service(db, user_id, amount)
        if deposit_res["status"] == "failed":
            raise HTTPException(status_code=400, detail="Không thể cập nhật số dư tài khoản.")

        # 4. Cập nhật trạng thái sự cố thành 'resolved' để ẩn khỏi danh sách Admin
        result = await db.deposit_issues.update_one(
            {"_id": ObjectId(issue_id)},
            {"$set": {
                "status": "resolved", 
                "resolved_at": datetime.now(),
                "admin_note": f"Đã duyệt thủ công số tiền {amount}"
            }}
        )

        if result.modified_count > 0:
            return {"status": "success", "message": f"Đã cộng {amount:,.0f} VNĐ thành công."}
        else:
            return {"status": "failed", "message": "Không thể cập nhật trạng thái đơn."}

    except Exception as e:
        # Trả về lỗi chi tiết để bạn dễ debug nếu vẫn chưa chạy được
        raise HTTPException(status_code=400, detail=f"Lỗi xử lý: {str(e)}")
# --- 4. WEBHOOK VIETQR.IO (PAYOS) ---
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
                    return {"status": "success", "message": "Giao dịch đã được xử lý trước đó."}

                await deposit_money_service(db, user_id, amount)
                await db.deposit_history.insert_one({
                    "user_id": user_id,
                    "amount": amount,
                    "content": description,
                    "reference": reference,
                    "type": "payos_auto",
                    "created_at": datetime.now()
                })
                return {"status": "success", "message": "Nạp tiền tự động thành công"}
        return {"status": "ignored", "message": "Nội dung không hợp lệ"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

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

@router.post("/profile/update/{user_id}")
async def api_update_profile(user_id: str, full_name: str = Form(None), avatar_file: UploadFile = File(None), db = Depends(get_db)):
    return await update_account_profile_service(db, user_id, full_name, avatar_file)

@router.post("/auth/forgot-password")
async def forgot_password(payload: dict = Body(...), db=Depends(get_db)):
    return await send_forgot_password_email_service(db, payload.get("email"))

@router.post("/auth/verify-reset")
async def verify_reset(payload: dict = Body(...), db=Depends(get_db)):
    return await verify_otp_and_reset_password_service(db, payload.get("email"), payload.get("otp"), payload.get("new_password"))

# --- 8. GAMIFICATION AWARD ---
@router.post("/gamification/award-exp")
async def api_award_exp(payload: dict = Body(...), db = Depends(get_db)):
    student_id = payload.get("student_id")
    action = payload.get("action")
    amount = calculate_exp_reward(action)
    if amount <= 0: raise HTTPException(status_code=400, detail="Hành động không hợp lệ.")
    return await award_exp_service(db, student_id, amount, action)
# --- 9. QUẢN LÝ CON & PHÊ DUYỆT (PHẦN MỚI CẬP NHẬT) ---

@router.get("/parent/my-children")
async def get_my_children(
    db = Depends(get_db), 
    current_user: dict = Depends(get_current_user)
):
    parent = await db.users.find_one({"_id": ObjectId(current_user["user_id"])})
    if not parent or not parent.get("student_ids_ref"):
        return []
    
    # Lấy thông tin chi tiết của tất cả các con dựa trên list ID
    child_ids = [ObjectId(sid) for sid in parent["student_ids_ref"]]
    children = await db.users.find({"_id": {"$in": child_ids}}).to_list(length=20)
    
    for c in children:
        c["id"] = str(c["_id"])
        del c["_id"]
        if "password" in c:
            del c["password"]
    return children

# --- QUẢN LÝ VÍ CỦA CON ---
@router.post("/parent/transfer-to-child")
async def transfer_to_child(payload: dict = Body(...), db=Depends(get_db), current_user: dict = Depends(get_current_user)):
    child_id = payload.get("child_id")
    amount = float(payload.get("amount", 0))
    parent_id = current_user["user_id"]
    
    if amount <= 0: return {"status": "failed", "message": "Số tiền không hợp lệ."}
    
    parent = await db.users.find_one({"_id": ObjectId(parent_id)})
    if parent.get("balance", 0) < amount:
        return {"status": "failed", "message": "Số dư ví phụ huynh không đủ."}
        
    # Trừ tiền mẹ, cộng tiền con
    await db.users.update_one({"_id": ObjectId(parent_id)}, {"$inc": {"balance": -amount}})
    await db.users.update_one({"_id": ObjectId(child_id)}, {"$inc": {"balance": amount}})
    return {"status": "success", "message": "Đã gửi tiền cho con."}

@router.post("/parent/withdraw-from-child")
async def withdraw_from_child(payload: dict = Body(...), db=Depends(get_db), current_user: dict = Depends(get_current_user)):
    child_id = payload.get("child_id")
    amount = float(payload.get("amount", 0))
    parent_id = current_user["user_id"]
    
    if amount <= 0: return {"status": "failed", "message": "Số tiền không hợp lệ."}
    
    child = await db.users.find_one({"_id": ObjectId(child_id)})
    if child.get("balance", 0) < amount:
        return {"status": "failed", "message": "Ví của bé không đủ số dư này."}
        
    # Trừ tiền con, cộng lại cho mẹ
    await db.users.update_one({"_id": ObjectId(child_id)}, {"$inc": {"balance": -amount}})
    await db.users.update_one({"_id": ObjectId(parent_id)}, {"$inc": {"balance": amount}})
    return {"status": "success", "message": "Đã rút tiền từ ví con."}

# --- CỬA HÀNG: HỌC SINH & PHỤ HUYNH ---
@router.post("/store/request-purchase")
async def student_request_purchase(req: dict = Body(...), db = Depends(get_db)):
    """API cho Học sinh gửi yêu cầu mua đồ"""
    # Lấy thông tin tài khoản học sinh
    student = await db.users.find_one({"_id": ObjectId(req["student_id"])})
    child_name = student.get("name", "Bé") if student else "Bé"

    request_doc = {
        "student_id": req["student_id"],
        "parent_id": req.get("parent_id"), # Có thể bỏ qua nếu tự dò từ DB, nhưng để tạm theo payload
        "child_name": child_name, # Thêm tên bé để frontend hiển thị
        "product_id": req["product_id"],
        "product_name": req["product_name"],
        "price": float(req["price"]),
        "status": "pending",
        "created_at": datetime.now()
    }
    
    # Tìm parent_id nếu frontend không gửi
    if not request_doc["parent_id"]:
        parent = await db.users.find_one({"student_ids_ref": req["student_id"]})
        if parent:
            request_doc["parent_id"] = str(parent["_id"])

    await db.purchase_requests.insert_one(request_doc)
    return {"status": "success", "message": "Đã gửi yêu cầu mua tới Phụ huynh!"}

@router.get("/parent/purchase-requests")
async def get_parent_purchase_requests(db = Depends(get_db), current_user: dict = Depends(get_current_user)):
    """API lấy danh sách các đơn hàng con đang xin mua"""
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
    """API Phụ huynh duyệt hoặc từ chối đơn hàng"""
    action = payload.get("action")
    req = await db.purchase_requests.find_one({"_id": ObjectId(request_id)})
    
    if not req:
        raise HTTPException(status_code=404, detail="Không tìm thấy yêu cầu.")
        
    if action == "reject":
        await db.purchase_requests.update_one({"_id": ObjectId(request_id)}, {"$set": {"status": "rejected"}})
        return {"message": "Đã từ chối yêu cầu."}
    
    if action == "approve":
        # 1. Trừ tiền ví con (Ví của con đã được mẹ nạp trước đó)
        child = await db.users.find_one({"_id": ObjectId(req["student_id"])})
        if child.get("balance", 0) < req["price"]:
            return {"status": "failed", "message": "Ví của bé không đủ tiền. Vui lòng nạp thêm cho bé!"}
        
        # 2. Trừ tiền con
        await db.users.update_one({"_id": ObjectId(req["student_id"])}, {"$inc": {"balance": -req["price"]}})
        
        # 3. Cập nhật trạng thái và ghi log mua hàng (nếu có)
        await db.purchase_requests.update_one({"_id": ObjectId(request_id)}, {"$set": {"status": "approved"}})
        
        return {"status": "success", "message": "Đã duyệt mua đồ cho con!"}