# frontend/auth/login.py
import streamlit as st
import os
import time
from utils.auth_state import login_user
from locales import UI_LOCALES  # Import từ điển ngôn ngữ tập trung

def load_auth_css():
    current_dir = os.path.dirname(os.path.abspath(__file__)) 
    css_path = os.path.abspath(os.path.join(current_dir, "../CSS/auth/style.css"))
    if os.path.exists(css_path):
        with open(css_path, "r", encoding="utf-8") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

load_auth_css()

# Lấy cấu hình ngôn ngữ hiện hành từ session_state (Mặc định là "vi")
lang = st.session_state.get("lang", "vi")

# Mở rộng bộ từ điển cho riêng các nhãn chi tiết của trang Login (Tránh viết sót)
LOGIN_LABELS = {
    "vi": {
        "welcome_title": "Chào mừng trở lại! 👋",
        "welcome_subtitle": "Đăng nhập để tiếp tục truy cập iKids Portal",
        "placeholder_email": "ví dụ: phuhuynh@gmail.com",
        "btn_forgot": "🔑 Quên mật khẩu",
        "btn_register_now": "📝 Đăng ký ngay",
        "redirect_success": "🎉 Đăng nhập thành công! Đang chuyển hướng..."
    },
    "en": {
        "welcome_title": "Welcome Back! 👋",
        "welcome_subtitle": "Sign in to continue to iKids Portal",
        "placeholder_email": "e.g., parent@gmail.com",
        "btn_forgot": "🔑 Forgot Password?",
        "btn_register_now": "📝 Register Now",
        "redirect_success": "🎉 Login successful! Redirecting..."
    }
}

# Dùng cột để ép Form vào giữa màn hình
_, col, _ = st.columns([1, 1.5, 1])

with col:
    # --- PHẦN HEADER ---
    st.markdown("<div class='auth-header'>", unsafe_allow_html=True)
    
    # SỬA ĐỔI: Đọc logo local từ thư mục static thay vì gọi link API chữ IK xanh cũ
    current_dir = os.path.dirname(os.path.abspath(__file__))
    logo_path = os.path.abspath(os.path.join(current_dir, "../static/logo.png"))
    
    if os.path.exists(logo_path):
        st.image(logo_path, width=85, output_format="PNG")
    else:
        # Fallback phòng hờ nếu hệ thống chưa nhận diện kịp file logo
        st.image("https://api.dicebear.com/7.x/initials/svg?seed=iKids&backgroundColor=1e3a8a", width=85)
        
    st.markdown(f"<h2 class='auth-title'>{LOGIN_LABELS[lang]['welcome_title']}</h2>", unsafe_allow_html=True)
    st.markdown(f"<p class='auth-subtitle'>{LOGIN_LABELS[lang]['welcome_subtitle']}</p>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

    # --- PHẦN FORM ĐĂNG NHẬP ---
    with st.container(border=True):
        with st.form("login_form"):
            # Sử dụng UI_LOCALES tập trung cho các trường input chính
            email = st.text_input(f"📧 {UI_LOCALES[lang]['field_username']}", placeholder=LOGIN_LABELS[lang]['placeholder_email'])
            password = st.text_input(f"🔒 {UI_LOCALES[lang]['field_password']}", type="password", placeholder="••••••••")
            st.write("") # Tạo khoảng trống nhỏ
            
            submit_login = st.form_submit_button(UI_LOCALES[lang]['btn_login'], use_container_width=True, type="primary")
            
            if submit_login:
                if not email.strip() or not password.strip():
                    st.error("⚠️ Please fill in all fields" if lang == "en" else "⚠️ Vui lòng điền đầy đủ các thông tin!")
                else:
                    success, msg = login_user(email, password)
                    if success:
                        st.success(LOGIN_LABELS[lang]['redirect_success'])
                        time.sleep(1)
                        st.rerun() 
                    else:
                        if lang == "en" and "Không tìm thấy" in msg:
                            st.error("❌ Account does not exist or wrong password.")
                        elif lang == "en" and "Mật khẩu" in msg:
                            st.error("❌ Incorrect password.")
                        else:
                            st.error(msg)

    # --- NÚT ĐIỀU HƯỚNG PHỤ (NẰM DƯỚI FORM) ---
    st.markdown("<div class='btn-outline'>", unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        if st.button(LOGIN_LABELS[lang]['btn_forgot'], use_container_width=True):
            st.switch_page("auth/forgot_password.py")
    with c2:
        if st.button(LOGIN_LABELS[lang]['btn_register_now'], use_container_width=True):
            st.switch_page("auth/register.py")
    st.markdown("</div>", unsafe_allow_html=True)