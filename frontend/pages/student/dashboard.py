import streamlit as st
from api_clients.tv3_client import get_gamification_profile

st.title("🚀 Bảng Điều Khiển Của Chiến Binh Nhí")

# Lấy thông tin user đang đăng nhập
user_info = st.session_state.get("user_info", {"name": "Học sinh"})
# Tạm dùng ID mặc định là 1 để test, thực tế sẽ lấy từ token sau
student_id = 1 

# Gọi API lấy dữ liệu Gamification
profile = get_gamification_profile(student_id)

st.markdown(f"### Xin chào, {user_info['name']}! 🌟")

# Hiển thị 3 cột thông số cực kỳ quan trọng của TV3
col1, col2, col3 = st.columns(3)
with col1:
    st.info(f"💰 **iKids Xu:** {profile.get('total_coins', 0)}")
with col2:
    st.success(f"🏆 **Cấp bậc:** {profile.get('rank_level', 'Beginner')}")
with col3:
    st.warning(f"🔥 **Chuỗi ngày học:** {profile.get('current_streak', 0)} ngày")

st.divider()

# Khung nhiệm vụ mô phỏng
st.subheader("🎯 Nhiệm vụ hôm nay")
st.checkbox("Làm 1 bài Quiz AI (+10 Xu)")
st.checkbox("Xem 1 video bài giảng (+5 Xu)")
st.button("Hoàn thành nhiệm vụ", type="primary")