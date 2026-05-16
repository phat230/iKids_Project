import streamlit as st
import requests
import os
import time

API_URL = "http://localhost:8000/api/tv3"

def load_auth_css():
    current_dir = os.path.dirname(os.path.abspath(__file__)) 
    css_path = os.path.abspath(os.path.join(current_dir, "../CSS/auth/style.css"))
    if os.path.exists(css_path):
        with open(css_path, "r", encoding="utf-8") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

load_auth_css()

if "forgot_step" not in st.session_state:
    st.session_state.forgot_step = 1
    st.session_state.reset_email = ""

_, col, _ = st.columns([1, 1.5, 1])

with col:
    st.markdown("<div class='auth-header'>", unsafe_allow_html=True)
    st.markdown("<h2 class='auth-title'>Khôi Phục Mật Khẩu 🔑</h2>", unsafe_allow_html=True)
    st.markdown("<p class='auth-subtitle'>Làm theo các bước dưới đây để lấy lại quyền truy cập</p>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

    with st.container(border=True):
        # --- BƯỚC 1: NHẬP EMAIL ---
        if st.session_state.forgot_step == 1:
            st.caption("Bước 1/2: Nhập email đã đăng ký để nhận mã xác thực OTP.")
            with st.form("email_form"):
                email = st.text_input("📧 Email của bạn")
                submit_email = st.form_submit_button("Gửi mã xác nhận OTP", use_container_width=True, type="primary")
                
                if submit_email:
                    if email:
                        with st.spinner("Đang gửi email..."):
                            try:
                                res = requests.post(f"{API_URL}/auth/forgot-password", json={"email": email})
                                if res.status_code == 200:
                                    st.session_state.reset_email = email
                                    st.session_state.forgot_step = 2
                                    st.rerun()
                                else:
                                    st.error("Email không tồn tại trong hệ thống.")
                            except:
                                st.error("Lỗi kết nối Server.")
                    else:
                        st.warning("Vui lòng điền email.")

        # --- BƯỚC 2: NHẬP OTP & ĐỔI PASS ---
        elif st.session_state.forgot_step == 2:
            st.success(f"Mã OTP đã được gửi đến: **{st.session_state.reset_email}**")
            st.caption("Bước 2/2: Xác thực và tạo mật khẩu mới.")
            with st.form("otp_form"):
                otp_code = st.text_input("🔢 Mã OTP (6 số)", max_chars=6)
                new_pass = st.text_input("🔒 Mật khẩu mới", type="password")
                confirm_pass = st.text_input("🔒 Xác nhận mật khẩu", type="password")
                
                submit_otp = st.form_submit_button("Xác nhận đổi mật khẩu", use_container_width=True, type="primary")
                
                if submit_otp:
                    if new_pass != confirm_pass:
                        st.error("Mật khẩu xác nhận không khớp.")
                    elif len(otp_code) < 6:
                        st.error("Mã OTP không hợp lệ.")
                    else:
                        with st.spinner("Đang xử lý..."):
                            payload = {"email": st.session_state.reset_email, "otp": otp_code, "new_password": new_pass}
                            res = requests.post(f"{API_URL}/auth/verify-reset", json=payload)
                            if res.status_code == 200:
                                st.session_state.forgot_step = 3
                                st.rerun()
                            else:
                                st.error("Mã OTP sai hoặc đã hết hạn.")

        # --- BƯỚC 3: THÀNH CÔNG ---
        elif st.session_state.forgot_step == 3:
            st.balloons()
            st.success("🎉 Mật khẩu của bạn đã được thay đổi thành công!")
            if st.button("Đăng nhập ngay", use_container_width=True, type="primary"):
                st.session_state.forgot_step = 1
                st.session_state.reset_email = ""
                st.switch_page("auth/login.py")

    # Nút quay lại (Chỉ hiện ở Bước 1 và 2)
    if st.session_state.forgot_step in [1, 2]:
        st.write("")
        st.markdown("<div class='btn-outline'>", unsafe_allow_html=True)
        if st.button("⬅️ Quay lại Đăng nhập", use_container_width=True):
            st.session_state.forgot_step = 1
            st.switch_page("auth/login.py")
        st.markdown("</div>", unsafe_allow_html=True)