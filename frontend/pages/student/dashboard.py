import streamlit as st
import requests
import urllib.parse
import os

# ================= CRITICAL: CẤU HÌNH TRANG LUÔN ĐỂ ĐẦU FILE =================
st.set_page_config(page_title="Bảng Điều Khiển Học Sinh", page_icon="🏠", layout="wide")

# ================= HÀM ĐỌC FILE CSS (SỬA LỖI ĐƯỜNG DẪN) =================
def load_css(file_name):
    """
    Tự động tìm file CSS trong thư mục frontend/CSS/
    file_name: tên file kèm thư mục con, ví dụ 'student/dashboard.css'
    """
    current_dir = os.path.dirname(os.path.abspath(__file__))
    css_root = os.path.abspath(os.path.join(current_dir, "../../CSS"))
    full_path = os.path.join(css_root, file_name)

    if os.path.exists(full_path):
        with open(full_path, "r", encoding="utf-8") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    else:
        st.warning(f"⚠️ Không tìm thấy file CSS tại: {full_path}")

# Tải CSS làm đẹp cho trang Dashboard
load_css("student/student_global.css")
BACKEND_URL = st.session_state.get("api_url", "http://localhost:8000")
API_URL = BACKEND_URL
lang = st.session_state.get("lang", "vi")

# ==========================================
# BỘ TỪ ĐIỂN SONG NGỮ CHI TIẾT CHO STUDENT DASHBOARD
# ==========================================
DASHBOARD_LABELS = {
    "vi": {
        "title": "🏠 Bảng Điều Khiển Học Sinh",
        "welcome": "Chào mừng trở lại, {}! 👋",
        "metric_exp": "Điểm EXP",
        "metric_rank": "Hạng hiện tại",
        "metric_balance": "Số dư ví",
        
        # Tiến trình thăng hạng
        "sub_progress": "🏆 Tiến Trình Thăng Hạng",
        "progress_remaining": "Còn **{} EXP** nữa để đạt hạng **{}**",
        "progress_max": "🎉 Chúc mừng! Bạn đã đạt mức hạng cao nhất là Legend!",
        "rank_max_label": "Tối Đa",
        
        # Nhiệm vụ
        "sub_tasks": "🎯 Nhiệm Vụ Hôm Nay",
        "task_vid_title": "Xem 1 video bài giảng AI",
        "task_quiz_title": "Hoàn thành 1 bài Quiz học tập",
        "task_att_title": "Điểm danh chuyên cần",
        "btn_done": "Đã xong",
        "btn_go": "Làm ngay",
        "lbl_auto": "Tự động"
    },
    "en": {
        "title": "🏠 Student Dashboard",
        "welcome": "Welcome back, {}! 👋",
        "metric_exp": "EXP Points",
        "metric_rank": "Current Rank",
        "metric_balance": "Wallet Balance",
        
        # Rank Progress
        "sub_progress": "🏆 Rank Progression",
        "progress_remaining": "**{} EXP** remaining until you reach **{}** rank",
        "progress_max": "🎉 Congratulations! You have reached the maximum rank tier: Legend!",
        "rank_max_label": "Maxed",
        
        # Daily Tasks
        "sub_tasks": "🎯 Daily Quests & Tasks",
        "task_vid_title": "Watch 1 AI animated video lesson",
        "task_quiz_title": "Complete 1 learning practice Quiz",
        "task_att_title": "Daily attendance checkpoint",
        "btn_done": "Completed",
        "btn_go": "Start Quest",
        "lbl_auto": "Automated"
    }
}

# ================= HÀM LẤY TÊN USER =================
def load_student_username():
    """Tự động tìm tên tài khoản thật từ hệ thống đăng nhập"""
    if "username" in st.session_state and st.session_state.username: return st.session_state.username
    if "full_name" in st.session_state and st.session_state.full_name: return st.session_state.full_name
    if "user_info" in st.session_state and isinstance(st.session_state.user_info, dict):
        return st.session_state.user_info.get("full_name", st.session_state.user_info.get("name", "Student"))
    return "Student"

real_name = load_student_username()
encoded_name = urllib.parse.quote(real_name)

# ================= ĐỒNG BỘ PROFILE TỪ DATABASE =================
try:
    prof_res = requests.get(f"http://127.0.0.1:8000/api/tv2/student/{encoded_name}/profile", timeout=5)
    if prof_res.status_code == 200:
        student_profile = prof_res.json()
    else:
        student_profile = {"username": real_name, "exp": 0, "completed_tasks": []}
except Exception:
    student_profile = {"username": real_name, "exp": 0, "completed_tasks": []}

st.session_state.student_profile = student_profile

exp = student_profile.get("exp", 0)
completed_tasks = student_profile.get("completed_tasks", [])

# Lấy số dư thực tế của học sinh từ session_state (đã nạp lúc đăng nhập)
wallet_balance = st.session_state.get("balance", 0.0)

