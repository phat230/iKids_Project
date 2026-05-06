import streamlit as st
from utils.auth_state import register_user

st.markdown("<h2 style='text-align: center; color: #1E3A8A;'>Đăng Ký</h2>", unsafe_allow_html=True)

with st.form("register_form"):
    reg_name = st.text_input("Họ và Tên")
    reg_email = st.text_input("Email")
    reg_password = st.text_input("Mật khẩu", type="password")
    
    # Chỉ cho phép đăng ký Học sinh và Phụ huynh
    role_options = {"Học sinh": "student", "Phụ huynh": "parent"}
    selected_role_label = st.selectbox("Vai trò của bạn", list(role_options.keys()))
    
    submit_reg = st.form_submit_button("Tạo Tài Khoản", use_container_width=True)
    
    if submit_reg:
        reg_role_value = role_options[selected_role_label]
        success, msg = register_user(reg_name, reg_email, reg_password, reg_role_value)
        if success:
            st.success(msg)
        else:
            st.error(msg)