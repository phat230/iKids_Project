import streamlit as st
import requests
import os
import time

# ĐỒNG BỘ: Định tuyến lại chính xác sang cụm phân hệ Auth của Backend
API_URL = "http://localhost:8000/api/auth"

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
    st.markdown("<h2 class='auth-title'>Khôi Phục Mật Khẩu </h2>", unsafe_allow_html=True)
    st.markdown("<p class='auth-subtitle'>Làm theo các bước dưới đây để lấy lại quyền truy cập</p>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

    with st.container(border=True):
        # --- BƯỚC 1: NHẬP EMAIL ---
        if st.session_state.forgot_step == 1:
            st.caption("Bước 1/2: Nhập email đã đăng ký để nhận mã xác thực OTP.")
            with st.form("email_form"):
                email = st.text_input(" Email của bạn")
                submit_email = st.form_submit_button("Gửi mã xác nhận OTP", use_container_width=True, type="primary")
                
                if submit_email:
                    clean_email = email.strip()
                    if clean_email:
                        with st.spinner("Đang khởi tạo mã khôi phục..."):
                            try:
                                # Gọi API phân hệ auth bước 1
                                res = requests.post(f"{API_URL}/forgot-password", json={"email": clean_email})
                                if res.status_code == 200:
                                    st.session_state.reset_email = clean_email
                                    st.session_state.forgot_step = 2
                                    st.success("Mã OTP đã được tạo! Hãy kiểm tra màn hình Terminal.")
                                    time.sleep(1.5)
                                    st.rerun()
                                else:
                                    err_detail = res.json().get("detail", "Email không tồn tại trong hệ thống.")
                                    st.error(f"❌ {err_detail}")
                            except requests.exceptions.ConnectionError:
                                st.error("❌ Không thể kết nối đến Server Backend. Vui lòng bật Uvicorn!")
                    else:
                        st.warning("⚠️ Vui lòng điền địa chỉ email của bạn.")

        # --- BƯỚC 2: NHẬP OTP & ĐỔI MẬT KHẨU MỚI ---
        elif st.session_state.forgot_step == 2:
            st.info(f"Mã OTP khôi phục đã được in ra Terminal backend cho tài khoản: **{st.session_state.reset_email}**")
            st.caption("Bước 2/2: Xác thực mã OTP và tạo mật khẩu mới.")
            with st.form("otp_form"):
                otp_code = st.text_input(" Mã OTP (6 số)", max_chars=6, placeholder="Nhập 6 chữ số tại đây...")
                new_pass = st.text_input(" Mật khẩu mới", type="password")
                confirm_pass = st.text_input(" Xác nhận mật khẩu mới", type="password")
                
                submit_otp = st.form_submit_button("Xác nhận đổi mật khẩu", use_container_width=True, type="primary")
                
                if submit_otp:
                    if not otp_code.strip() or not new_pass or not confirm_pass:
                        st.error("⚠️ Vui lòng điền đầy đủ tất cả các ô thông tin.")
                    elif new_pass != confirm_pass:
                        st.error("❌ Mật khẩu mới và mật khẩu xác nhận không trùng khớp.")
                    elif len(otp_code.strip()) != 6:
                        st.error("❌ Mã OTP nhập vào phải có độ dài đúng 6 số.")
                    else:
                        with st.spinner("Đang ghi đè mật khẩu mới vào cơ sở dữ liệu..."):
                            try:
                                payload = {
                                    "email": st.session_state.reset_email, 
                                    "otp": otp_code.strip(), 
                                    "new_password": new_pass
                                }
                                # Gọi API phân hệ auth bước 2
                                res = requests.post(f"{API_URL}/verify-reset", json=payload)
                                if res.status_code == 200:
                                    st.session_state.forgot_step = 3
                                    st.rerun()
                                else:
                                    err_detail = res.json().get("detail", "Mã OTP không chính xác hoặc đã hết hạn.")
                                    st.error(f"❌ {err_detail}")
                            except requests.exceptions.ConnectionError:
                                st.error("❌ Lỗi kết nối đến Server Backend.")

        # --- BƯỚC 3: THÀNH CÔNG ---
        elif st.session_state.forgot_step == 3:
            st.balloons()
            st.success("🎉 Mật khẩu của bạn đã được thay đổi thành công!")
            if st.button("Quay lại màn hình Đăng nhập ngay", use_container_width=True, type="primary"):
                st.session_state.forgot_step = 1
                st.session_state.reset_email = ""
                st.switch_page("auth/login.py")

    # Nút quay lại (Chỉ hiển thị ở Bước 1 và Bước 2)
    if st.session_state.forgot_step in [1, 2]:
        st.write("")
        st.markdown("<div class='btn-outline'>", unsafe_allow_html=True)
        if st.button(" Quay lại Đăng nhập", use_container_width=True):
            st.session_state.forgot_step = 1
            st.session_state.reset_email = ""
            st.switch_page("auth/login.py")
        st.markdown("</div>", unsafe_allow_html=True)