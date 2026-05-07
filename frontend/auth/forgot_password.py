import streamlit as st
import requests

API_URL = "http://localhost:8000/api/tv3"

# CSS để nút bấm đẹp hơn
st.markdown("<style>.stButton>button { width: 100%; }</style>", unsafe_allow_html=True)

# Nút quay lại trang đăng nhập (Vì trang này bị ẩn khỏi Menu)
if st.sidebar.button("⬅️ Quay lại Đăng nhập"):
    st.switch_page("auth/login.py")

st.title("🔑 Khôi Phục Mật Khẩu")

if "forgot_step" not in st.session_state:
    st.session_state.forgot_step = 1
    st.session_state.reset_email = ""

# --- BƯỚC 1: NHẬP EMAIL ---
if st.session_state.forgot_step == 1:
    st.write("Nhập email đã đăng ký để nhận mã xác thực OTP.")
    with st.form("email_form"):
        email = st.text_input("Email tài khoản", placeholder="example@gmail.com")
        if st.form_submit_button("Gửi mã xác nhận OTP"):
            if email:
                try:
                    res = requests.post(f"{API_URL}/auth/forgot-password", json={"email": email})
                    if res.status_code == 200:
                        st.session_state.reset_email = email
                        st.session_state.forgot_step = 2
                        st.rerun()
                    else:
                        st.error("Email không tồn tại trong hệ thống.")
                except Exception as e:
                    st.error(f"Lỗi kết nối Server: {e}")
            else:
                st.warning("Vui lòng điền email.")

# --- BƯỚC 2: NHẬP OTP & ĐỔI PASS ---
elif st.session_state.forgot_step == 2:
    st.info(f"Đang khôi phục cho: **{st.session_state.reset_email}**")
    with st.form("otp_form"):
        otp_code = st.text_input("Mã OTP (6 số)", max_chars=6)
        new_pass = st.text_input("Mật khẩu mới", type="password")
        confirm_pass = st.text_input("Xác nhận mật khẩu mới", type="password")
        
        if st.form_submit_button("Xác nhận đổi mật khẩu"):
            if new_pass != confirm_pass:
                st.error("Mật khẩu xác nhận không khớp.")
            elif len(otp_code) < 6:
                st.error("Mã OTP không hợp lệ.")
            else:
                payload = {
                    "email": st.session_state.reset_email,
                    "otp": otp_code,
                    "new_password": new_pass
                }
                res = requests.post(f"{API_URL}/auth/verify-reset", json=payload)
                if res.status_code == 200:
                    st.session_state.forgot_step = 3
                    st.rerun()
                else:
                    st.error("Mã OTP sai hoặc đã hết hạn.")

# --- BƯỚC 3: THÀNH CÔNG ---
elif st.session_state.forgot_step == 3:
    st.balloons()
    st.success("🎉 Đổi mật khẩu thành công! Bạn có thể dùng mật khẩu mới để đăng nhập.")
    if st.button("Quay lại Đăng nhập ngay"):
        st.session_state.forgot_step = 1
        st.session_state.reset_email = ""
        st.switch_page("auth/login.py")