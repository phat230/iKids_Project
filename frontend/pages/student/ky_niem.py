import streamlit as st
import os
from api_clients.tv3_client import get_memories, like_memory

st.set_page_config(page_title="Góc Kỷ Niệm", page_icon="📸")

# ================= HÀM ĐỌC FILE CSS (SỬA LỖI ĐƯỜNG DẪN) =================
def load_css(file_name):
    """
    Tự động tìm file CSS trong thư mục frontend/CSS/
    file_name: tên file kèm thư mục con, ví dụ 'student/ky_niem.css'
    """
    # Lấy đường dẫn tuyệt đối của thư mục chứa file hiện tại (frontend/pages/student)
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Lùi 2 cấp để về thư mục iKids_Project, sau đó vào frontend/CSS
    css_root = os.path.abspath(os.path.join(current_dir, "../../CSS"))
    full_path = os.path.join(css_root, file_name)

    if os.path.exists(full_path):
        with open(full_path, "r", encoding="utf-8") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    else:
        st.warning(f"⚠️ Không tìm thấy file CSS tại: {full_path}")

# Tải CSS (Chỉ truyền phần tên thư mục con và file nằm sau thư mục CSS/)
load_css("student/ky_niem.css")

# ================= GIAO DIỆN CHÍNH =================
st.title("📸 Góc Kỷ Niệm")
st.write("Nơi lưu giữ những khoảnh khắc học tập và vui chơi tuyệt vời của các bé!")
st.divider()

memories = get_memories()

if not memories:
    st.info("Chưa có kỷ niệm nào được chia sẻ.")
else:
    # Hiển thị giống dạng feed của mạng xã hội
    for item in memories:
        with st.container(border=True):
            # Phần tiêu đề bài đăng
            st.markdown(f"**👨‍🏫 {item.get('teacher_name', 'Giáo viên')}** đã chia sẻ một khoảnh khắc:")
            st.caption(f"🗓️ {item['created_at'][:16].replace('T', ' ')}")
            
            # Hiển thị ảnh
            st.image(item["media_url"], use_container_width=True)
            
            # Mô tả ảnh
            st.write(item["description"])
            
            # Khu vực tương tác (Thả tim)
            col1, col2 = st.columns([1, 5])
            with col1:
                # Đếm số tim
                likes = item.get('likes', 0)
                # Dùng key động để Streamlit phân biệt các nút thả tim khác nhau
                if st.button(f"❤️ {likes}", key=f"like_{item['_id']}"):
                    if like_memory(item['_id']):
                        st.rerun() # Load lại trang để cập nhật số tim ngay lập tức