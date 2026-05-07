import streamlit as st
from api_clients.tv3_client import get_memories, like_memory

st.set_page_config(page_title="Góc Kỷ Niệm", page_icon="📸")

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