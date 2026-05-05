import streamlit as st
from utils.role_guard import require_role

require_role(["student"])

st.set_page_config(page_title="Góc Kỷ Niệm", page_icon="📸", layout="centered")

st.title("📸 Góc Kỷ Niệm Lớp Học")
st.write("Lưu giữ những khoảnh khắc vui vẻ cùng bạn bè và thầy cô.")
st.divider()

# Bài post 1
with st.container(border=True):
    st.write("👩‍🏫 **Cô giáo Lan Anh** đã đăng một ảnh mới - *Hôm qua*")
    st.info("[Hình ảnh: Cả lớp đang làm bài tập nhóm môn Khoa học]")
    st.write("Các chiến binh nhí hôm nay làm thí nghiệm núi lửa phun trào cực kỳ tập trung luôn nha! 🥰")
    
    col1, col2 = st.columns([1, 5])
    with col1:
        st.button("❤️ 15")
    with col2:
        st.text_input("Bình luận...", key="cmt1", label_visibility="collapsed", placeholder="Viết bình luận...")

# Bài post 2
with st.container(border=True):
    st.write("👨‍🏫 **Thầy Quốc Bảo** đã đăng một ảnh mới - *Tuần trước*")
    st.info("[Hình ảnh: Lễ trao giải Cuộc thi Rung Chuông Vàng]")
    st.write("Chúc mừng bạn Nam đã giành giải Nhất nhé! 🏆")
    st.button("❤️ 32")