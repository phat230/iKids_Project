import streamlit as st

# KHÔNG dùng st.set_page_config ở đây nữa vì đã có ở app.py

st.title("📰 Trang Chủ Cộng Đồng iKids")
st.write("Cập nhật những tin tức, bài viết và sự kiện mới nhất từ trung tâm.")
st.divider()

# Bài viết 1
col1, col2 = st.columns([1, 3])
with col1:
    st.image("https://images.unsplash.com/photo-1503676260728-1c00da094a0b?w=500&q=80", use_container_width=True)
with col2:
    st.subheader("Bí quyết giúp trẻ tự giác học tập ở nhà")
    st.caption("Đăng ngày: 15/05/2026 | Chuyên mục: Dành cho Phụ huynh")
    st.write("Tự giác học tập không phải là bản năng, mà là một kỹ năng cần rèn luyện. Áp dụng phương pháp Pomodoro 25 phút kết hợp phần thưởng nhỏ sẽ giúp não bộ của bé tạo ra Dopamine, từ đó thích thú với việc học hơn...")
    if st.button("Đọc tiếp ▸", key="btn1"):
        st.info("Chức năng đang được cập nhật!")

st.markdown("---")

# Bài viết 2
col3, col4 = st.columns([1, 3])
with col3:
    st.image("https://images.unsplash.com/photo-1516321497487-e288fb19713f?w=500&q=80", use_container_width=True)
with col4:
    st.subheader("Sự kiện: Cuộc thi Rung Chuông Vàng 2026")
    st.caption("Đăng ngày: 12/05/2026 | Chuyên mục: Sự kiện")
    st.write("Tuần tới, trung tâm iKids sẽ tổ chức cuộc thi Rung Chuông Vàng dành cho tất cả học viên. Giải thưởng cao nhất lên tới 5,000 Xu và một chuyến dã ngoại.")
    if st.button("Đọc tiếp ▸", key="btn2"):
        st.info("Chức năng đang được cập nhật!")

# Gợi ý đăng nhập nếu chưa có token
if "token" not in st.session_state:
    st.sidebar.warning("Hãy đăng nhập để tham gia cộng đồng!")