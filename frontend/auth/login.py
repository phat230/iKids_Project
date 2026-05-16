import streamlit as st
import os
import time
from utils.auth_state import login_user

def load_auth_css():
    current_dir = os.path.dirname(os.path.abspath(__file__)) 
    css_path = os.path.abspath(os.path.join(current_dir, "../CSS/auth/style.css"))
    if os.path.exists(css_path):
        with open(css_path, "r", encoding="utf-8") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

load_auth_css()

# Dùng cột để ép Form vào giữa màn hình
_, col, _ = st.columns([1, 1.5, 1])

with col:
    # Phần Header
    st.markdown("<div class='auth-header'>", unsafe_allow_html=True)
    # Tạm dùng icon sinh ngẫu nhiên, bạn có thể thay bằng logo iKids thật
    st.image("https://api.dicebear.com/7.x/initials/svg?seed=iKids&backgroundColor=1e3a8a", width=70)
    st.markdown("<h2 class='auth-title'>Chào mừng trở lại! 👋</h2>", unsafe_allow_html=True)
    st.markdown("<p class='auth-subtitle'>Đăng nhập để tiếp tục truy cập iKids Portal</p>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

    # Phần Form nằm trong khung
    with st.container(border=True):
        with st.form("login_form"):
            email = st.text_input("📧 Địa chỉ Email", placeholder="ví dụ: phuhuynh@gmail.com")
            password = st.text_input("🔒 Mật khẩu", type="password", placeholder="••••••••")
            st.write("") # Tạo khoảng trống nhỏ
            submit_login = st.form_submit_button("🚀 Đăng Nhập", use_container_width=True, type="primary")
            
            if submit_login:
                success, msg = login_user(email, password)
                if success:
                    st.success("Đăng nhập thành công! Đang chuyển hướng...")
                    time.sleep(1)
                    st.rerun() 
                else:
                    st.error(msg)

    # Nút điều hướng phụ (nằm dưới form)
    st.markdown("<div class='btn-outline'>", unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        if st.button("❓ Quên mật khẩu", use_container_width=True):
            st.switch_page("auth/forgot_password.py")
    with c2:
        if st.button("✨ Đăng ký ngay", use_container_width=True):
            st.switch_page("auth/register.py")
    st.markdown("</div>", unsafe_allow_html=True)