import streamlit as st
import requests
import os

st.set_page_config(page_title="Quản trị hệ thống iKids", page_icon="🛡️", layout="wide")

# ================= HÀM ĐỌC FILE CSS (SỬA LỖI ĐƯỜNG DẪN TUYỆT ĐỐI) =================
def load_css(file_name):
    """
    Tự động tìm file CSS trong thư mục frontend/CSS/
    file_name: tên file kèm thư mục con, ví dụ 'admin/manage_academic.css'
    """
    # Lấy đường dẫn tuyệt đối đến thư mục chứa file hiện tại (frontend/pages/admin)
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Tìm đường dẫn đến thư mục CSS (lùi 2 cấp rồi vào CSS/)
    css_root = os.path.abspath(os.path.join(current_dir, "../../CSS"))
    full_path = os.path.join(css_root, file_name)

    if os.path.exists(full_path):
        with open(full_path, "r", encoding="utf-8") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    else:
        st.warning(f"⚠️ Không tìm thấy file CSS tại: {full_path}")

# Tải CSS làm đẹp (Chỉ truyền phần sau thư mục CSS/)
load_css("admin/manage_academic.css")

st.title("🛡️ Quản trị hệ thống iKids")
st.subheader("Quản lý cấp phát tài khoản nhân sự")

# Kiểm tra quyền truy cập từ session_state
if st.session_state.get("user_info", {}).get("role") != "admin":
    st.error("Khu vực hạn chế. Vui lòng đăng nhập với quyền Admin.")
    st.stop()

with st.form("admin_create_user"):
    st.info("Sử dụng form này để tạo tài khoản cho Giáo viên hoặc Nhân viên vận hành.")
    col1, col2 = st.columns(2)
    
    full_name = col1.text_input("Họ và tên")
    email = col2.text_input("Email đăng nhập")
    
    password = col1.text_input("Mật khẩu tạm thời", type="password")
    role = col2.selectbox("Vai trò", ["teacher", "operator", "admin"])
    
    submit = st.form_submit_button("👤 Tạo tài khoản nhân sự", type="primary", use_container_width=True)
    
    if submit:
        # Kiểm tra tính đầy đủ của thông tin
        if not full_name or not email or not password:
            st.warning("Vui lòng điền đầy đủ thông tin trước khi tạo.")
        else:
            # Gọi API admin_create_staff
            payload = {
                "name": full_name,
                "email": email,
                "password": password,
                "role": role
            }
            headers = {"Authorization": f"Bearer {st.session_state.get('access_token')}"}
            
            try:
                # URL Backend
                res = requests.post("http://localhost:8000/api/auth/admin/create-user", 
                                    json=payload, headers=headers)
                
                if res.status_code == 200:
                    st.success(f"Đã tạo tài khoản {role} thành công!")
                    st.balloons()
                else:
                    st.error(f"Lỗi: {res.json().get('detail', 'Lỗi không xác định')}")
            except Exception as e:
                st.error(f"Không thể kết nối Backend: {e}")