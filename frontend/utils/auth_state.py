import requests
import streamlit as st

# Đảm bảo URL chính xác với cổng Backend của bạn
API_URL = "http://localhost:8000/api/auth"

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
        return False, "Không thể kết nối đến Backend. Vui lòng bật Uvicorn!"

def logout_user():
    """Xóa sạch phiên làm việc và quay về trang chủ"""
    # Xóa toàn bộ session bao gồm user_info và avatar_image
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.rerun()

def register_user(name, email, password, role):
    """Gọi API Đăng ký người dùng mới"""
    payload = {"name": name, "email": email, "password": password, "role": role}
    try:
        response = requests.post(f"{API_URL}/register", json=payload)
        if response.status_code == 200:
            return True, "Đăng ký thành công! Hãy chuyển sang Đăng nhập."
        
        try:
            error_msg = response.json().get("detail", "Lỗi đăng ký")
        except Exception:
            error_msg = f"Lỗi hệ thống ({response.status_code})"
            
        return False, error_msg
        
    except requests.exceptions.ConnectionError:
        return False, "Lỗi kết nối Server."