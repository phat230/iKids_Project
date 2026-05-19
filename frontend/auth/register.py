import streamlit as st
import os
import time
from datetime import date
from utils.auth_state import register_user, verify_registration_otp

def load_auth_css():
    current_dir = os.path.dirname(os.path.abspath(__file__)) 
    css_path = os.path.abspath(os.path.join(current_dir, "../CSS/auth/style.css"))
    if os.path.exists(css_path):
        with open(css_path, "r", encoding="utf-8") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

load_auth_css()

# Khởi tạo các trạng thái Session State để điều khiển luồng nhập OTP
if "register_step" not in st.session_state:
    st.session_state["register_step"] = 1  # Bước 1: Nhập thông tin, Bước 2: Nhập OTP
if "temp_reg_email" not in st.session_state:
    st.session_state["temp_reg_email"] = ""

_, col, _ = st.columns([1, 1.5, 1])

with col:
    st.markdown("<div class='auth-header'>", unsafe_allow_html=True)
    st.markdown("<h2 class='auth-title'>Đăng Ký Phụ Huynh </h2>", unsafe_allow_html=True)
    st.markdown("<p class='auth-subtitle'>Tạo tài khoản để đồng hành cùng bé tại iKids</p>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

    with st.container(border=True):
        st.info(" Lưu ý: Tài khoản học sinh sẽ được tạo sau khi phụ huynh đăng nhập thành công.")
        
        # ==========================================
        # BƯỚC 1: ĐIỀN FORM ĐĂNG KÝ THÔNG TIN CÁ NHÂN
        # ==========================================
        if st.session_state["register_step"] == 1:
            with st.form("register_form"):
                reg_name = st.text_input(" Họ và Tên (*)")
                reg_email = st.text_input("Địa chỉ Email (*)")
                reg_phone = st.text_input("Số điện thoại (Nhận SMS OTP) (*)", placeholder="Ví dụ: 0912345678")
                
                # Widget chọn ngày sinh để Backend tự động tính toán độ tuổi phụ huynh
                reg_birth = st.date_input(
                    "Ngày tháng năm sinh của bạn (*)", 
                    min_value=date(1940, 1, 1),
                    max_value=date.today(),
                    value=date(1995, 1, 1)
                )
                
                reg_password = st.text_input(" Mật khẩu (*)", type="password")
                
                st.write("")
                submit_reg = st.form_submit_button("Tiếp Tục & Nhận OTP", use_container_width=True, type="primary")
                
                if submit_reg:
                    # Kiểm tra nhanh dữ liệu rỗng ở Client trước khi gửi đi
                    if not reg_name.strip() or not reg_email.strip() or not reg_phone.strip() or not reg_password:
                        st.error("⚠️ Vui lòng điền đầy đủ thông tin vào các trường bắt buộc (*)")
                    else:
                        # Gọi hàm đăng ký mở rộng trong auth_state.py
                        # Chuyển đổi reg_birth sang định dạng chuỗi ISO 'YYYY-MM-DD' để Pydantic dễ xử lý
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
                            st.success(msg)
                            time.sleep(1.5)
                            st.rerun()
                        else:
                            st.error(msg)
                            
        # ==========================================
        # BƯỚC 2: NHẬP MÃ XÁC THỰC TIN NHẮN OTP
        # ==========================================
        elif st.session_state["register_step"] == 2:
            st.warning(f"Mã xác thực OTP đã được gửi. Vui lòng kiểm tra Terminal backend hoặc tin nhắn di động gắn với tài khoản: {st.session_state['temp_reg_email']}")
            
            with st.form("otp_verify_form"):
                otp_code = st.text_input("Mã OTP Xác Thực (6 chữ số)", max_chars=6, placeholder="Nhập tại đây...")
                st.write("")
                submit_otp = st.form_submit_button("Kích Hoạt Tài Khoản", use_container_width=True, type="primary")
                
                if submit_otp:
                    if len(otp_code.strip()) != 6:
                        st.error("⚠️ Mã OTP phải có độ dài đúng 6 ký tự số.")
                    else:
                        # Gọi API xác thực kích hoạt tài khoản
                        success_otp, msg_otp = verify_registration_otp(
                            email=st.session_state["temp_reg_email"],
                            otp_code=otp_code.strip()
                        )
                        
                        if success_otp:
                            st.success("🎉 Tài khoản đã kích hoạt thành công! Hệ thống đang chuyển hướng...")
                            # Dọn dẹp session tạm sau khi đăng ký xong
                            st.session_state["register_step"] = 1
                            st.session_state["temp_reg_email"] = ""
                            time.sleep(2.0)
                            st.switch_page("auth/login.py")
                        else:
                            st.error(msg_otp)
            
            # Nút hủy bỏ luồng nhập OTP để quay lại điền thông tin mới
            if st.button("⬅️ Quay lại form đăng ký"):
                st.session_state["register_step"] = 1
                st.session_state["temp_reg_email"] = ""
                st.rerun()
    
    # Khu vực liên kết chuyển hướng nhanh sang đăng nhập
    if st.session_state["register_step"] == 1:
        st.write("")
        st.markdown("<div class='btn-outline'>", unsafe_allow_html=True)
        if st.button(" Đã có tài khoản? Đăng nhập tại đây", use_container_width=True):
            st.switch_page("auth/login.py")
        st.markdown("</div>", unsafe_allow_html=True)