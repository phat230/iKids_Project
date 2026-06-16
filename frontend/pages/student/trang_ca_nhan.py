import streamlit as st
import base64
import os
from datetime import date
import time
from api_clients.tv3_client import update_profile, get_gamification_profile
from utils.role_guard import require_role

require_role(["student", "parent", "admin"])

# ================= HÀM HỖ TRỢ =================

def load_css(file_name):
    current_dir = os.path.dirname(os.path.abspath(__file__))
    css_root = os.path.abspath(os.path.join(current_dir, "../../CSS"))
    full_path = os.path.join(css_root, file_name)

    if os.path.exists(full_path):
        with open(full_path, "r", encoding="utf-8") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    else:
        st.error(f"⚠️ Không tìm thấy file CSS tại: {full_path}")

def get_image_base64(image_bytes):
    """Chuyển đổi bytes ảnh sang base64 để hiển thị"""
    return base64.b64encode(image_bytes).decode()

# ================= CẤU HÌNH GIAO DIỆN =================

load_css("student/student_global.css")
BACKEND_URL = st.session_state.get("api_url", "http://localhost:8000")
lang = st.session_state.get("lang", "vi")

# ==========================================
# BỘ TỪ ĐIỂN SONG NGỮ CHI TIẾT CHO TRANG_CA_NHAN
# ==========================================
PROFILE_LABELS = {
    "vi": {
        "title": "⚙️ Quản Lý Hồ Sơ Cá Nhân",
        "err_login": "Vui lòng đăng nhập để tiếp tục.",
        "lbl_student_stats": "🏆 Cấp độ hiện tại: **{}** | ⭐ EXP: **{}**",
        "lbl_parent_stats": "💰 Số dư ví phụ huynh: **{:,} VNĐ**",
        "lbl_role_stats": "🔑 Vai trò: **{}**",
        
        # Thẻ thông tin cơ bản
        "sec_basic": "👤 Thông tin cơ bản",
        "input_name": "Họ và Tên hiện tại: (*)",
        "input_phone": "Số điện thoại liên hệ:",
        "phone_placeholder": "Ví dụ: 0912345678",
        
        # Thẻ thông tin bảo mật
        "sec_secure": "🔒 Thông tin mở rộng bảo mật",
        "input_birth": "Ngày tháng năm sinh:",
        
        # Ảnh đại diện
        "lbl_avatar": "📸 **Ảnh Đại Diện (Avatar)**",
        "caption_current_avatar": "Ảnh hiện tại",
        "warn_no_avatar": "Bạn chưa có ảnh đại diện.",
        "btn_upload_new": "Tải ảnh mới",
        "file_uploader_lbl": "Chọn tệp ảnh (JPG, PNG)",
        "btn_cancel_img": "Hủy chọn ảnh",
        
        # Nút hành động tổng thể
        "btn_save": "💾 Lưu Thông Tin Thay Đổi",
        "err_empty_name": "⚠️ Họ và Tên không được để trống!",
        "spinner_sync": "Đang đồng bộ dữ liệu...",
        "err_save_failed": "❌ Không thể lưu thay đổi:"
    },
    "en": {
        "title": "⚙️ Account Profile Settings",
        "err_login": "Authentication required. Please log in to continue.",
        "lbl_student_stats": "🏆 Current Rank: **{}** | ⭐ EXP: **{}**",
        "lbl_parent_stats": "💰 Parent Wallet Balance: **{:,} VND**",
        "lbl_role_stats": "🔑 Account Role: **{}**",
        
        # Basic Info
        "sec_basic": "👤 Personal Profile Data",
        "input_name": "Full Name Specification: (*)",
        "input_phone": "Contact Phone Number:",
        "phone_placeholder": "e.g., +84912345678",
        
        # Security Info
        "sec_secure": "🔒 Extended Security Metadata",
        "input_birth": "Date of Birth:",
        
        # Avatar Profile Image
        "lbl_avatar": "📸 **Profile Image (Avatar)**",
        "caption_current_avatar": "Current Avatar",
        "warn_no_avatar": "No profile image uploaded yet.",
        "btn_upload_new": "Upload New Image",
        "file_uploader_lbl": "Select image file format (JPG, PNG)",
        "btn_cancel_img": "Cancel Image Selection",
        
        # Main Submit Buttons
        "btn_save": "💾 Save Profile Specifications",
        "err_empty_name": "⚠️ Full Name field calculation cannot be empty!",
        "spinner_sync": "Synchronizing credential vectors...",
        "err_save_failed": "❌ Failed to overwrite profile changes:"
    }
}

st.title(PROFILE_LABELS[lang]["title"])

# Kiểm tra Session
user_id = st.session_state.get("user_id")
user_info = st.session_state.get("user_info", {})
role = st.session_state.get("role")

if not user_id:
    st.error(PROFILE_LABELS[lang]["err_login"])
    st.stop()

profile_data = get_gamification_profile(user_id)

# Render thanh trạng thái KPI theo từng loại tài khoản RBAC biệt lập
if role == "student":
    st.info(PROFILE_LABELS[lang]["lbl_student_stats"].format(profile_data.get('rank', 'Beginner'), profile_data.get('exp', 0)))
elif role == "parent":
    balance = profile_data.get('balance', 0)
    st.success(PROFILE_LABELS[lang]["lbl_parent_stats"].format(balance))
