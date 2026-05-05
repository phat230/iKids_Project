import requests
import streamlit as st

API_URL = "http://localhost:8000/api/auth"

def login_user(email, password):
    """Gọi API Đăng nhập an toàn"""
    try:
        response = requests.post(f"{API_URL}/login", json={"email": email, "password": password})
        if response.status_code == 200:
            data = response.json()
            st.session_state["token"] = data["access_token"]
            st.session_state["user_info"] = data["user_info"]
            st.session_state["role"] = data["user_info"]["role"]
            return True, "Đăng nhập thành công"
        
        # Thử đọc JSON lỗi, nếu không phải JSON thì bắt lỗi
        try:
            error_msg = response.json().get("detail", "Lỗi đăng nhập không xác định")
        except Exception:
            error_msg = f"Lỗi Server ({response.status_code}): {response.text[:100]}"
            
        return False, error_msg
        
    except requests.exceptions.ConnectionError:
        return False, "Không thể kết nối đến Backend. Vui lòng bật Uvicorn!"

def register_user(name, email, password, role):
    """Gọi API Đăng ký an toàn"""
    payload = {"name": name, "email": email, "password": password, "role": role}
    try:
        response = requests.post(f"{API_URL}/register", json=payload)
        if response.status_code == 200:
            return True, "Đăng ký thành công! Vui lòng chuyển sang tab Đăng nhập."
        
        # Thử đọc JSON lỗi, nếu không phải JSON thì bắt lỗi
        try:
            error_msg = response.json().get("detail", "Lỗi đăng ký không xác định")
        except Exception:
            error_msg = f"Lỗi Server ({response.status_code}): {response.text[:150]}"
            
        return False, error_msg
        
    except requests.exceptions.ConnectionError:
        return False, "Không thể kết nối đến Backend. Vui lòng bật Uvicorn!"

def logout_user():
    """Xóa phiên và đăng xuất"""
    st.session_state.clear()
    st.rerun()