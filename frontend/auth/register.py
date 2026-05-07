import streamlit as st
from utils.auth_state import register_user

st.markdown("<h2 style='text-align: center; color: #1E3A8A;'>Đăng Ký Phụ Huynh</h2>", unsafe_allow_html=True)

# Thêm một thông báo nhỏ để người dùng không bị bỡ ngỡ
st.info("💡 Lưu ý: Chỉ phụ huynh mới có thể đăng ký tài khoản tại đây. Tài khoản học sinh sẽ được tạo sau khi phụ huynh đăng nhập thành công.")

with st.form("register_form"):
    reg_name = st.text_input("Họ và Tên Phụ Huynh")
    reg_email = st.text_input("Email")
    reg_password = st.text_input("Mật khẩu", type="password")
    
    submit_reg = st.form_submit_button("Tạo Tài Khoản", use_container_width=True)
    
    if submit_reg:
        # Ép cứng role là 'parent'
        success, msg = register_user(reg_name, reg_email, reg_password, "parent")
        if success:
            st.success(msg)
        else:
            st.error(msg)