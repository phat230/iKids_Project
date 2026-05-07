import streamlit as st
from utils.auth_state import login_user

st.markdown("<h2 style='text-align: center; color: #1E3A8A;'>Đăng Nhập</h2>", unsafe_allow_html=True)

# Khối Form Đăng Nhập
with st.form("login_form"):
    email = st.text_input("Email", placeholder="nhap-email@gmail.com")
    password = st.text_input("Mật khẩu", type="password")
    submit_login = st.form_submit_button("Đăng Nhập", use_container_width=True)
    
    if submit_login:
        success, msg = login_user(email, password)
        if success:
            st.success(msg)
            st.rerun() 
        else:
            st.error(msg)

st.markdown("<br>", unsafe_allow_html=True)
col1, col2, col3 = st.columns([1, 2, 1])

with col2:
    # Nút bấm này sẽ kích hoạt chuyển trang
    if st.button("❓ Quên mật khẩu?", key="forgot_link", use_container_width=True):
        # Đường dẫn phải khớp 100% với file khai báo trong app.py
        st.switch_page("auth/forgot_password.py")