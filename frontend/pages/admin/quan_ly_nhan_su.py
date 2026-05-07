import streamlit as st
import requests

st.title("🛡️ Quản trị iKids - Quản lý nhân sự")

# 1. Bảo vệ trang bằng cách check Role trong session_state
if "user_info" not in st.session_state or st.session_state["user_info"]["role"] != "admin":
    st.error("Bạn không có quyền truy cập trang này!")
    st.stop()

# 2. Giao diện tạo tài khoản
with st.container(border=True):
    st.subheader("➕ Cấp tài khoản mới")
    with st.form("form_create_staff"):
        name = st.text_input("Họ và tên nhân viên")
        email = st.text_input("Email đăng nhập")
        password = st.text_input("Mật khẩu tạm thời", type="password")
        role = st.selectbox("Vai trò", ["teacher", "operator", "admin"])
        
        if st.form_submit_button("🔥 Xác nhận tạo tài khoản"):
            if not name or not email or not password:
                st.warning("Vui lòng điền đầy đủ thông tin!")
            else:
                # Gửi request lên Backend
                headers = {"Authorization": f"Bearer {st.session_state['access_token']}"}
                payload = {
                    "name": name,
                    "email": email,
                    "password": password,
                    "role": role
                }
                try:
                    response = requests.post(
                        "http://localhost:8000/api/auth/admin/create-staff", 
                        json=payload, 
                        headers=headers
                    )
                    if response.status_code == 200:
                        st.success(f"Đã tạo thành công tài khoản {role} cho {name}!")
                        st.balloons()
                    else:
                        st.error(f"Lỗi: {response.json().get('detail')}")
                except Exception as e:
                    st.error(f"Không thể kết nối đến Backend: {e}")

# 3. Giao diện xem danh sách (Optional)
st.divider()
st.subheader("👥 Danh sách nhân sự hiện tại")
st.info("Chức năng liệt kê danh sách giáo viên/nhân viên sẽ hiển thị tại đây.")