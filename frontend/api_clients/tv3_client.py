import requests
import streamlit as st

# Đảm bảo URL khớp với cấu hình FastAPI của bạn
API_URL = "http://localhost:8000/api/tv3"

def get_gamification_profile(user_id):
    """
    Lấy thông tin thực tế: Số dư (balance), EXP, và Rank từ collection users[cite: 166].
    Dữ liệu này được dùng để hiển thị trên Dashboard học sinh và phụ huynh[cite: 111, 145].
    """
    try:
        res = requests.get(f"{API_URL}/gamification/profile/{user_id}")
        if res.status_code == 200:
            return res.json()
    except Exception:
        pass
    # Trả về các giá trị mặc định theo tài liệu iKids nếu lỗi kết nối [cite: 146]
    return {"balance": 0.0, "exp": 0, "rank": "Beginner", "full_name": "Người dùng"}

def deposit_money(user_id, amount):
    """
    Gửi yêu cầu nạp tiền thật vào tài khoản Phụ huynh[cite: 125, 126].
    Sau khi phụ huynh quét mã Vietcombank, hàm này được gọi để cập nhật số dư vào DB[cite: 196].
    """
    payload = {"user_id": str(user_id), "amount": float(amount)}
    try:
        res = requests.post(f"{API_URL}/account/deposit", json=payload)
        if res.status_code == 200:
            return True, res.json().get("message", "Nạp tiền thành công")
        return False, res.json().get("detail", "Giao dịch không thành công")
    except Exception as e:
        return False, str(e)

def purchase_product(user_id, product_id):
    """
    Xử lý yêu cầu mua học liệu bằng số dư tiền mặt VNĐ trong ví[cite: 149, 150].
    Dành cho cả vai trò Phụ huynh và Học sinh[cite: 124, 149].
    """
    payload = {"user_id": str(user_id), "product_id": int(product_id)}
    try:
        res = requests.post(f"{API_URL}/products/purchase", json=payload)
        if res.status_code == 200:
            return True, res.json()["message"]
        return False, res.json().get("detail", "Giao dịch thất bại")
    except Exception:
        return False, "Lỗi kết nối máy chủ."

def update_profile(user_id, name=None, avatar_file=None):
    """
    Cập nhật thông tin cá nhân bao gồm họ tên và ảnh đại diện thật lên server[cite: 49, 98].
    Dữ liệu ảnh được gửi dưới dạng multipart/form-data[cite: 816, 819].
    """
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

def send_forgot_password_otp(email):
    """
    Yêu cầu hệ thống gửi mã OTP khôi phục mật khẩu qua Email (SMTP Gmail)[cite: 52, 290, 1013].
    """
    try:
        res = requests.post(f"{API_URL}/auth/forgot-password", json={"email": email})
        if res.status_code == 200:
            return True, res.json().get("message")
        return False, res.json().get("detail", "Email không tồn tại.")
    except Exception:
        return False, "Không thể gửi yêu cầu lúc này."

def verify_and_reset_password(email, otp, new_password):
    """
    Xác thực mã OTP và tiến hành thiết lập mật khẩu mới cho người dùng[cite: 1058, 1073].
    """
    payload = {"email": email, "otp": otp, "new_password": new_password}
    try:
        res = requests.post(f"{API_URL}/auth/verify-reset", json=payload)
        if res.status_code == 200:
            return True, res.json().get("message")
        return False, res.json().get("detail", "Mã OTP sai hoặc hết hạn.")
    except Exception:
        return False, "Xác thực thất bại."

def submit_contact(sender_id, receiver_id, subject, content):
    """
    Gửi tin nhắn liên hệ. Nếu tiêu đề chứa 'nghỉ học', hệ thống tự động tạo 
    yêu cầu cho bộ phận Vận hành (TV1) xử lý[cite: 122, 123, 190].
    """
    payload = {
        "sender_id": str(sender_id),
        "receiver_id": str(receiver_id),
        "subject": subject,
        "content": content
    }
    try:
        res = requests.post(f"{API_URL}/contact/submit", json=payload)
        if res.status_code == 200:
            return True, res.json()
        return False, "Gửi tin nhắn thất bại."
    except Exception:
        return False, "Lỗi kết nối máy chủ."

# --- CÁC HÀM BỔ TRỢ VÀ GÓC KỶ NIỆM ---

def get_store_products():
    """Lấy danh sách các sản phẩm dụng cụ học tập hiện có trong cửa hàng[cite: 921, 929]."""
    try:
        res = requests.get(f"{API_URL}/products")
        return res.json() if res.status_code == 200 else []
    except Exception:
        return []

def get_memories():
    """Lấy danh sách kỷ niệm lớp học (ảnh/video) được giáo viên chia sẻ[cite: 115, 117, 151]."""
    try:
        res = requests.get(f"{API_URL}/memories")
        return res.json() if res.status_code == 200 else []
    except Exception:
        return []

def like_memory(memory_id):
    """
    Thực hiện thả tim cho một kỷ niệm lớp học[cite: 116, 203].
    Khắc phục lỗi ImportError trong các trang kỷ niệm.
    """
    try:
        res = requests.post(f"{API_URL}/memories/{memory_id}/like")
        return res.status_code == 200
    except Exception:
        return False

def get_contact_history(user_id):
    """Lấy lại toàn bộ lịch sử tin nhắn và trạng thái xử lý đơn xin nghỉ[cite: 1102]."""
    try:
        res = requests.get(f"{API_URL}/contact/history/{user_id}")
        return res.json() if res.status_code == 200 else []
    except Exception:
        return []

def get_daily_missions(student_id):
    """Lấy danh sách nhiệm vụ hằng ngày của học sinh để nhận thưởng EXP[cite: 161, 164]."""
    try:
        # Giả định endpoint này được cấu hình trong router.py
        res = requests.get(f"{API_URL}/gamification/missions/{student_id}")
        if res.status_code == 200:
            return res.json()
    except Exception:
        pass
    return []

@st.cache_data(ttl=300) 
def get_store_products():
    """Lấy danh sách sản phẩm sẽ nhanh hơn rất nhiều vì không phải gọi API liên tục"""
    res = requests.get(f"{API_URL}/products")
    return res.json() if res.status_code == 200 else []

@st.cache_data(ttl=600)
def get_memories():
    """Ảnh kỷ niệm thường nặng, cần cache để load nhanh hơn"""
    res = requests.get(f"{API_URL}/memories")
    return res.json() if res.status_code == 200 else []