# ================= LOGIC TÍNH TOÁN THĂNG HẠNG =================
def get_rank_info(current_exp):
    ranks = [
        (0, "Beginner"),
        (500, "Explorer"),
        (1500, "Scholar"),
        (3000, "Expert"),
        (6000, "Master"),
        (10000, "Legend")
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
                exp_range = ranks[i+1][0] - ranks[i][0]
                exp_gained = current_exp - ranks[i][0]
                progress = exp_gained / exp_range
            else:
                next_rank = DASHBOARD_LABELS[lang]["rank_max_label"]
                exp_needed = current_exp
                progress = 1.0
        else:
            break
            
    return current_rank, next_rank, exp_needed, progress

current_rank, next_rank, exp_needed, progress = get_rank_info(exp)
exp_remaining = exp_needed - exp if next_rank != DASHBOARD_LABELS[lang]["rank_max_label"] else 0

# ================= RENDER GIAO DIỆN CHÍNH =================
st.title(DASHBOARD_LABELS[lang]["title"])

# 1. Hiển thị Thông số KPI thẻ điểm
col1, col2, col3 = st.columns(3)
col1.metric(DASHBOARD_LABELS[lang]["metric_exp"], f"{exp} EXP")
col2.metric(DASHBOARD_LABELS[lang]["metric_rank"], current_rank)
col3.metric(DASHBOARD_LABELS[lang]["metric_balance"], f"{wallet_balance:,.0f} VNĐ")

st.success(DASHBOARD_LABELS[lang]["welcome"].format(real_name))

# 2. Thanh Tiến trình Thăng hạng Gamification
st.markdown(f"### {DASHBOARD_LABELS[lang]['sub_progress']}")
if next_rank != DASHBOARD_LABELS[lang]["rank_max_label"]:
    st.write(DASHBOARD_LABELS[lang]["progress_remaining"].format(exp_remaining, next_rank))
    st.progress(progress)
else:
    st.write(DASHBOARD_LABELS[lang]["progress_max"])
    st.progress(1.0)

st.divider()

# 3. Danh sách nhiệm vụ hằng ngày (Daily Quests)
st.markdown(f"### {DASHBOARD_LABELS[lang]['sub_tasks']}")

# Quét mảng log xem học sinh đã hoàn thành những phân hệ nào
has_completed_video = any(str(task).startswith("vid_") for task in completed_tasks)
has_completed_quiz = any(str(task).startswith("quiz_") for task in completed_tasks)

# Quest 1: Xem Video bài giảng
c1, c2, c3 = st.columns([6, 2, 2])
with c1:
    if has_completed_video:
        st.markdown(f"<div class='task-text'>~~{DASHBOARD_LABELS[lang]['task_vid_title']}~~</div>", unsafe_allow_html=True)
    else:
        st.markdown(f"<div class='task-text'>{DASHBOARD_LABELS[lang]['task_vid_title']}</div>", unsafe_allow_html=True)
with c2:
    st.button("+30 EXP", disabled=True, key="btn_exp_vid", use_container_width=True)
with c3:
    if has_completed_video:
        st.button(DASHBOARD_LABELS[lang]["btn_done"], disabled=True, key="btn_do_vid", use_container_width=True)
    else:
        if st.button(DASHBOARD_LABELS[lang]["btn_go"], key="btn_do_vid_go", use_container_width=True, type="primary"):
            st.switch_page("pages/student/video.py")

# Quest 2: Làm bài luyện tập Quiz
c4, c5, c6 = st.columns([6, 2, 2])
with c4:
    if has_completed_quiz:
        st.markdown(f"<div class='task-text'>~~{DASHBOARD_LABELS[lang]['task_quiz_title']}~~</div>", unsafe_allow_html=True)
    else:
        st.markdown(f"<div class='task-text'>{DASHBOARD_LABELS[lang]['task_quiz_title']}</div>", unsafe_allow_html=True)
with c5:
    st.button("+50 EXP", disabled=True, key="btn_exp_quiz", use_container_width=True)
with c6:
    if has_completed_quiz:
        st.button(DASHBOARD_LABELS[lang]["btn_done"], disabled=True, key="btn_do_quiz", use_container_width=True)
    else:
        if st.button(DASHBOARD_LABELS[lang]["btn_go"], key="btn_do_quiz_go", use_container_width=True, type="primary"):
            st.switch_page("pages/student/quiz.py")

# Quest 3: Điểm danh chuyên cần tự động
c7, c8, c9 = st.columns([6, 2, 2])
with c7:
    st.markdown(f"<div class='task-text'>~~{DASHBOARD_LABELS[lang]['task_att_title']}~~</div>", unsafe_allow_html=True)
with c8:
    st.button("+20 EXP", disabled=True, key="btn_exp_att", use_container_width=True)
with c9:
    st.markdown(f"<div class='auto-text'>{DASHBOARD_LABELS[lang]['lbl_auto']}</div>", unsafe_allow_html=True)