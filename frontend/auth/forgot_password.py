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

# Lấy cấu hình ngôn ngữ hiện hành (Mặc định là "vi")
lang = st.session_state.get("lang", "vi")

# Bộ từ điển song ngữ chi tiết cho các bước khôi phục mật khẩu
FORGOT_LABELS = {
    "vi": {
        "title": "Khôi Phục Mật Khẩu",
        "subtitle": "Làm theo các bước dưới đây để lấy lại quyền truy cập",
        "step_1_cap": "Bước 1/2: Nhập email đã đăng ký để nhận mã xác thực OTP.",
        "field_email": "📧 Email của bạn",
        "btn_send_otp": "🚀 Gửi mã xác nhận OTP",
        "spinner_send": "Đang khởi tạo mã khôi phục...",
        "success_otp_sent": "Mã OTP đã được tạo! Hãy kiểm tra màn hình Terminal.",
        "err_connection": "❌ Không thể kết nối đến Server Backend. Vui lòng bật Uvicorn!",
        "warn_empty_email": "⚠️ Vui lòng điền địa chỉ email của bạn.",
        
        # Bước 2
        "otp_info": "Mã OTP khôi phục đã được in ra Terminal backend cho tài khoản:",
        "step_2_cap": "Bước 2/2: Xác thực mã OTP và tạo mật khẩu mới.",
        "field_otp": "🔢 Mã OTP (6 số)",
        "placeholder_otp": "Nhập 6 chữ số tại đây...",
        "field_new_pass": "🔒 Mật khẩu mới",
        "field_confirm_pass": "🔄 Xác nhận mật khẩu mới",
        "btn_confirm_reset": "💾 Xác nhận đổi mật khẩu",
        "err_fields_empty": "⚠️ Vui lòng điền đầy đủ tất cả các ô thông tin.",
        "err_match": "❌ Mật khẩu mới và mật khẩu xác nhận không trùng khớp.",
        "err_otp_len": "❌ Mã OTP nhập vào phải có độ dài đúng 6 số.",
        "spinner_reset": "Đang ghi đè mật khẩu mới vào cơ sở dữ liệu...",
        
        # Bước 3 & Điều hướng
        "success_reset": "🎉 Mật khẩu của bạn đã được thay đổi thành công!",
        "btn_back_login": "🔑 Quay lại màn hình Đăng nhập ngay",
        "btn_cancel": "⬅️ Quay lại Đăng nhập"
    },
    "en": {
        "title": "Reset Password",
        "subtitle": "Follow the steps below to regain access to your account",
        "step_1_cap": "Step 1/2: Enter your registered email to receive an OTP code.",
        "field_email": "📧 Your Email Address",
        "btn_send_otp": "🚀 Send OTP Verification Code",
        "spinner_send": "Generating recovery code...",
        "success_otp_sent": "OTP code generated! Please check the Backend Terminal.",
        "err_connection": "❌ Cannot connect to Backend Server. Please start Uvicorn!",
        "warn_empty_email": "⚠️ Please enter your email address.",
        
        # Step 2
        "otp_info": "The recovery OTP code has been printed to the backend Terminal for account:",
        "step_2_cap": "Step 2/2: Verify OTP code and create a new password.",
        "field_otp": "🔢 OTP Code (6 digits)",
        "placeholder_otp": "Enter 6 digits here...",
        "field_new_pass": "🔒 New Password",
        "field_confirm_pass": "🔄 Confirm New Password",
        "btn_confirm_reset": "💾 Confirm Reset Password",
        "err_fields_empty": "⚠️ Please fill in all information fields.",
        "err_match": "❌ New password and confirmation password do not match.",
        "err_otp_len": "❌ OTP code must be exactly 6 digits.",
        "spinner_reset": "Overwriting new password in the database...",
        
        # Step 3 & Navigation
        "success_reset": "🎉 Your password has been changed successfully!",
        "btn_back_login": "🔑 Back to Login screen now",
        "btn_cancel": "⬅️ Back to Login"
    }
}

if "forgot_step" not in st.session_state:
    st.session_state.forgot_step = 1
    st.session_state.reset_email = ""

_, col, _ = st.columns([1, 1.5, 1])

