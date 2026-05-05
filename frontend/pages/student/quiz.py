import streamlit as st
from utils.role_guard import require_role

require_role(["student"])

st.set_page_config(page_title="Làm Bài Quiz", page_icon="📝")

st.title("📝 Kho Bài Tập AI")
st.write("Hoàn thành bài tập để rèn luyện kiến thức và nhận thêm xu!")
st.divider()

st.subheader("Chưa hoàn thành")
with st.expander("Khám phá Hệ Mặt Trời (Khoa học) - Hạn: Hôm nay", expanded=True):
    st.write("**Câu 1: Hành tinh nào lớn nhất trong Hệ Mặt Trời?**")
    ans = st.radio("Chọn đáp án:", ["Trái Đất", "Sao Hỏa", "Sao Mộc", "Sao Kim"], key="q1")
    if st.button("Nộp bài"):
        st.success("Tuyệt vời! Bạn được cộng 10 Xu.")

with st.expander("Từ vựng chủ đề Động Vật (Tiếng Anh) - Hạn: Ngày mai"):
    st.write("Bấm vào để bắt đầu làm bài.")