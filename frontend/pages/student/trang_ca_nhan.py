import streamlit as st
from PIL import Image
import io
import base64
import requests

# 1. Hàm hỗ trợ hiển thị ảnh xem trước
def get_image_base64(image_bytes):
    return base64.b64encode(image_bytes).decode()

st.title("👤 Quản Lý Tài Khoản")

# 2. Lấy thông tin người dùng từ Session (Đồng bộ với app.py)
user_id = st.session_state.get("user_id")
user_info = st.session_state.get("user_info", {})

if not user_id:
    st.error("Vui lòng đăng nhập để tiếp tục.")
    st.stop()

# Lấy tên hiện tại từ user_info để làm giá trị mặc định
current_name = user_info.get("name", "Học sinh iKids")
new_full_name = st.text_input("Họ và Tên mới:", value=current_name)

st.divider()

# 3. PHẦN XỬ LÝ ẢNH ĐẠI DIỆN
st.write("🖼️ **Ảnh đại diện**")

# Kiểm tra nếu chưa chọn ảnh mới, hiển thị ảnh cũ từ Database nếu có
if "avatar_image" not in st.session_state:
    st.session_state.avatar_image = None

# Hiển thị ảnh hiện tại nếu chưa tải ảnh mới lên
old_avatar_url = user_info.get("avatar_url")
if st.session_state.avatar_image is None and old_avatar_url:
    st.image(f"http://localhost:8000/{old_avatar_url}", width=150, caption="Ảnh hiện tại")
    if st.button("Thay đổi ảnh"):
        st.session_state.avatar_image = None # Kích hoạt lại uploader

# Uploader ảnh mới
if st.session_state.avatar_image is None:
    uploaded_file = st.file_uploader("Tải ảnh đại diện từ máy tính", type=["jpg", "png", "jpeg"])
    if uploaded_file:
        st.session_state.avatar_image = uploaded_file.read()
        st.rerun()
else:
    # Giao diện điều chỉnh khung hình và xem trước ảnh mới
    shape = st.radio("Chọn kiểu khung hình:", ["Hình tròn ⚪", "Hình vuông 🟦"], horizontal=True)
    border_radius = "50%" if "tròn" in shape.lower() else "15px"

    img_base64 = get_image_base64(st.session_state.avatar_image)
    st.markdown(f"""
        <div style="display: flex; justify-content: center; margin: 20px 0;">
            <div style="
                width: 200px; height: 200px; 
                border: 4px solid #00adef; 
                border-radius: {border_radius}; 
                overflow: hidden;
                box-shadow: 0 4px 10px rgba(0,0,0,0.1);
            ">
                <img src="data:image/png;base64,{img_base64}" 
                     style="width: 100%; height: 100%; object-fit: cover;">
            </div>
        </div>
    """, unsafe_allow_html=True)

    if st.button("🔄 Chọn ảnh khác", key="change_avatar_btn"):
        st.session_state.avatar_image = None
        st.rerun()

st.divider()

# 4. NÚT LƯU ĐỒNG BỘ
if st.button("✅ Lưu tất cả thay đổi", key="main_save_btn", width="stretch"):
    with st.spinner("Đang lưu dữ liệu vĩnh viễn..."):
        payload = {"full_name": new_full_name}
        files = None
        if st.session_state.avatar_image:
            files = {"avatar_file": ("avatar.png", st.session_state.avatar_image, "image/png")}
        
        try:
            response = requests.post(
                f"http://localhost:8000/api/tv3/profile/update/{user_id}",
                data=payload,
                files=files
            )
            
            if response.status_code == 200:
                result = response.json()
                
                # CẬP NHẬT TRỰC TIẾP VÀO TÚI user_info ĐỂ app.py NHẬN DIỆN NGAY
                st.session_state["user_info"]["name"] = new_full_name
                if "avatar_url" in result:
                    st.session_state["user_info"]["avatar_url"] = result["avatar_url"]
                
                st.success("Thông tin tài khoản đã được cập nhật thành công!")
                st.balloons()
                st.rerun() # Reload để Sidebar hiển thị đúng tên mới
            else:
                st.error(f"Lỗi Server: {response.status_code}")
        except Exception as e:
            st.error(f"Lỗi kết nối Backend: {e}")