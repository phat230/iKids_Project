import streamlit as st
import requests

API_URL = "http://localhost:8000/api/auth"

st.title("👨‍👩‍👦 Quản Lý Hồ Sơ Học Sinh")
st.write("Tại đây, bạn có thể tạo tài khoản cho bé để bé tham gia vào hệ thống học tập iKids.")

# Lấy ID thực tế của phụ huynh từ session
parent_id = st.session_state.get("user_id") 

if not parent_id:
    st.error("Không tìm thấy thông tin phiên đăng nhập. Vui lòng đăng nhập lại.")
    st.stop()

with st.form("create_student_form"):
    st.subheader("Tạo tài khoản mới cho bé")
    stu_name = st.text_input("Họ và tên của bé")
    stu_email = st.text_input("Email đăng nhập của bé (Có thể dùng email phụ của bạn)")
    stu_password = st.text_input("Mật khẩu", type="password")
    
    submit = st.form_submit_button("Tạo & Liên Kết Tài Khoản", use_container_width=True)
    
    if submit:
        if not stu_name or not stu_email or not stu_password:
            st.warning("Vui lòng điền đầy đủ thông tin.")
        else:
            payload = {
                "name": stu_name,
                "email": stu_email,
                "password": stu_password,
                "role": "student"
            }
            # Gửi kèm parent_id thật qua headers
            headers = {"parent-id": parent_id}
            
            try:
                res = requests.post(f"{API_URL}/parent/create-student", json=payload, headers=headers)
                if res.status_code == 200:
                    st.success("🎉 Đã tạo tài khoản cho bé thành công! Bé có thể dùng email và mật khẩu trên để đăng nhập.")
                else:
                    st.error(f"Lỗi: {res.json().get('detail', 'Không thể tạo tài khoản')}")
            except Exception as e:
                st.error("Lỗi kết nối đến máy chủ.")