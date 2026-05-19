import streamlit as st
import requests
import os

# ================= CRITICAL: CẤU HÌNH TRANG LUÔN ĐỂ ĐẦU FILE =================
st.set_page_config(page_title="Quản trị hệ thống iKids", page_icon="🛡️", layout="wide")

# ================= HÀM ĐỌC FILE CSS (SỬA LỖI ĐƯỜNG DẪN TUYỆT ĐỐI) =================
def load_css(file_name):
    """
    Tự động tìm file CSS trong thư mục frontend/CSS/
    file_name: tên file kèm thư mục con, ví dụ 'admin/manage_academic.css'
    """
    current_dir = os.path.dirname(os.path.abspath(__file__))
    css_root = os.path.abspath(os.path.join(current_dir, "../../CSS"))
    full_path = os.path.join(css_root, file_name)

    if os.path.exists(full_path):
        with open(full_path, "r", encoding="utf-8") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    else:
        st.warning(f"⚠️ Không tìm thấy file CSS tại: {full_path}")

# Tải CSS làm đẹp
load_css("admin/manage_academic.css")

# Lấy cấu hình ngôn ngữ hiện hành từ session_state (Mặc định là "vi")
lang = st.session_state.get("lang", "vi")

# Bộ từ điển song ngữ chi tiết cho trang quản trị tài khoản nhân sự
ACADEMIC_LABELS = {
    "vi": {
        "title": "🛡️ Quản trị hệ thống iKids",
        "subtitle": "Quản lý cấp phát tài khoản nhân sự",
        "access_denied": "❌ Khu vực hạn chế. Vui lòng đăng nhập với quyền Admin.",
        "form_info": "💡 Sử dụng biểu mẫu này để tạo tài khoản cho Giáo viên hoặc Nhân viên vận hành.",
        "field_name": "Họ và tên (*)",
        "field_email": "Email đăng nhập (*)",
        "field_password": "Mật khẩu tạm thời (*)",
        "field_role": "Vai trò / Chức vụ (*)",
        "btn_submit": "👤 Tạo tài khoản nhân sự",
        "warn_empty": "⚠️ Vui lòng điền đầy đủ thông tin trước khi tạo.",
        "success_created": "🎉 Đã tạo tài khoản thành công!",
        "err_connection": "❌ Không thể kết nối Backend. Vui lòng bật Uvicorn!",
        
        # Vai trò tuyển chọn
        "role_teacher": "Giáo viên",
        "role_operator": "Nhân viên vận hành",
        "role_admin": "Quản trị viên"
    },
    "en": {
        "title": "🛡️ iKids System Administration",
        "subtitle": "Staff Account Provisioning & Management",
        "access_denied": "❌ Restricted Area. Please log in with Administrator privileges.",
        "form_info": "💡 Use this form to issue accounts for Teachers, Operators, or Admins.",
        "field_name": "Full Name (*)",
        "field_email": "Login Email Address (*)",
        "field_password": "Temporary Password (*)",
        "field_role": "System Role / Position (*)",
        "btn_submit": "👤 Create Staff Account",
        "warn_empty": "⚠️ Please fill in all required fields before submission.",
        "success_created": "🎉 Staff account created successfully!",
        "err_connection": "❌ Cannot connect to Backend. Please verify that Uvicorn is running!",
        
        # Roles mapped
        "role_teacher": "Teacher",
        "role_operator": "Operator",
        "role_admin": "Administrator"
    }
}

st.title(ACADEMIC_LABELS[lang]["title"])
st.subheader(ACADEMIC_LABELS[lang]["subtitle"])

# Kiểm tra quyền truy cập từ session_state bảo mật (Dùng cấu trúc kiểm tra rỗng nâng cao)
current_role = st.session_state.get("role") or st.session_state.get("user_info", {}).get("role", "")
if current_role.lower() != "admin":
    st.error(ACADEMIC_LABELS[lang]["access_denied"])
    st.stop()

# --- BIỂU MẪU ĐĂNG KÝ TÀI KHOẢN ---
with st.form("admin_create_user"):
    st.info(ACADEMIC_LABELS[lang]["form_info"])
    col1, col2 = st.columns(2)
    
    full_name = col1.text_input(ACADEMIC_LABELS[lang]["field_name"])
    email = col2.text_input(ACADEMIC_LABELS[lang]["field_email"])
    
    password = col1.text_input(ACADEMIC_LABELS[lang]["field_password"], type="password")
    
    # Cấu hình danh sách lựa chọn hiển thị theo ngôn ngữ nhưng lưu giá trị gốc (raw value) sang backend
    role_options = {
        ACADEMIC_LABELS[lang]["role_teacher"]: "teacher",
        ACADEMIC_LABELS[lang]["role_operator"]: "operator",
        ACADEMIC_LABELS[lang]["role_admin"]: "admin"
    }
    selected_role_display = col2.selectbox(ACADEMIC_LABELS[lang]["field_role"], options=list(role_options.keys()))
    role_raw_val = role_options[selected_role_display]
    
    submit = st.form_submit_button(ACADEMIC_LABELS[lang]["btn_submit"], type="primary", use_container_width=True)
    
    if submit:
        # Kiểm tra tính đầy đủ của thông tin phía Client
        if not full_name.strip() or not email.strip() or not password.strip():
            st.warning(ACADEMIC_LABELS[lang]["warn_empty"])
        else:
            # Đóng gói Payload dữ liệu gửi lên API Backend
            payload = {
                "name": full_name.strip(),
                "email": email.strip().lower(),
                "password": password,
                "role": role_raw_val
            }
            
            # Đồng bộ sử dụng biến access_token hoặc token linh hoạt từ hệ thống xác thực
            auth_token = st.session_state.get('access_token') or st.session_state.get('token', '')
            headers = {"Authorization": f"Bearer {auth_token}"}
            
            try:
                res = requests.post("http://localhost:8000/api/auth/admin/create-user", json=payload, headers=headers)
                
                if res.status_code == 200:
                    st.success(f"{ACADEMIC_LABELS[lang]['success_created']} [{selected_role_display}]")
                    st.balloons()
                else:
                    err_detail = res.json().get('detail', '')
                    # Chuyển ngữ thông báo lỗi tài khoản đã tồn tại phổ biến từ Backend
                    if lang == "en" and "đã tồn tại" in err_detail:
                        st.error("❌ This email address is already registered.")
                    else:
                        st.error(f"❌ {err_detail if err_detail else 'Error occurred'}")
            except Exception as e:
                st.error(f"{ACADEMIC_LABELS[lang]['err_connection']}: {e}")