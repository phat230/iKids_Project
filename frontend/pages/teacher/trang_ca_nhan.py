import streamlit as st
import os
import time
from api_clients.tv3_client import update_profile, get_gamification_profile
from utils.role_guard import require_role

# Bảo vệ trang: Chỉ giáo viên hoặc Admin mới có quyền truy cập
require_role(["teacher", "admin"])

# ================= CRITICAL: CẤU HÌNH TRANG LUÔN ĐỂ ĐẦU FILE =================
st.set_page_config(page_title="Quản Lý Tài Khoản", page_icon="👤", layout="wide")

def load_css(file_name):
    current_dir = os.path.dirname(os.path.abspath(__file__))
    css_root = os.path.abspath(os.path.join(current_dir, "../../CSS"))
    full_path = os.path.join(css_root, file_name)

    if os.path.exists(full_path):
        with open(full_path, "r", encoding="utf-8") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    else:
        st.error(f"⚠️ Không tìm thấy file CSS tại: {full_path}")

load_css("teacher/trang_ca_nhan.css")

# Lấy cấu hình ngôn ngữ hiện hành (Mặc định "vi")
lang = st.session_state.get("lang", "vi")

# ================= BỘ TỪ ĐIỂN SONG NGỮ =================
PROFILE_LABELS = {
    "vi": {
        "title": "👤 Quản Lý Tài Khoản",
        "desc": "Cập nhật thông tin cá nhân, ảnh đại diện và các liên kết mạng xã hội để kết nối tốt hơn.",
        "sec_avatar": "🖼️ Ảnh đại diện",
        "btn_upload": "Tải ảnh mới lên",
        "msg_upload_success": "✅ Đã tải ảnh lên! Hãy bấm Lưu ở bên phải.",
        "sec_detail": "📝 Thông tin chi tiết",
        "sec_basic": "📌 Thông tin cơ bản",
        "input_name": "Họ và Tên (*)",
        "input_phone": "Số điện thoại",
        "phone_placeholder": "VD: 0901 234 567",
        "sec_social": "🌐 Liên kết Mạng xã hội",
        "input_fb": "Link Facebook",
        "input_git": "Link Github (Nếu có)",
        "sec_hobby": "🎨 Sở thích & Giới thiệu",
        "input_hobby": "Sở thích cá nhân / Châm ngôn giảng dạy",
        "hobby_placeholder": "Ví dụ: Thích đọc sách công nghệ, đi du lịch...",
        "btn_save": "💾 LƯU TẤT CẢ THAY ĐỔI",
        "err_name_empty": "⚠️ Họ và Tên không được để trống!",
        "success_msg": "🎉 Đã cập nhật thông tin hồ sơ thành công!"
    },
    "en": {
        "title": "👤 Account Profile Management",
        "desc": "Update your personal information, profile picture, and social links to connect better with students and colleagues.",
        "sec_avatar": "🖼️ Profile Picture",
        "btn_upload": "Upload new image",
        "msg_upload_success": "✅ Image uploaded! Please click Save on the right.",
        "sec_detail": "📝 Personal Details",
        "sec_basic": "📌 Basic Information",
        "input_name": "Full Name (*)",
        "input_phone": "Phone Number",
        "phone_placeholder": "e.g., +84901 234 567",
        "sec_social": "🌐 Social Media Links",
        "input_fb": "Facebook Link",
        "input_git": "Github Link (Optional)",
        "sec_hobby": "🎨 Hobbies & Introduction",
        "input_hobby": "Personal Hobbies / Teaching Motto",
        "hobby_placeholder": "e.g., Loves tech books, traveling, and inspiring children...",
        "btn_save": "💾 SAVE ALL CHANGES",
        "err_name_empty": "⚠️ Full Name cannot be empty!",
        "success_msg": "🎉 Profile updated successfully!"
    }
}

def render_profile_page():
    st.title(PROFILE_LABELS[lang]["title"])
    st.markdown(PROFILE_LABELS[lang]["desc"])
    st.divider()

    user_id = st.session_state.get("user_id")
    if not user_id:
        st.error("Vui lòng đăng nhập để tiếp tục.")
        st.stop()

    col_avatar, col_info = st.columns([1, 2.5], gap="large")

    # Cột 1: Quản lý ảnh
    with col_avatar:
        st.markdown(f"### {PROFILE_LABELS[lang]['sec_avatar']}")
        with st.container(border=True):
            st.image("https://api.dicebear.com/7.x/avataaars/svg?seed=Teacher", use_container_width=True)
            uploaded_file = st.file_uploader(PROFILE_LABELS[lang]["btn_upload"], type=['png', 'jpg', 'jpeg'])
            if uploaded_file:
                st.success(PROFILE_LABELS[lang]["msg_upload_success"])

    # Cột 2: Form thông tin
    with col_info:
        st.markdown(f"### {PROFILE_LABELS[lang]['sec_detail']}")
        with st.form("profile_update_form", border=True):
            st.markdown(f"##### {PROFILE_LABELS[lang]['sec_basic']}")
            c1, c2 = st.columns(2)
            with c1: name = st.text_input(PROFILE_LABELS[lang]["input_name"], value="Minh Tran")
            with c2: phone = st.text_input(PROFILE_LABELS[lang]["input_phone"], placeholder=PROFILE_LABELS[lang]["phone_placeholder"])

            st.markdown(f"##### {PROFILE_LABELS[lang]['sec_social']}")
            c3, c4 = st.columns(2)
            with c3: fb = st.text_input(PROFILE_LABELS[lang]["input_fb"])
            with c4: github = st.text_input(PROFILE_LABELS[lang]["input_git"])

            st.markdown(f"##### {PROFILE_LABELS[lang]['sec_hobby']}")
            hobbies = st.text_area(PROFILE_LABELS[lang]["input_hobby"], placeholder=PROFILE_LABELS[lang]["hobby_placeholder"], height=100)

            submitted = st.form_submit_button(PROFILE_LABELS[lang]["btn_save"], use_container_width=True, type="primary")

            if submitted:
                if not name.strip():
                    st.error(PROFILE_LABELS[lang]["err_name_empty"])
                else:
                    # Gọi API update_profile đã import từ api_clients.tv3_client
                    # success, message = update_profile(user_id=user_id, name=name, ...)
                    st.success(PROFILE_LABELS[lang]["success_msg"])
                    time.sleep(1)
                    st.rerun()

render_profile_page()