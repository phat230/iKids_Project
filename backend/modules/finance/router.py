from fastapi import APIRouter, Depends, HTTPException
from core.database import get_db
from core.security import get_current_user
from bson import ObjectId
from datetime import datetime

router = APIRouter(prefix="/api/finance", tags=["Finance"])


def only_admin_operator(user):
    if user["role"] not in ["admin", "operator"]:
        raise HTTPException(status_code=403, detail="Không có quyền truy cập")


def only_parent(user):
    if user["role"] != "parent":
        raise HTTPException(status_code=403, detail="Chỉ phụ huynh được xem")


def clean_doc(doc):
    doc["id"] = str(doc["_id"])
    del doc["_id"]
    return doc


async def get_parent_children(db, parent_id: str):
    parent = await db.users.find_one({"_id": ObjectId(parent_id)})

    if not parent:
        raise HTTPException(status_code=404, detail="Không tìm thấy phụ huynh")

    return parent.get("student_ids_ref", [])


async def build_parent_history(db, parent_id: str):
    student_ids = await get_parent_children(db, parent_id)
    data = []

    # ==========================================
    # 1. LỊCH SỬ NẠP / CHUYỂN / RÚT TIỀN
    # ==========================================
    wallet_query = {
        "$or": [
            {"parent_id": parent_id},
            {"user_id": parent_id},
            {"from_user_id": parent_id},
            {"to_user_id": {"$in": student_ids}},
            {"student_id": {"$in": student_ids}},
            {"child_id": {"$in": student_ids}},
        ]
    }

    for collection_name in [
        "transactions",
        "coin_transactions",
        "wallet_transactions"
    ]:
        cursor = db[collection_name].find(wallet_query).sort("created_at", -1)

        async for doc in cursor:
            doc["group"] = "Ví tiền"
            doc["source_collection"] = collection_name
            data.append(clean_doc(doc))

    # ==========================================
    # 2. LỊCH SỬ PHỤ HUYNH MUA ĐỒ / TẶNG CON
    # ==========================================
    parent_purchase_query = {
        "$or": [
            {"parent_id": parent_id},
            {"buyer_id": parent_id},
            {"user_id": parent_id},
            {"student_id": {"$in": student_ids}},
            {"child_id": {"$in": student_ids}},
        ]
    }

    for collection_name in [
        "orders",
        "purchases",
        "store_orders"
    ]:
        cursor = db[collection_name].find(parent_purchase_query).sort("created_at", -1)

        async for doc in cursor:
            doc["group"] = "Mua đồ"
            doc["source_collection"] = collection_name
            data.append(clean_doc(doc))

    # ==========================================
    # 3. LỊCH SỬ CON TỰ MUA ĐỒ
    # ==========================================
    child_purchase_query = {
        "$or": [
            {"student_id": {"$in": student_ids}},
            {"buyer_id": {"$in": student_ids}},
            {"user_id": {"$in": student_ids}},
        ]
    }

    for collection_name in [
        "student_orders",
        "orders",
        "purchases",
        "store_orders"
    ]:
        cursor = db[collection_name].find(child_purchase_query).sort("created_at", -1)

        async for doc in cursor:
            doc["group"] = "Con tự mua"
            doc["source_collection"] = collection_name
            data.append(clean_doc(doc))

    return data


@router.get("/parent/history")
async def parent_transaction_history(
    db=Depends(get_db),
    current_user=Depends(get_current_user)
):
    only_parent(current_user)

    parent_id = current_user["user_id"]

    return await build_parent_history(db, parent_id)


@router.get("/admin/all-history")
async def admin_all_transaction_history(
    db=Depends(get_db),
    current_user=Depends(get_current_user)
):
    only_admin_operator(current_user)

    parents = await db.users.find({"role": "parent"}).to_list(length=500)

    result = []

    for parent in parents:
        parent_id = str(parent["_id"])
        history = await build_parent_history(db, parent_id)

        for item in history:
            item["parent_id"] = parent_id
            item["parent_name"] = parent.get("name", "")
            item["parent_email"] = parent.get("email", "")

        result.extend(history)

    # Sắp xếp mới nhất lên đầu nếu có created_at
    try:
        result = sorted(
            result,
            key=lambda x: x.get("created_at", datetime.min),
            reverse=True
        )
    except Exception:
        pass

    return result


@router.put("/transactions/{transaction_id}")
async def update_transaction(
    transaction_id: str,
    payload: dict,
    db=Depends(get_db),
    current_user=Depends(get_current_user)
):
    only_admin_operator(current_user)

    payload.pop("_id", None)
    payload.pop("id", None)
    payload["updated_at"] = datetime.now()

    for collection_name in [
        "transactions",
        "coin_transactions",
        "wallet_transactions",
        "orders",
        "purchases",
        "store_orders",
        "student_orders"
    ]:
        result = await db[collection_name].update_one(
            {"_id": ObjectId(transaction_id)},
            {"$set": payload}
        )

        if result.matched_count:
            return {
                "status": "success",
                "message": "Đã cập nhật giao dịch",
                "source_collection": collection_name
            }

    raise HTTPException(status_code=404, detail="Không tìm thấy giao dịch")


@router.delete("/transactions/{transaction_id}")
async def delete_transaction(
    transaction_id: str,
    db=Depends(get_db),
    current_user=Depends(get_current_user)
):
    only_admin_operator(current_user)

    for collection_name in [
        "transactions",
        "coin_transactions",
        "wallet_transactions",
        "orders",
        "purchases",
        "store_orders",
        "student_orders"
    ]:
        result = await db[collection_name].delete_one({
            "_id": ObjectId(transaction_id)
        })

        if result.deleted_count:
            return {
                "status": "success",
                "message": "Đã xóa giao dịch",
                "source_collection": collection_name
            }

    raise HTTPException(status_code=404, detail="Không tìm thấy giao dịch")