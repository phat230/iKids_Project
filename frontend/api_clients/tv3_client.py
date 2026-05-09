import requests
import streamlit as st

# Đảm bảo URL khớp với cấu hình FastAPI của bạn
API_URL = "http://localhost:8000/api/tv3"

# --- 1. HỆ THỐNG GAMIFICATION & PROFILE ---

def get_gamification_profile(user_id):
    """Lấy thông tin thực tế: Số dư (balance), EXP, và Rank."""
    try:
        res = requests.get(f"{API_URL}/gamification/profile/{user_id}")
        if res.status_code == 200:
            return res.json()
    except Exception:
        pass
    return {"balance": 0.0, "exp": 0, "rank": "Beginner", "full_name": "Người dùng"}

def update_profile(user_id, name=None, avatar_file=None):
    """Cập nhật thông tin cá nhân và ảnh đại diện."""
    data = {}
    if name: data["full_name"] = name
    
    files = {}
    if avatar_file:
        files = {"avatar_file": (avatar_file.name, avatar_file.getvalue(), avatar_file.type)}
    
    try:
        res = requests.post(f"{API_URL}/profile/update/{user_id}", data=data, files=files)
        if res.status_code == 200:
            return True, "Cập nhật hồ sơ thành công!"
        return False, "Không thể cập nhật hồ sơ."
    except Exception as e:
        return False, f"Lỗi: {str(e)}"

# --- 2. TÀI CHÍNH & CỬA HÀNG ---

def deposit_money(user_id, amount):
    """Gửi yêu cầu nạp tiền (Dùng để xác nhận gửi thông báo cho Admin/Webhook)."""
    payload = {"user_id": str(user_id), "amount": float(amount)}
    try:
        res = requests.post(f"{API_URL}/account/deposit", json=payload)
        if res.status_code == 200:
            return True, res.json().get("message", "Đã gửi thông báo nạp tiền.")
        return False, res.json().get("detail", "Giao dịch thất bại.")
    except Exception as e:
        return False, str(e)

@st.cache_data(ttl=300) 
def get_store_products():
    """Lấy danh sách sản phẩm (có cache để load nhanh hơn)."""
    try:
        res = requests.get(f"{API_URL}/products")
        return res.json() if res.status_code == 200 else []
    except Exception:
        return []

def purchase_product(user_id, product_id):
    """Xử lý mua sản phẩm bằng số dư ví."""
    payload = {"user_id": str(user_id), "product_id": int(product_id)}
    try:
        res = requests.post(f"{API_URL}/products/purchase", json=payload)
        if res.status_code == 200:
            return True, res.json()["message"]
        return False, res.json().get("detail", "Số dư không đủ hoặc sản phẩm hết hàng.")
    except Exception:
        return False, "Lỗi kết nối máy chủ."

# --- 3. LIÊN HỆ & BẢO MẬT (SỬA LỖI IMPORT TẠI ĐÂY) ---

def submit_contact_request(message_data):
    """
    SỬA LỖI: Đồng bộ tên hàm với file nap_tien.py.
    Gửi tin nhắn liên hệ/báo cáo sự cố nạp tiền.
    """
    # Xử lý nếu message_data là một object (như bạn gọi trong nap_tien.py)
    payload = {
        "sender_id": str(message_data.sender_id),
        "receiver_id": str(message_data.receiver_id),
        "subject": message_data.subject,
        "content": message_data.content
    }
    try:
        res = requests.post(f"{API_URL}/contact/submit", json=payload)
        if res.status_code == 200:
            return True, "Gửi yêu cầu thành công."
        return False, "Gửi yêu cầu thất bại."
    except Exception:
        return False, "Lỗi kết nối máy chủ."

def get_contact_history(user_id):
    """Lấy lịch sử tin nhắn."""
    try:
        res = requests.get(f"{API_URL}/contact/history/{user_id}")
        return res.json() if res.status_code == 200 else []
    except Exception:
        return []

# --- 4. XỬ LÝ MẬT KHẨU ---

def send_forgot_password_otp(email):
    try:
        res = requests.post(f"{API_URL}/auth/forgot-password", json={"email": email})
        return res.status_code == 200, res.json().get("message")
    except Exception:
        return False, "Không thể gửi OTP."

def verify_and_reset_password(email, otp, new_password):
    payload = {"email": email, "otp": otp, "new_password": new_password}
    try:
        res = requests.post(f"{API_URL}/auth/verify-reset", json=payload)
        return res.status_code == 200, res.json().get("message")
    except Exception:
        return False, "Xác thực thất bại."

# --- 5. GÓC KỶ NIỆM ---

@st.cache_data(ttl=600)
def get_memories():
    """Lấy ảnh kỷ niệm (Cache để tiết kiệm băng thông vì ảnh nặng)."""
    try:
        res = requests.get(f"{API_URL}/memories")
        return res.json() if res.status_code == 200 else []
    except Exception:
        return []

def like_memory(memory_id):
    try:
        res = requests.post(f"{API_URL}/memories/{memory_id}/like")
        return res.status_code == 200
    except Exception:
        return False