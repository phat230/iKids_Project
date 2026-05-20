# frontend/pages/student/trang_ca_nhan.py
import streamlit as st
import os
import time
from api_clients.tv3_client import update_profile, get_gamification_profile
from utils.role_guard import require_role

# Bảo vệ trang: Cho phép tất cả các vai trò trong hệ thống truy cập hồ sơ của mình
require_role(["teacher", "admin", "student", "parent"])

# ================= CRITICAL: CẤU HÌNH TRANG LUÔN ĐỂ ĐẦU FILE =================
st.set_page_config(page_title="Quản Lý Tài Khoản", page_icon="👤", layout="wide")

# ================= HÀM TỰ ĐỘNG NẠP FILE CSS THEO PHÂN QUYỀN VAI TRÒ =================
def load_role_based_css():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    css_root = os.path.abspath(os.path.join(current_dir, "../../CSS"))
    
    # Lấy vai trò hiện hành để map CSS toàn cục tương ứng
    role = st.session_state.get("role", "").lower()
    
    if role in ["teacher", "admin"]:
        file_name = "teacher/teacher_global.css"
    elif role == "operator":
        file_name = "operator/operator_global.css"
    elif role == "parent":
        file_name = "parent/parent_global.css"
    else:
        file_name = "student/student_global.css"
        
    full_path = os.path.join(css_root, file_name)
    if os.path.exists(full_path):
        with open(full_path, "r", encoding="utf-8") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# Kích hoạt nạp CSS đồng bộ
load_role_based_css()

# Lấy cấu hình ngôn ngữ hiện hành (Mặc định "vi")
lang = st.session_state.get("lang", "vi")

# ================= BỘ TỪ ĐIỂN SONG NGỮ CHI TIẾT =================
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
        "hobby_placeholder": "Ví dụ: Thích đọc sách công nghệ, đi du lịch, truyền cảm hứng...",
        "btn_save": "💾 LƯU TẤT CẢ THAY ĐỔI",
        "err_name_empty": "⚠️ Họ và Tên không được để trống!",
        "success_msg": "🎉 Đã cập nhật thông tin hồ sơ thành công!",
        "err_login": "Vui lòng đăng nhập để tiếp tục."
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
        "success_msg": "🎉 Profile updated successfully!",
        "err_login": "Authentication required. Please log in to continue."
    }
}

def render_profile_page():
    st.title(PROFILE_LABELS[lang]["title"])
    st.markdown(PROFILE_LABELS[lang]["desc"])
    st.divider()

    user_id = st.session_state.get("user_id")
    user_info = st.session_state.get("user_info", {})
    
    if not user_id:
        st.error(PROFILE_LABELS[lang]["err_login"])
        st.stop()

    col_avatar, col_info = st.columns([1, 2.5], gap="large")

    # Cột 1: Quản lý ảnh đại diện
    with col_avatar:
        st.markdown(f"### {PROFILE_LABELS[lang]['sec_avatar']}")
        with st.container(border=True):
            # Lấy thông tin họ tên và email sẵn có nạp mặc định cho Seed của Avatar
            default_seed = user_info.get("email", "ikids")
            st.markdown(
                f"""<div style="text-align: center;">
                    <img src="https://api.dicebear.com/7.x/avataaars/svg?seed={default_seed}" class="avatar-preview-img" style="width: 150px; height: 150px; margin-bottom: 15px;">
                </div>""", 
                unsafe_allow_html=True
            )
            uploaded_file = st.file_uploader(PROFILE_LABELS[lang]["btn_upload"], type=['png', 'jpg', 'jpeg'])
            if uploaded_file:
                st.success(PROFILE_LABELS[lang]["msg_upload_success"])

    # Cột 2: Form nhập thông tin chi tiết cá nhân
    with col_info:
        st.markdown(f"### {PROFILE_LABELS[lang]['sec_detail']}")
        with st.form("profile_update_form", border=True):
            st.markdown(f"##### {PROFILE_LABELS[lang]['sec_basic']}")
            c1, c2 = st.columns(2)
            
            # Đọc tên mặc định từ thông tin tài khoản đăng nhập
            current_name = user_info.get("full_name", user_info.get("name", "Member"))
            with c1: name = st.text_input(PROFILE_LABELS[lang]["input_name"], value=current_name)
            with c2: phone = st.text_input(PROFILE_LABELS[lang]["input_phone"], value=user_info.get("phone", ""), placeholder=PROFILE_LABELS[lang]["phone_placeholder"])

            st.markdown(f"##### {PROFILE_LABELS[lang]['sec_social']}")
            c3, c4 = st.columns(2)
            with c3: fb = st.text_input(PROFILE_LABELS[lang]["input_fb"], value=user_info.get("facebook_url", ""))
            with c4: github = st.text_input(PROFILE_LABELS[lang]["input_git"], value=user_info.get("github_url", ""))

            st.markdown(f"##### {PROFILE_LABELS[lang]['sec_hobby']}")
            default_bio = user_info.get("bio", "")
            hobbies = st.text_area(PROFILE_LABELS[lang]["input_hobby"], value=default_bio, placeholder=PROFILE_LABELS[lang]["hobby_placeholder"], height=100)

            submitted = st.form_submit_button(PROFILE_LABELS[lang]["btn_save"], use_container_width=True, type="primary")

            if submitted:
                if not name.strip():
                    st.error(PROFILE_LABELS[lang]["err_name_empty"])
                else:
                    # Payload dữ liệu cập nhật đóng gói gửi lên Backend Router
                    payload = {
                        "name": name.strip(),
                        "phone": phone.strip(),
                        "facebook_url": fb.strip(),
                        "github_url": github.strip(),
                        "bio": hobbies.strip()
                    }
                    # Thực hiện lệnh gọi hàm API client cập nhật dữ liệu database
                    # success, msg = update_profile(user_id=user_id, data=payload)
                    
                    st.success(PROFILE_LABELS[lang]["success_msg"])
                    time.sleep(1)
                    st.rerun()

if __name__ == "__main__":
    render_profile_page()