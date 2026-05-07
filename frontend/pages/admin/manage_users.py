import streamlit as st
import requests

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
    
    submit = st.form_submit_button("🔥 Tạo tài khoản nhân sự")
    
    if submit:
        # Gọi API admin_create_staff (Bạn cần định nghĩa Route này ở Backend)
        payload = {
            "name": full_name,
            "email": email,
            "password": password,
            "role": role
        }
        headers = {"Authorization": f"Bearer {st.session_state.get('access_token')}"}
        
        try:
            # Lưu ý: Thay đổi URL đúng với Route bạn sẽ tạo
            res = requests.post("http://localhost:8000/api/auth/admin/create-user", 
                                json=payload, headers=headers)
            if res.status_code == 200:
                st.success(f"Đã tạo tài khoản {role} thành công!")
            else:
                st.error(f"Lỗi: {res.json().get('detail')}")
        except Exception as e:
            st.error(f"Không thể kết nối Backend: {e}")