else:
    st.info(PROFILE_LABELS[lang]["lbl_role_stats"].format(str(role).upper()))

# ================= CÁC TRƯỜNG NHẬP THÔNG TIN CÁ NHÂN =================
st.markdown(f"##### {PROFILE_LABELS[lang]['sec_basic']}")
c1, c2 = st.columns(2)

with c1:
    current_name = user_info.get("full_name", user_info.get("name", "Người dùng iKids" if lang == 'vi' else "iKids User"))
    new_full_name = st.text_input(PROFILE_LABELS[lang]["input_name"], value=current_name)

with c2:
    current_phone = user_info.get("phone_number", "")
    new_phone = st.text_input(PROFILE_LABELS[lang]["input_phone"], value=current_phone, placeholder=PROFILE_LABELS[lang]["phone_placeholder"])

st.markdown("<br>", unsafe_allow_html=True)
st.markdown(f"##### {PROFILE_LABELS[lang]['sec_secure']}")

current_birth_str = user_info.get("birth_date", "2000-01-01")
try:
    default_birth = date.fromisoformat(current_birth_str)
except:
    default_birth = date(2000, 1, 1)

new_birth_date = st.date_input(PROFILE_LABELS[lang]["input_birth"], value=default_birth)

st.divider()

st.markdown(PROFILE_LABELS[lang]["lbl_avatar"])

if "temp_avatar" not in st.session_state:
    st.session_state.temp_avatar = None

# Luồng xử lý giao diện hiển thị ảnh đại diện cũ
old_avatar_url = user_info.get("avatar_url")
if st.session_state.temp_avatar is None:
    if old_avatar_url:
        st.image(f"http://localhost:8000{old_avatar_url}", width=150, caption=PROFILE_LABELS[lang]["caption_current_avatar"])
    else:
        st.warning(PROFILE_LABELS[lang]["warn_no_avatar"])
    
    if st.button(PROFILE_LABELS[lang]["btn_upload_new"]):
        st.session_state.temp_avatar = "uploading"
        st.rerun()

# Trình tải ảnh và kết xuất Preview ảnh mới qua Base64
if st.session_state.temp_avatar == "uploading":
    uploaded_file = st.file_uploader(PROFILE_LABELS[lang]["file_uploader_lbl"], type=["jpg", "png", "jpeg"])
    if uploaded_file:
        raw_data = uploaded_file.read()
        st.session_state.avatar_data = raw_data
        st.session_state.avatar_name = uploaded_file.name
        st.session_state.avatar_type = uploaded_file.type
        
        # Xem trước ảnh vừa chọn (Sử dụng class CSS bọc mượt)
        img_base64 = get_image_base64(raw_data)
        st.markdown(f"""
            <div class="avatar-preview-container">
                <img src="data:{uploaded_file.type};base64,{img_base64}" class="avatar-preview-img">
            </div>
        """, unsafe_allow_html=True)
        
        if st.button(PROFILE_LABELS[lang]["btn_cancel_img"]):
            st.session_state.temp_avatar = None
            st.rerun()

st.divider()

# ================= NÚT LƯU TỔNG THỂ VÀ ĐỒNG BỘ BACKEND =================
if st.button(PROFILE_LABELS[lang]["btn_save"], use_container_width=True, type="primary"):
    if not new_full_name.strip():
        st.error(PROFILE_LABELS[lang]["err_empty_name"])
    else:
        with st.spinner(PROFILE_LABELS[lang]["spinner_sync"]):
            avatar_file = None
            if st.session_state.temp_avatar == "uploading" and hasattr(st.session_state, "avatar_data"):
                class MockFile:
                    def __init__(self, name, data, type):
                        self.name = name
                        self.type = type
                        self._data = data
                    def getvalue(self): return self._data
                
                avatar_file = MockFile(st.session_state.avatar_name, st.session_state.avatar_data, st.session_state.avatar_type)

            success, message = update_profile(
                user_id=user_id, 
                name=new_full_name.strip(), 
                avatar_file=avatar_file,
                phone_number=new_phone.strip(),
                birth_date=new_birth_date.isoformat()
            )
            
            if success:
                if "user_info" not in st.session_state:
                    st.session_state["user_info"] = {}
                
                # Cập nhật nóng mảng dữ liệu phiên đăng nhập cục bộ
                st.session_state["user_info"]["full_name"] = new_full_name.strip()
                st.session_state["user_info"]["name"] = new_full_name.strip()
                st.session_state["user_info"]["phone_number"] = new_phone.strip()
                st.session_state["user_info"]["birth_date"] = new_birth_date.isoformat()
                
                # Bản dịch thông báo lưu thành công nếu backend phản hồi chuỗi Việt thô khi xem ở bản English
                if lang == "en" and "Thành công" in str(message):
                    st.success("🎉 Profile modifications updated successfully!")
                else:
                    st.success(message)
                    
                st.balloons()
                st.session_state.temp_avatar = None
                if hasattr(st.session_state, "avatar_data"):
                    del st.session_state.avatar_data
                time.sleep(1.5)
                st.rerun()
            else:
                if isinstance(message, list):
                    message = message[0].get("msg", "Dữ liệu nhập vào không hợp lệ." if lang == "vi" else "Invalid input data fields specified.")
                st.error(f"{PROFILE_LABELS[lang]['err_save_failed']} {message}")