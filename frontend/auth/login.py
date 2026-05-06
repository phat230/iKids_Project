import streamlit as st
from utils.auth_state import login_user

st.markdown("<h2 style='text-align: center; color: #1E3A8A;'>Đăng Nhập</h2>", unsafe_allow_html=True)

with st.form("login_form"):
    email = st.text_input("Email")
    password = st.text_input("Mật khẩu", type="password")
    submit_login = st.form_submit_button("Đăng Nhập", use_container_width=True)
    
    if submit_login:
        success, msg = login_user(email, password)
        if success:
            st.success(msg)
            st.rerun()  # Load lại trang để app.py nhận diện được token mới
        else:
            st.error(msg)