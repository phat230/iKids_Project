import streamlit as st
import os
import time
from datetime import date
from utils.auth_state import register_user, verify_registration_otp
from locales import UI_LOCALES  # Import từ điển ngôn ngữ tập trung

def load_auth_css():
    current_dir = os.path.dirname(os.path.abspath(__file__)) 
    css_path = os.path.abspath(os.path.join(current_dir, "../CSS/auth/style.css"))
    if os.path.exists(css_path):
        with open(css_path, "r", encoding="utf-8") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

load_auth_css()

# Lấy cấu hình ngôn ngữ hiện hành (Mặc định là "vi")
lang = st.session_state.get("lang", "vi")

# Bộ từ điển chi tiết hóa các chuỗi ký tự động dành riêng cho luồng Đăng ký & OTP
REGISTER_LABELS = {
    "vi": {
        "title": "Đăng Ký Phụ Huynh",
        "subtitle": "Tạo tài khoản để đồng hành cùng bé tại iKids",
        "info_note": "💡 Lưu ý: Tài khoản học sinh sẽ được tạo sau khi phụ huynh đăng nhập thành công.",
        "field_email": "Địa chỉ Email (*)",
        "field_phone": "Số điện thoại (Nhận SMS OTP) (*)",
        "field_birth": "Ngày tháng năm sinh của bạn (*)",
        "placeholder_phone": "Ví dụ: 0912345678",
        "btn_continue": "🚀 Tiếp Tục & Nhận OTP",
        "error_empty": "⚠️ Vui lòng điền đầy đủ thông tin vào các trường bắt buộc (*)",
        
        # Bước 2: OTP
        "otp_warning": "Mã xác thực OTP đã được gửi. Vui lòng kiểm tra Terminal backend hoặc tin nhắn di động gắn với tài khoản:",
        "otp_field": "Mã OTP Xác Thực (6 chữ số)",
        "otp_placeholder": "Nhập tại đây...",
        "btn_activate": "🔑 Kích Hoạt Tài Khoản",
        "error_length": "⚠️ Mã OTP phải có độ dài đúng 6 ký tự số.",
        "success_activate": "🎉 Tài khoản đã kích hoạt thành công! Hệ thống đang chuyển hướng...",
        "btn_back": "⬅️ Quay lại form đăng ký",
        "btn_have_account": "🔑 Đã có tài khoản? Đăng nhập tại đây"
    },
    "en": {
        "title": "Parent Registration",
        "subtitle": "Create an account to companion with your child at iKids",
        "info_note": "💡 Note: Student accounts will be created after the parent logs in successfully.",
        "field_email": "Email Address (*)",
        "field_phone": "Phone Number (For SMS OTP) (*)",
        "field_birth": "Your Date of Birth (*)",
        "placeholder_phone": "e.g., 0912345678",
        "btn_continue": "🚀 Continue & Receive OTP",
        "error_empty": "⚠️ Please fill in all required fields (*)",
        
        # Step 2: OTP
        "otp_warning": "An OTP verification code has been sent. Please check backend terminal or SMS associated with account:",
        "otp_field": "OTP Verification Code (6 digits)",
        "otp_placeholder": "Enter here...",
        "btn_activate": "🔑 Activate Account",
        "error_length": "⚠️ OTP code must be exactly 6 digits.",
        "success_activate": "🎉 Account activated successfully! Redirecting...",
        "btn_back": "⬅️ Back to registration form",
        "btn_have_account": "🔑 Already have an account? Sign in here"
    }
}

# Khởi tạo các trạng thái Session State để điều khiển luồng nhập OTP
if "register_step" not in st.session_state:
    st.session_state["register_step"] = 1  
if "temp_reg_email" not in st.session_state:
    st.session_state["temp_reg_email"] = ""

_, col, _ = st.columns([1, 1.5, 1])

