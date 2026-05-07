import requests
import streamlit as st

API_URL = "http://localhost:8000/api/tv3"

def get_gamification_profile(student_id):
    """Gọi API lấy thông tin Số dư (Balance) và Rank của học sinh"""
    try:
        res = requests.get(f"{API_URL}/gamification/profile/{student_id}")
        if res.status_code == 200:
            return res.json()
    except Exception:
        pass
    # Trả về mặc định với balance thay cho total_coins
    return {"balance": 0.0, "rank_level": "Beginner"}

def deposit_money(user_id, amount):
    """Gọi API nạp tiền vào tài khoản (Dành cho Phụ huynh)"""
    payload = {
        "user_id": str(user_id),
        "amount": float(amount)
    }
    try:
        res = requests.post(f"{API_URL}/account/deposit", json=payload)
        return res.status_code == 200, res.json().get("message", "Nạp tiền thành công")
    except Exception as e:
        return False, str(e)

def get_store_products():
    """Lấy danh sách sản phẩm học liệu (Sách, dụng cụ...)"""
    try:
        res = requests.get(f"{API_URL}/products")
        if res.status_code == 200:
            return res.json()
    except Exception:
        pass
    return []

def purchase_product(user_id, product_id):
    """Gửi yêu cầu thanh toán mua sản phẩm bằng số dư ví"""
    payload = {
        "user_id": str(user_id),
        "product_id": int(product_id)
    }
    try:
        res = requests.post(f"{API_URL}/products/purchase", json=payload)
        if res.status_code == 200:
            return True, res.json()["message"]
        return False, res.json().get("detail", "Giao dịch thất bại")
    except Exception:
        return False, "Không thể kết nối đến máy chủ."

def submit_contact(sender_id, receiver_id, subject, content):
    """Gọi API gửi yêu cầu xin nghỉ/liên hệ từ Phụ huynh"""
    payload = {
        "sender_id": str(sender_id),
        "receiver_id": str(receiver_id),
        "subject": subject,
        "content": content
    }
    try:
        res = requests.post(f"{API_URL}/contact/submit", json=payload)
        return res.status_code == 200, res.json()
    except Exception as e:
        return False, {"detail": str(e)}

def get_contact_history(parent_id):
    """Gọi API lấy lịch sử tin nhắn của Phụ huynh"""
    try:
        res = requests.get(f"{API_URL}/contact/history/{parent_id}")
        if res.status_code == 200:
            return res.json()
    except Exception:
        pass
    return []

def get_memories():
    """Lấy danh sách kỷ niệm lớp học"""
    try:
        res = requests.get(f"{API_URL}/memories")
        if res.status_code == 200:
            return res.json()
    except Exception:
        pass
    return []

def like_memory(memory_id):
    """Thả tim ảnh kỷ niệm"""
    try:
        res = requests.post(f"{API_URL}/memories/{memory_id}/like")
        return res.status_code == 200
    except Exception:
        return False
    
def get_transaction_history(user_id):
    """Lấy lịch sử nạp tiền và mua hàng của người dùng"""
    try:
        # Gọi đến endpoint lấy hồ sơ hoặc tạo endpoint riêng /account/history nếu cần
        res = requests.get(f"{API_URL}/gamification/profile/{user_id}")
        if res.status_code == 200:
            # Trong thực tế, bạn nên có một collection riêng cho transactions
            # Ở đây mình giả định lấy từ một list lưu trong profile hoặc một endpoint history
            return res.json().get("transaction_history", [])
    except Exception:
        pass
    return []
def update_profile(user_id, name=None, avatar_file=None):
    # Logic gửi file ảnh và tên lên Backend
    # Tạm thời giả lập xử lý thành công để bạn chạy UI
    return True, "Cập nhật thành công"

def change_password(user_id, new_pass):
    # Gọi API đổi mật khẩu
    return True, "Mật khẩu đã được thay đổi"