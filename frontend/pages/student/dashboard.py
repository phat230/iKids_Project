# frontend/pages/student/dashboard.py
import streamlit as st
from api_clients.tv3_client import get_gamification_profile

def show_dashboard():
    st.title("🌟 Bảng Điều Khiển Học Sinh")
    
    # 1. Lấy thông tin từ Session
    student_id = st.session_state.get("user_id")
    
    if not student_id:
        st.warning("Vui lòng đăng nhập để xem thông tin.")
        return

    # 2. Gọi API lấy dữ liệu thật (EXP, Rank, Balance)
    profile = get_gamification_profile(student_id)
    
    if profile:
        # Hiển thị chỉ số chính
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Điểm EXP", f"{profile.get('exp', 0)} ⭐")
        with col2:
            # Rank: Beginner -> Explorer -> Master [cite: 146]
            st.metric("Hạng hiện tại", profile.get("rank", "Beginner"))
        with col3:
            # Dùng tiền thật VNĐ thay vì coins [cite: 9, 125]
            st.metric("Số dư ví", f"{profile.get('balance', 0):,} VNĐ")
        
        st.success(f"Chào mừng trở lại, {profile.get('full_name', 'Học sinh')}!")

        st.divider()

        # 3. Thanh tiến trình thăng hạng (Gamification)
        st.subheader("🏆 Tiến trình thăng hạng")
        exp = profile.get('exp', 0)
        
        if exp < 1500:
            next_rank = "Explorer"
            progress = exp / 1500
            st.write(f"Còn **{1500 - exp} EXP** nữa để đạt hạng **{next_rank}**")
        elif exp < 5000:
            next_rank = "Master"
            progress = (exp - 1500) / (5000 - 1500)
            st.write(f"Còn **{5000 - exp} EXP** nữa để đạt hạng **{next_rank}**")
        else:
            progress = 1.0
            st.write("🌟 Chúc mừng! Bạn đã đạt hạng cao nhất: **Master**")
        
        st.progress(progress)

        st.divider()

        # 4. Bảng Nhiệm Vụ Hàng Ngày (Daily Missions) [cite: 161]
        st.subheader("🎯 Nhiệm vụ hôm nay")
        
        missions = [
            {"icon": "📺", "task": "Xem 1 video bài giảng AI", "exp": 30, "page": "pages/student/video.py"},
            {"icon": "📝", "task": "Hoàn thành 1 bài Quiz học tập", "exp": 50, "page": "pages/student/quiz.py"},
            {"icon": "✅", "task": "Điểm danh chuyên cần", "exp": 20, "page": None}
        ]

        for m in missions:
            m_col1, m_col2, m_col3 = st.columns([3, 1, 1])
            with m_col1:
                st.write(f"{m['icon']} {m['task']}")
            with m_col2:
                st.info(f"+{m['exp']} EXP")
            with m_col3:
                if m["page"]:
                    if st.button("Làm ngay", key=m["task"]):
                        st.switch_page(m["page"])
                else:
                    st.write("Tự động")

    else:
        st.error("Không thể kết nối dữ liệu học sinh.")

# Gọi hàm hiển thị
show_dashboard()