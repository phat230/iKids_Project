import os
import requests
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

# Lấy URL linh hoạt từ cấu hình của Render
BACKEND_URL = os.getenv("API_URL", "http://localhost:8000")
API_URL = f"{BACKEND_URL}/api/auth"

def login_user(email, password):
    """Gọi API Đăng nhập và nạp đầy đủ thông tin vào Session"""
    try:
        response = requests.post(f"{API_URL}/login", json={"email": email, "password": password})
        if response.status_code == 200:
            data = response.json()
            
            # 1. Lưu Token và Role
            st.session_state["token"] = data["access_token"]
            st.session_state["access_token"] = data["access_token"] # THÊM DÒNG NÀY ĐỂ FIX LỖI KEYERROR
            st.session_state["role"] = data["user_info"]["role"]
            st.session_state["user_id"] = data["user_info"]["id"]
            
            # 2. Lưu user_info để app.py hiển thị ở Sidebar
            st.session_state["user_info"] = data["user_info"]
            
            return True, "Đăng nhập thành công"
        
        try:
            error_msg = response.json().get("detail", "Lỗi đăng nhập không xác định")
        except Exception:
            error_msg = f"Lỗi Server ({response.status_code})"
            
        return False, error_msg
        
    except requests.exceptions.ConnectionError:
        return False, "Không thể kết nối đến Backend. Vui lòng kiểm tra lại trạng thái Server!"

def logout_user():
    """Xóa sạch phiên làm việc và quay về trang chủ"""
    # Xóa toàn bộ session bao gồm user_info và avatar_image
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.rerun()

def register_user(name, email, password, role, phone_number=None, birth_date=None):
    """
    Gọi API Đăng ký người dùng mới.
    Đã bổ sung: phone_number (Số điện thoại nhận OTP) và birth_date (Ngày sinh YYYY-MM-DD)
    """
    payload = {
        "name": name, 
        "email": email, 
        "password": password, 
        "role": role,
        "phone_number": phone_number,
        "birth_date": birth_date
    }
    try:
        response = requests.post(f"{API_URL}/register", json=payload)
        
        # Nhận mã trạng thái 200 từ Backend khi đăng ký bước đầu thành công
        if response.status_code == 200:
            msg = response.json().get("message", "Đăng ký thành công bước đầu! Vui lòng kiểm tra OTP.")
            return True, msg
        
        try:
            error_msg = response.json().get("detail", "Lỗi đăng ký")
            # Trường hợp Pydantic Validation trả về lỗi mảng
            if isinstance(error_msg, list):
                error_msg = error_msg[0].get("msg", "Dữ liệu nhập vào không hợp lệ.")
        except Exception:
            error_msg = f"Lỗi hệ thống ({response.status_code})"
            
        return False, error_msg
        
    except requests.exceptions.ConnectionError:
        return False, "Lỗi kết nối Server Backend."

def verify_registration_otp(email, otp_code):
    """
    Gọi API Xác thực mã OTP để chính thức kích hoạt tài khoản vừa đăng ký
    """
    payload = {
        "email": email,
        "otp_code": otp_code
    }
    try:
        response = requests.post(f"{API_URL}/verify-registration-otp", json=payload)
        if response.status_code == 200:
            msg = response.json().get("message", "Xác thực tài khoản thành công!")
            return True, msg
        
        try:
            error_msg = response.json().get("detail", "Mã xác thực không hợp lệ hoặc đã hết hạn.")
            if isinstance(error_msg, list):
                error_msg = error_msg[0].get("msg", "Dữ liệu OTP không hợp lệ.")
        except Exception:
            error_msg = f"Lỗi hệ thống ({response.status_code})"
            
        return False, error_msg
        
    except requests.exceptions.ConnectionError:
        return False, "Lỗi kết nối Server khi gửi mã xác thực."