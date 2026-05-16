import streamlit as st
import os
import time
from utils.auth_state import register_user

def load_auth_css():
    current_dir = os.path.dirname(os.path.abspath(__file__)) 
    css_path = os.path.abspath(os.path.join(current_dir, "../CSS/auth/style.css"))
    if os.path.exists(css_path):
        with open(css_path, "r", encoding="utf-8") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

load_auth_css()

_, col, _ = st.columns([1, 1.5, 1])

with col:
    st.markdown("<div class='auth-header'>", unsafe_allow_html=True)
    st.markdown("<h2 class='auth-title'>Đăng Ký Phụ Huynh 👨‍👩‍👧‍👦</h2>", unsafe_allow_html=True)
    st.markdown("<p class='auth-subtitle'>Tạo tài khoản để đồng hành cùng bé tại iKids</p>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

    with st.container(border=True):
        st.info("💡 Lưu ý: Tài khoản học sinh sẽ được tạo sau khi phụ huynh đăng nhập thành công.")
        
        with st.form("register_form"):
            reg_name = st.text_input("👤 Họ và Tên")
            reg_email = st.text_input("📧 Địa chỉ Email")
            reg_password = st.text_input("🔒 Mật khẩu", type="password")
            
            st.write("")
            submit_reg = st.form_submit_button("Tạo Tài Khoản Mới", use_container_width=True, type="primary")
            
            if submit_reg:
                success, msg = register_user(reg_name, reg_email, reg_password, "parent")
                if success:
                    st.success("Tạo tài khoản thành công! Hãy đăng nhập.")
                    time.sleep(1.5)
                    st.switch_page("auth/login.py")
                else:
                    st.error(msg)
    
    st.write("")
    st.markdown("<div class='btn-outline'>", unsafe_allow_html=True)
    if st.button("⬅️ Đã có tài khoản? Đăng nhập tại đây", use_container_width=True):
        st.switch_page("auth/login.py")
    st.markdown("</div>", unsafe_allow_html=True)