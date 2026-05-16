import streamlit as st
import base64
import os
from api_clients.tv3_client import update_profile, get_gamification_profile
from utils.role_guard import require_role

# Bảo mật: Cho phép tất cả các vai trò đã đăng nhập truy cập vào trang hồ sơ của chính họ
require_role(["student", "parent", "admin"])

# ================= HÀM HỖ TRỢ (ĐÃ SỬA LỖI ĐƯỜNG DẪN CSS) =================

def load_css(file_name):
    """
    Tự động tìm file CSS trong thư mục frontend/CSS/
    file_name: tên file kèm thư mục con, ví dụ 'student/trang_ca_nhan.css'
    """
    # Lấy đường dẫn tuyệt đối của thư mục chứa file trang_ca_nhan.py hiện tại
    current_dir = os.path.dirname(os.path.abspath(__file__)) # frontend/pages/student
    
    # Tìm đường dẫn đến thư mục CSS (lùi 2 cấp rồi vào CSS/)
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

# Tải CSS từ file bên ngoài (Chỉ truyền phần tên thư mục con và file)
load_css("student/trang_ca_nhan.css")

st.title(" Quản Lý Hồ Sơ Cá Nhân")

# Kiểm tra Session
user_id = st.session_state.get("user_id")
user_info = st.session_state.get("user_info", {})
role = st.session_state.get("role")

if not user_id:
    st.error("Vui lòng đăng nhập để tiếp tục.")
    st.stop()

# HIỂN THỊ THÔNG TIN ĐẶC THÙ THEO VAI TRÒ
profile_data = get_gamification_profile(user_id)

if role == "student":
    st.info(f"🏆 Cấp độ hiện tại: **{profile_data.get('rank', 'Beginner')}** | ⭐ EXP: **{profile_data.get('exp', 0)}**")
elif role == "parent":
    balance = profile_data.get('balance', 0)
    st.success(f" Số dư ví phụ huynh: **{balance:,.0f} VNĐ**")
else:
    st.info(f" Vai trò: **{role.upper()}**")

# Nhập tên mới
current_name = user_info.get("full_name", user_info.get("name", "Người dùng iKids"))
new_full_name = st.text_input("Họ và Tên hiện tại:", value=current_name)

st.divider()

# PHẦN XỬ LÝ ẢNH ĐẠI DIỆN
st.write(" **Ảnh Đại Diện**")

if "temp_avatar" not in st.session_state:
    st.session_state.temp_avatar = None

# Hiển thị ảnh hiện tại
old_avatar_url = user_info.get("avatar_url")
if st.session_state.temp_avatar is None:
    if old_avatar_url:
        st.image(f"http://localhost:8000{old_avatar_url}", width=150, caption="Ảnh hiện tại")
    else:
        st.warning("Bạn chưa có ảnh đại diện.")
    
    if st.button("Tải ảnh mới"):
        st.session_state.temp_avatar = "uploading"
        st.rerun()

# Uploader và Xem trước
if st.session_state.temp_avatar == "uploading":
    uploaded_file = st.file_uploader("Chọn tệp ảnh (JPG, PNG)", type=["jpg", "png", "jpeg"])
    if uploaded_file:
        raw_data = uploaded_file.read()
        st.session_state.avatar_data = raw_data
        st.session_state.avatar_name = uploaded_file.name
        st.session_state.avatar_type = uploaded_file.type
        
        # Xem trước ảnh vừa chọn (Sử dụng class từ file CSS)
        img_base64 = get_image_base64(raw_data)
        st.markdown(f"""
            <div class="avatar-preview-container">
                <img src="data:{uploaded_file.type};base64,{img_base64}" class="avatar-preview-img">
            </div>
        """, unsafe_allow_html=True)
        
        if st.button("Hủy chọn ảnh"):
            st.session_state.temp_avatar = None
            st.rerun()

st.divider()

# NÚT LƯU TỔNG THỂ
if st.button(" Lưu Thông Tin Thay Đổi", use_container_width=True, type="primary"):
    with st.spinner("Đang đồng bộ dữ liệu..."):
        avatar_file = None
        if st.session_state.temp_avatar == "uploading" and hasattr(st.session_state, "avatar_data"):
            class MockFile:
                def __init__(self, name, data, type):
                    self.name = name
                    self.type = type
                    self._data = data
                def getvalue(self): return self._data
            
            avatar_file = MockFile(st.session_state.avatar_name, st.session_state.avatar_data, st.session_state.avatar_type)

        # Gọi API cập nhật
        success, message = update_profile(user_id, name=new_full_name, avatar_file=avatar_file)
        
        if success:
            if "user_info" not in st.session_state:
                st.session_state["user_info"] = {}
            st.session_state["user_info"]["full_name"] = new_full_name
            
            st.success(message)
            st.balloons()
            st.session_state.temp_avatar = None
            if hasattr(st.session_state, "avatar_data"):
                del st.session_state.avatar_data
            st.rerun()
        else:
            st.error(message)