with col:
    # --- PHẦN HEADER ---
    st.markdown("<div class='auth-header'>", unsafe_allow_html=True)
    st.markdown(f"<h2 class='auth-title'>{REGISTER_LABELS[lang]['title']}</h2>", unsafe_allow_html=True)
    st.markdown(f"<p class='auth-subtitle'>{REGISTER_LABELS[lang]['subtitle']}</p>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

    with st.container(border=True):
        st.info(REGISTER_LABELS[lang]["info_note"])
        
        # ==========================================
        # BƯỚC 1: ĐIỀN FORM ĐĂNG KÝ THÔNG TIN CÁ NHÂN
        # ==========================================
        if st.session_state["register_step"] == 1:
            with st.form("register_form"):
                reg_name = st.text_input(f"👤 {UI_LOCALES[lang]['field_fullname']}")
                reg_email = st.text_input(f"📧 {REGISTER_LABELS[lang]['field_email']}")
                reg_phone = st.text_input(f"📱 {REGISTER_LABELS[lang]['field_phone']}", placeholder=REGISTER_LABELS[lang]['placeholder_phone'])
                
                reg_birth = st.date_input(
                    f"📅 {REGISTER_LABELS[lang]['field_birth']}", 
                    min_value=date(1940, 1, 1),
                    max_value=date.today(),
                    value=date(1995, 1, 1)
                )
                
                reg_password = st.text_input(f"🔒 {UI_LOCALES[lang]['field_password']}", type="password")
                
                st.write("")
                submit_reg = st.form_submit_button(REGISTER_LABELS[lang]["btn_continue"])
                
                if submit_reg:
                    if not reg_name.strip() or not reg_email.strip() or not reg_phone.strip() or not reg_password:
                        st.error(REGISTER_LABELS[lang]["error_empty"])
                    else:
                        success, msg = register_user(
                            name=reg_name.strip(), 
                            email=reg_email.strip(), 
                            password=reg_password, 
                            role="parent",
                            phone_number=reg_phone.strip(),
                            birth_date=reg_birth.isoformat()
                        )
                        
                        if success:
                            st.session_state["register_step"] = 2
                            st.session_state["temp_reg_email"] = reg_email.strip().lower()
                            
                            # Nếu phản hồi thành công từ backend trả về tiếng Việt, chuyển ngữ hiển thị nếu lang == 'en'
                            success_msg = "Registration successful! OTP sent." if lang == "en" else msg
                            st.success(success_msg)
                            time.sleep(1.5)
                            st.rerun()
                        else:
                            # Khớp dịch một số thông báo lỗi trùng tài khoản phổ biến từ Backend
                            if lang == "en" and "đã tồn tại" in msg:
                                st.error("❌ Email or phone number already registered.")
                            else:
                                st.error(msg)
                                
        # ==========================================
        # BƯỚC 2: NHẬP MÃ XÁC THỰC TIN NHẮN OTP
        # ==========================================
        elif st.session_state["register_step"] == 2:
            st.warning(f"⚠️ {REGISTER_LABELS[lang]['otp_warning']} {st.session_state['temp_reg_email']}")
            
            with st.form("otp_verify_form"):
                otp_code = st.text_input(REGISTER_LABELS[lang]["otp_field"], max_chars=6, placeholder=REGISTER_LABELS[lang]["otp_placeholder"])
                st.write("")
                submit_otp = st.form_submit_button(REGISTER_LABELS[lang]["btn_activate"])
                
                if submit_otp:
                    if len(otp_code.strip()) != 6:
                        st.error(REGISTER_LABELS[lang]["error_length"])
                    else:
                        success_otp, msg_otp = verify_registration_otp(
                            email=st.session_state["temp_reg_email"],
                            otp_code=otp_code.strip()
                        )
                        
                        if success_otp:
                            st.success(REGISTER_LABELS[lang]["success_activate"])
                            st.session_state["register_step"] = 1
                            st.session_state["temp_reg_email"] = ""
                            time.sleep(2.0)
                            st.switch_page("auth/login.py")
                        else:
                            if lang == "en" and "không chính xác" in msg_otp:
                                st.error("❌ Invalid or expired OTP code.")
                            else:
                                st.error(msg_otp)
            
            if st.button(REGISTER_LABELS[lang]["btn_back"]):
                st.session_state["register_step"] = 1
                st.session_state["temp_reg_email"] = ""
                st.rerun()
    
    # --- KHU VỰC LIÊN KẾT CHUYỂN HƯỚNG NHANH ---
    if st.session_state["register_step"] == 1:
        st.write("")
        st.markdown("<div class='btn-outline'>", unsafe_allow_html=True)
        if st.button(REGISTER_LABELS[lang]["btn_have_account"], use_container_width=True):
            st.switch_page("auth/login.py")
        st.markdown("</div>", unsafe_allow_html=True)