with col:
    # --- PHẦN HEADER ---
    st.markdown("<div class='auth-header'>", unsafe_allow_html=True)
    st.markdown(f"<h2 class='auth-title'>{FORGOT_LABELS[lang]['title']}</h2>", unsafe_allow_html=True)
    st.markdown(f"<p class='auth-subtitle'>{FORGOT_LABELS[lang]['subtitle']}</p>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

    with st.container(border=True):
        # ==========================================
        # BƯỚC 1: NHẬP ĐỊA CHỈ EMAIL ĐỂ LẤY OTP
        # ==========================================
        if st.session_state.forgot_step == 1:
            st.caption(FORGOT_LABELS[lang]["step_1_cap"])
            with st.form("email_form"):
                email = st.text_input(FORGOT_LABELS[lang]["field_email"])
                submit_email = st.form_submit_button(FORGOT_LABELS[lang]["btn_send_otp"])
                
                if submit_email:
                    clean_email = email.strip()
                    if clean_email:
                        with st.spinner(FORGOT_LABELS[lang]["spinner_send"]):
                            try:
                                res = requests.post(f"{API_URL}/forgot-password", json={"email": clean_email})
                                if res.status_code == 200:
                                    st.session_state.reset_email = clean_email
                                    st.session_state.forgot_step = 2
                                    st.success(FORGOT_LABELS[lang]["success_otp_sent"])
                                    time.sleep(1.5)
                                    st.rerun()
                                else:
                                    err_detail = res.json().get("detail", "")
                                    # Chuyển ngữ thông báo lỗi email không tồn tại từ Backend
                                    if lang == "en" and ("không tồn tại" in err_detail or not err_detail):
                                        st.error("❌ Email address not found in the system.")
                                    else:
                                        st.error(f"❌ {err_detail if err_detail else 'Error'}")
                            except requests.exceptions.ConnectionError:
                                st.error(FORGOT_LABELS[lang]["err_connection"])
                    else:
                        st.warning(FORGOT_LABELS[lang]["warn_empty_email"])

        # ==========================================
        # BƯỚC 2: XÁC THỰC MÃ OTP & ĐỔI MẬT KHẨU MỚI
        # ==========================================
        elif st.session_state.forgot_step == 2:
            st.info(f"💡 {FORGOT_LABELS[lang]['otp_info']} **{st.session_state.reset_email}**")
            st.caption(FORGOT_LABELS[lang]["step_2_cap"])
            with st.form("otp_form"):
                otp_code = st.text_input(FORGOT_LABELS[lang]["field_otp"], max_chars=6, placeholder=FORGOT_LABELS[lang]["placeholder_otp"])
                new_pass = st.text_input(FORGOT_LABELS[lang]["field_new_pass"], type="password")
                confirm_pass = st.text_input(FORGOT_LABELS[lang]["field_confirm_pass"], type="password")
                
                submit_otp = st.form_submit_button(FORGOT_LABELS[lang]["btn_confirm_reset"])
                
                if submit_otp:
                    if not otp_code.strip() or not new_pass or not confirm_pass:
                        st.error(FORGOT_LABELS[lang]["err_fields_empty"])
                    elif new_pass != confirm_pass:
                        st.error(FORGOT_LABELS[lang]["err_match"])
                    elif len(otp_code.strip()) != 6:
                        st.error(FORGOT_LABELS[lang]["err_otp_len"])
                    else:
                        with st.spinner(FORGOT_LABELS[lang]["spinner_reset"]):
                            try:
                                payload = {
                                    "email": st.session_state.reset_email, 
                                    "otp": otp_code.strip(), 
                                    "new_password": new_pass
                                }
                                res = requests.post(f"{API_URL}/verify-reset", json=payload)
                                if res.status_code == 200:
                                    st.session_state.forgot_step = 3
                                    st.rerun()
                                else:
                                    err_detail = res.json().get("detail", "")
                                    # Chuyển ngữ thông báo OTP lỗi hoặc hết hạn từ Backend
                                    if lang == "en" and ("không chính xác" in err_detail or "hết hạn" in err_detail or not err_detail):
                                        st.error("❌ Invalid or expired OTP code.")
                                    else:
                                        st.error(f"❌ {err_detail if err_detail else 'Error'}")
                            except requests.exceptions.ConnectionError:
                                st.error(FORGOT_LABELS[lang]["err_connection"])

        # ==========================================
        # BƯỚC 3: THÀNH CÔNG (HIỂN THỊ HIỆU ỨNG)
        # ==========================================
        elif st.session_state.forgot_step == 3:
            st.balloons()
            st.success(FORGOT_LABELS[lang]["success_reset"])
            if st.button(FORGOT_LABELS[lang]["btn_back_login"], use_container_width=True, type="primary"):
                st.session_state.forgot_step = 1
                st.session_state.reset_email = ""
                st.switch_page("auth/login.py")

    # --- NÚT HỦY / QUAY LẠI (HIỂN THỊ Ở BƯỚC 1 VÀ 2) ---
    if st.session_state.forgot_step in [1, 2]:
        st.write("")
        st.markdown("<div class='btn-outline'>", unsafe_allow_html=True)
        if st.button(FORGOT_LABELS[lang]["btn_cancel"], use_container_width=True):
            st.session_state.forgot_step = 1
            st.session_state.reset_email = ""
            st.switch_page("auth/login.py")
        st.markdown("</div>", unsafe_allow_html=True)