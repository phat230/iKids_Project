import streamlit as st
import requests
import urllib.parse

st.set_page_config(page_title="Bảng Điều Khiển Học Sinh", page_icon="🌟", layout="wide")

# ================= HÀM LẤY TÊN USER =================
def get_current_username():
    """Tự động tìm tên tài khoản thật từ hệ thống đăng nhập"""
    if "username" in st.session_state and st.session_state.username: return st.session_state.username
    if "full_name" in st.session_state and st.session_state.full_name: return st.session_state.full_name
    if "user_info" in st.session_state and isinstance(st.session_state.user_info, dict):
        return st.session_state.user_info.get("full_name", st.session_state.user_info.get("name", "Học sinh"))
    return "Học sinh"

real_name = get_current_username()
encoded_name = urllib.parse.quote(real_name)

# ================= ĐỒNG BỘ PROFILE TỪ DATABASE =================
try:
    # Gọi API để lấy điểm thật từ MongoDB
    prof_res = requests.get(f"http://127.0.0.1:8000/api/tv2/student/{encoded_name}/profile", timeout=5)
    if prof_res.status_code == 200:
        student_profile = prof_res.json()
    else:
        student_profile = {"username": real_name, "exp": 0, "completed_tasks": []}
except Exception:
    student_profile = {"username": real_name, "exp": 0, "completed_tasks": []}

# Cập nhật session_state để các trang khác xài ké
st.session_state.student_profile = student_profile

exp = student_profile.get("exp", 0)
completed_tasks = student_profile.get("completed_tasks", [])

# ================= LOGIC TÍNH TOÁN THĂNG HẠNG (CHẾ ĐỘ HARDCORE) =================
def get_rank_info(current_exp):
    # Các mốc thăng hạng siêu khó
    ranks = [
        (0, "Beginner"),
        (500, "Explorer"),
        (1500, "Scholar"),
        (3000, "Expert"),
        (6000, "Master"),
        (10000, "Legend 👑")
    ]
    
    current_rank = ranks[0][1]
    next_rank = ranks[1][1]
    exp_needed = ranks[1][0]
    progress = 0.0

    for i in range(len(ranks)):
        if current_exp >= ranks[i][0]:
            current_rank = ranks[i][1]
            if i + 1 < len(ranks):
                next_rank = ranks[i+1][1]
                exp_needed = ranks[i+1][0]
                # Tính % cho thanh tiến trình
                exp_range = ranks[i+1][0] - ranks[i][0]
                exp_gained = current_exp - ranks[i][0]
                progress = exp_gained / exp_range
            else:
                next_rank = "Tối Đa"
                exp_needed = current_exp
                progress = 1.0
        else:
            break
            
    return current_rank, next_rank, exp_needed, progress

current_rank, next_rank, exp_needed, progress = get_rank_info(exp)
exp_remaining = exp_needed - exp if next_rank != "Tối Đa" else 0

# ================= GIAO DIỆN CHÍNH =================
st.title("🌟 Bảng Điều Khiển Học Sinh")

# 1. Hiển thị Thông số
col1, col2, col3 = st.columns(3)
col1.metric("Điểm EXP", f"{exp} ⭐")
col2.metric("Hạng hiện tại", current_rank)
col3.metric("Số dư ví", "0.0 VNĐ")

st.success(f"Chào mừng trở lại, {real_name}!")

# 2. Thanh Tiến trình Thăng hạng
st.markdown("### 🏆 Tiến trình thăng hạng")
if next_rank != "Tối Đa":
    st.write(f"Còn **{exp_remaining} EXP** nữa để đạt hạng **{next_rank}**")
    st.progress(progress)
else:
    st.write("🎉 Chúc mừng! Bạn đã đạt mức hạng cao nhất là Legend 👑!")
    st.progress(1.0)

st.divider()

# 3. Nhiệm vụ hôm nay
st.markdown("### 🎯 Nhiệm vụ hôm nay")

# Quét xem đã làm bài nào chưa (Dựa vào ID lưu trong DB)
has_completed_video = any(str(task).startswith("vid_") for task in completed_tasks)
has_completed_quiz = any(str(task).startswith("quiz_") for task in completed_tasks)

# Task 1: Xem Video
c1, c2, c3 = st.columns([6, 2, 2])
with c1:
    if has_completed_video:
        st.markdown("✅ ~~Xem 1 video bài giảng AI~~")
    else:
        st.markdown("📺 Xem 1 video bài giảng AI")
with c2:
    st.button("+30 EXP", disabled=True, key="btn_exp_vid", use_container_width=True)
with c3:
    if has_completed_video:
        st.button("Đã xong", disabled=True, key="btn_do_vid", use_container_width=True)
    else:
        if st.button("Làm ngay", key="btn_do_vid_go", use_container_width=True):
            st.switch_page("pages/student/video.py")

# Task 2: Làm Quiz
c4, c5, c6 = st.columns([6, 2, 2])
with c4:
    if has_completed_quiz:
        st.markdown("✅ ~~Hoàn thành 1 bài Quiz học tập~~")
    else:
        st.markdown("📝 Hoàn thành 1 bài Quiz học tập")
with c5:
    st.button("+50 EXP", disabled=True, key="btn_exp_quiz", use_container_width=True)
with c6:
    if has_completed_quiz:
        st.button("Đã xong", disabled=True, key="btn_do_quiz", use_container_width=True)
    else:
        if st.button("Làm ngay", key="btn_do_quiz_go", use_container_width=True):
            st.switch_page("pages/student/quiz.py")

# Task 3: Điểm danh (Mặc định cho sẵn)
c7, c8, c9 = st.columns([6, 2, 2])
with c7:
    st.markdown("✅ ~~Điểm danh chuyên cần~~")
with c8:
    st.button("+20 EXP", disabled=True, key="btn_exp_att", use_container_width=True)
with c9:
    st.write("<div style='margin-top:10px; color:gray;'>Tự động</div>", unsafe_allow_html=True)