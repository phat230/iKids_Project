import streamlit as st
import os
from api_clients.tv3_client import get_memories, like_memory

st.set_page_config(page_title="Góc Kỷ Niệm", page_icon="📸")

# ================= HÀM ĐỌC FILE CSS (SỬA LỖI ĐƯỜNG DẪN) =================
def load_css(file_name):
    """
    Tự động tìm file CSS trong thư mục frontend/CSS/
    file_name: tên file kèm thư mục con, ví dụ 'parent/ky_niem.css'
    """
    # Lấy đường dẫn tuyệt đối đến thư mục chứa file hiện tại (frontend/pages/parent)
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Tìm đường dẫn đến thư mục CSS (lùi 2 cấp rồi vào CSS/)
    css_root = os.path.abspath(os.path.join(current_dir, "../../CSS"))
    full_path = os.path.join(css_root, file_name)

    if os.path.exists(full_path):
        with open(full_path, "r", encoding="utf-8") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    else:
        st.warning(f"⚠️ Không tìm thấy file CSS tại: {full_path}")

# Tải CSS làm đẹp cho trang Kỷ Niệm (Chỉnh đường dẫn tương ứng với thư mục CSS của bạn)
load_css("parent/ky_niem.css")

# ================= GIAO DIỆN CHÍNH =================
st.title("📸 Góc Kỷ Niệm")
st.write("Nơi lưu giữ những khoảnh khắc học tập và vui chơi tuyệt vời của các bé!")
st.divider()

# Lấy dữ liệu từ API
try:
    memories = get_memories()
except Exception:
    memories = []

if not memories:
    st.info("✨ Hiện chưa có kỷ niệm nào được chia sẻ. Những khoảnh khắc đáng yêu sẽ xuất hiện tại đây!")
else:
    # Hiển thị giống dạng feed của mạng xã hội
    for item in memories:
        with st.container(border=True):
            # Phần tiêu đề bài đăng (Avatar giả lập & Tên giáo viên)
            col_head1, col_head2 = st.columns([1, 10])
            with col_head1:
                st.write("👤") # Có thể thay bằng ảnh đại diện nếu có
            with col_head2:
                st.markdown(f"**{item.get('teacher_name', 'Giáo viên iKids')}**")
                st.caption(f"🗓️ {item['created_at'][:16].replace('T', ' ')}")
            
            # Hiển thị ảnh kỷ niệm
            st.image(item["media_url"], use_container_width=True)
            
            # Mô tả ảnh
            st.markdown(f"<div class='memory-desc'>{item['description']}</div>", unsafe_allow_html=True)
            
            # Khu vực tương tác (Thả tim)
            st.divider()
            col1, col2 = st.columns([1, 5])
            with col1:
                # Đếm số tim
                likes = item.get('likes', 0)
                # Dùng key động để Streamlit phân biệt các nút
                if st.button(f"❤️ {likes}", key=f"like_{item['_id']}"):
                    if like_memory(item['_id']):
                        st.rerun() # Load lại để cập nhật số tim ngay lập tức
            with col2:
                st.caption("Hãy nhấn tim để ủng hộ khoảnh khắc này của bé!")