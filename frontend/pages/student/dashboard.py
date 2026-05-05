import streamlit as st
from utils.role_guard import require_role

# Bảo vệ trang, chỉ cho phép học sinh
require_role(["student"])

st.set_page_config(page_title="Dashboard Học Sinh", page_icon="🏠", layout="wide")

user_info = st.session_state.get("user_info", {"name": "Học sinh"})

st.title(f"🚀 Xin chào chiến binh không gian, {user_info['name']}!")
st.write("Chúc bạn một ngày học tập thật nhiều năng lượng!")
st.divider()

# Khối Gamification (Dữ liệu giả lập)
col1, col2, col3 = st.columns(3)
with col1:
    st.info("💰 Ví iKids Xu")
    st.metric(label="Số dư hiện tại", value="1,250 Xu", delta="+50 Xu hôm nay")
with col2:
    st.success("🏆 Danh hiệu")
    st.metric(label="Hạng hiện tại", value="Bạc 🥈", delta="Còn 250 xu lên Vàng")
with col3:
    st.warning("🔥 Chuỗi chăm chỉ")
    st.metric(label="Ngày học liên tiếp", value="12 Ngày", delta="Đang giữ phong độ!")

st.markdown("---")
st.subheader("📌 Nhiệm vụ hôm nay")
st.checkbox("Hoàn thành bài Quiz Tiếng Anh (Thưởng 20 Xu)")
st.checkbox("Xem video bài giảng Toán (Thưởng 15 Xu)")
st.checkbox("Tham gia lớp học đúng giờ (Thưởng 10 Xu)")