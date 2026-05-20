from fastapi import APIRouter, Depends, HTTPException
from core.database import get_db
from core.security import get_current_user
from bson import ObjectId
from datetime import datetime

router = APIRouter(prefix="/api/finance", tags=["Finance"])


def check_operator_admin(user):
    if user["role"] not in ["operator", "admin"]:
        raise HTTPException(status_code=403, detail="Không có quyền truy cập")


@router.get("/wallet-transactions")
async def get_wallet_transactions(
    db=Depends(get_db),
    current_user=Depends(get_current_user)
):
    check_operator_admin(current_user)

    cursor = db.transactions.find({
        "category": "wallet"
    }).sort("created_at", -1)

    data = []
    async for doc in cursor:
        doc["id"] = str(doc["_id"])
        del doc["_id"]
        data.append(doc)

    return data


@router.get("/purchase-transactions")
async def get_purchase_transactions(
    db=Depends(get_db),
    current_user=Depends(get_current_user)
):
    check_operator_admin(current_user)

    cursor = db.transactions.find({
        "category": "purchase"
    }).sort("created_at", -1)

    data = []
    async for doc in cursor:
        doc["id"] = str(doc["_id"])
        del doc["_id"]
        data.append(doc)

    return data


@router.put("/transactions/{transaction_id}")
async def update_transaction(
    transaction_id: str,
    payload: dict,
    db=Depends(get_db),
    current_user=Depends(get_current_user)
):
    check_operator_admin(current_user)

    payload.pop("_id", None)
    payload.pop("id", None)
    payload["updated_at"] = datetime.now()

    result = await db.transactions.update_one(
        {"_id": ObjectId(transaction_id)},
        {"$set": payload}
    )

    if result.matched_count:
        return {"status": "success", "message": "Đã cập nhật giao dịch"}

    raise HTTPException(status_code=404, detail="Không tìm thấy giao dịch")


@router.delete("/transactions/{transaction_id}")
async def delete_transaction(
    transaction_id: str,
    db=Depends(get_db),
    current_user=Depends(get_current_user)
):
    check_operator_admin(current_user)

    result = await db.transactions.delete_one({
        "_id": ObjectId(transaction_id)
    })

    if result.deleted_count:
        return {"status": "success", "message": "Đã xóa giao dịch"}

    raise HTTPException(status_code=404, detail="Không tìm thấy giao dịch")