import streamlit as st
import requests
import pandas as pd
import os

# ================= CRITICAL: CẤU HÌNH TRANG LUÔN ĐỂ ĐẦU FILE =================
st.set_page_config(page_title="Admin Dashboard - iKids", layout="wide", initial_sidebar_state="expanded", page_icon=None)

# ================= HÀM ĐỌC FILE CSS =================
def load_css(file_name):
    """
    Tự động tìm file CSS trong thư mục frontend/CSS/
    file_name: tên file kèm thư mục con, ví dụ 'admin/dashboard.css'
    """
    current_dir = os.path.dirname(os.path.abspath(__file__))
    css_root = os.path.abspath(os.path.join(current_dir, "../../CSS"))
    full_path = os.path.join(css_root, file_name)

    if os.path.exists(full_path):
        with open(full_path, "r", encoding="utf-8") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    else:
        st.warning(f"Canh bao: Khong tim thay file CSS tai: {full_path}")

# Tải CSS làm đẹp
load_css("admin/dashboard.css")

# Lấy mã ngôn ngữ hiện hành (Mặc định là "vi")
lang = st.session_state.get("lang", "vi")

# ================= BỘ TỪ ĐIỂN SONG NGỮ CHO ADMIN DASHBOARD =================
DASHBOARD_LABELS = {
    "vi": {
        "title": "Bảng Điều Khiển Quản Trị Trung Tâm",
        "subtitle": "*Hệ thống giám sát vận hành đồng bộ: Lịch dạy (TV1), Học thuật & AI (TV2), Cộng đồng (TV3)*",
        "metric_tv1_pending": "ĐƠN GV CHỜ DUYỆT (TV1)",
        "metric_tv1_today": "CA DẠY HÔM NAY (TV1)",
        "metric_tv2_logs": "NHẬT KÝ ĐÃ NỘP (TV2)",
        "metric_tv3_issues": "SỰ CỐ NẠP TIỀN (TV3)",
        "caption_mongo": "Dữ liệu trực tiếp từ MongoDB",
        "caption_updating": "Đang cập nhật luồng API",
        "caption_deposit": "Dữ liệu từ deposit_issues",
        
        "section_tv1": "1. Phê duyệt & Điều phối",
        "sub_tv1_pending": "A. Yêu cầu đang chờ duyệt",
        "sub_tv1_history": "B. Lịch sử xét duyệt gần đây",
        "no_requests": "Không có đơn hỗ trợ nào cần xử lý.",
        "btn_approve": "Duyệt",
        "btn_reject": "Từ chối",
        
        "table_teacher": "Giáo viên",
        "table_type": "Loại đơn",
        "table_detail": "Chi tiết",
        "table_time": "Thời gian xử lý",
        "table_status": "Trạng thái",
        "status_approved": "Đã duyệt",
        "status_rejected": "Từ chối",
        
        "section_tv2_tv3": "2. Học thuật & Tương tác",
        "sub_tv2": "A. Quản Lý Nội Dung Học Thuật",
        "tab_quiz": "Kho Bài Tập",
        "tab_video": "Kho Video",
        "no_quizzes": "Chưa có bộ đề nào.",
        "no_videos": "Chưa có video nào.",
        "author": "Tác giả",
        "questions_count": "Số câu hỏi",
        "topic": "Chủ đề",
        "likes": "Lượt thích",
        "btn_view": "Xem",
        "btn_back": "Quay Lại",
        "answer": "Đáp án",
        
        "sub_tv3": "B. Trung tâm Tương tác Phụ huynh (TV3)",
        "no_deposits": "Không có sự cố nạp tiền.",
        "btn_check": "Kiểm tra",
        "msg_success": "Hoàn tất!",
        "msg_saved": "Đã lưu.",
        
        "sub_parent_leave": "C. Yêu cầu xin nghỉ từ Phụ huynh",
        "info_leave_sync": "Yêu cầu xin nghỉ học sẽ được tự động đồng bộ sang bộ phận Vận hành (TV1)."
    },
    "en": {
        "title": "Central Administration Dashboard",
        "subtitle": "*Synchronized Monitoring System: Scheduling (TV1), Academics & AI (TV2), Community (TV3)*",
        "metric_tv1_pending": "TEACHER REQUESTS PENDING (TV1)",
        "metric_tv1_today": "CLASSES TODAY (TV1)",
        "metric_tv2_logs": "JOURNALS SUBMITTED (TV2)",
        "metric_tv3_issues": "DEPOSIT ISSUES (TV3)",
        "caption_mongo": "Live data from MongoDB",
        "caption_updating": "Updating API streams",
        "caption_deposit": "Data from deposit_issues",
        
        "section_tv1": "1. Approval & Coordination",
        "sub_tv1_pending": "A. Pending Requests",
        "sub_tv1_history": "B. Recent Approval History",
        "no_requests": "No support requests require processing.",
        "btn_approve": "Approve",
        "btn_reject": "Reject",
        
        "table_teacher": "Teacher",
        "table_type": "Request Type",
        "table_detail": "Details",
        "table_time": "Processed Time",
        "table_status": "Status",
        "status_approved": "Approved",
        "status_rejected": "Rejected",
        
        "section_tv2_tv3": "2. Academics & Interaction",
        "sub_tv2": "A. Academic Content Management",
        "tab_quiz": "Quiz Repository",
        "tab_video": "Video Repository",
        "no_quizzes": "No quizzes available.",
        "no_videos": "No videos available.",
        "author": "Author",
        "questions_count": "Questions",
        "topic": "Topic",
        "likes": "Likes",
        "btn_view": "View",
        "btn_back": "Back",
        "answer": "Answer",
        
        "sub_tv3": "B. Parent Interaction Center (TV3)",
        "no_deposits": "No pending deposit issues.",
        "btn_check": "Check",
        "msg_success": "Completed!",
        "msg_saved": "Saved.",
        
        "sub_parent_leave": "C. Parent Leave Requests",
        "info_leave_sync": "Student leave requests will be automatically synchronized with Operations (TV1)."
    }
}

# ================= KHỞI TẠO SESSION STATE CHO TV2 =================
if "admin_tv2_view" not in st.session_state:
    st.session_state.admin_tv2_view = "list"
if "admin_tv2_item" not in st.session_state:
    st.session_state.admin_tv2_item = None
if "admin_tv2_type" not in st.session_state:
    st.session_state.admin_tv2_type = None

# Cấu hình địa chỉ Backend
API_URL = "http://127.0.0.1:8000"
API_TV3 = f"{API_URL}/api/tv3"

# --- CÁC HÀM GỌI API ---
def fetch_pending_requests():
    try:
        res = requests.get(f"{API_URL}/pending-requests")
        return res.json() if res.status_code == 200 else []
    except: return []

def fetch_history_requests():
    try:
        res = requests.get(f"{API_URL}/request-history")
        return res.json() if res.status_code == 200 else []
    except: return []

def fetch_deposit_issues():
    try:
        res = requests.get(f"{API_TV3}/admin/deposit-issues")
        return res.json() if res.status_code == 200 else []
    except: return []

def approve_deposit_issue(issue_id):
    try:
        res = requests.post(f"{API_TV3}/admin/resolve-deposit/{issue_id}")
        return res.status_code == 200
    except: return False

# --- HEADER ---
st.title(DASHBOARD_LABELS[lang]["title"])
st.markdown(DASHBOARD_LABELS[lang]["subtitle"])
st.write("---")

# --- 1. CHỈ SỐ TỔNG QUAN ---
pending_requests = fetch_pending_requests()
total_pending_tv1 = len(pending_requests)
deposit_issues = fetch_deposit_issues()
total_pending_tv3 = len(deposit_issues)

col1, col2, col3, col4 = st.columns(4)
with col1:
    st.markdown(f"""<div class="metric-card tv1-border">
        <p class="metric-label">{DASHBOARD_LABELS[lang]['metric_tv1_pending']}</p>
        <h2 class="metric-value">{total_pending_tv1}</h2>
        <p class="metric-caption caption-red">{DASHBOARD_LABELS[lang]['caption_mongo']}</p></div>""", unsafe_allow_html=True)
with col2:
    st.markdown(f"""<div class="metric-card tv1-border">
        <p class="metric-label">{DASHBOARD_LABELS[lang]['metric_tv1_today']}</p>
        <h2 class="metric-value">--</h2>
        <p class="metric-caption caption-green">{DASHBOARD_LABELS[lang]['caption_updating']}</p></div>""", unsafe_allow_html=True)
with col3:
    st.markdown(f"""<div class="metric-card tv2-border">
        <p class="metric-label">{DASHBOARD_LABELS[lang]['metric_tv2_logs']}</p>
        <h2 class="metric-value">--</h2>
        <p class="metric-caption caption-orange">{DASHBOARD_LABELS[lang]['caption_updating']}</p></div>""", unsafe_allow_html=True)
with col4:
    st.markdown(f"""<div class="metric-card tv3-border">
        <p class="metric-label">{DASHBOARD_LABELS[lang]['metric_tv3_issues']}</p>
        <h2 class="metric-value">{total_pending_tv3}</h2>
        <p class="metric-caption caption-blue">{DASHBOARD_LABELS[lang]['caption_deposit']}</p></div>""", unsafe_allow_html=True)

st.write("<br>", unsafe_allow_html=True)

# --- LAYOUT CHÍNH: CHIA 2 CỘT ---
left_col, right_col = st.columns([1.6, 1])

# --- CỘT TRÁI: TV1 ---
with left_col:
    st.subheader(DASHBOARD_LABELS[lang]["section_tv1"])
    st.markdown(f"**{DASHBOARD_LABELS[lang]['sub_tv1_pending']} ({total_pending_tv1})**")
    
    if not pending_requests:
        st.success(DASHBOARD_LABELS[lang]["no_requests"])
    else:
        tv1_container = st.container(height=400) if len(pending_requests) > 3 else st.container()
        with tv1_container:
            for req in pending_requests:
                with st.container(border=True):
                    c_info, c_btn = st.columns([3, 1])
                    with c_info:
                        req_id = req.get('id', req.get('_id', ''))
                        req_type = req.get('type', 'Yêu cầu')
                        teacher_name = req.get('teacher_name', 'Không rõ') if lang == "vi" else req.get('teacher_name', 'Unknown')
                        
                        st.markdown(f"**{req_type} - GV: {teacher_name}**")
                        st.caption(f"**{DASHBOARD_LABELS[lang]['table_detail']}:** {req.get('details', req.get('class_name', ''))} | **{'Ngày gửi' if lang == 'vi' else 'Sent Date'}:** {req.get('created_at', req.get('date', ''))}")
                        st.markdown(f"**{'Lý do' if lang == 'vi' else 'Reason'}:** {req.get('reason', '')}")
                    with c_btn:
                        if st.button(DASHBOARD_LABELS[lang]["btn_approve"], key=f"app_{req_id}", type="primary", use_container_width=True):
                            res = requests.post(f"{API_URL}/approve/{req_id}")
                            if res.status_code == 200: st.rerun()
                        if st.button(DASHBOARD_LABELS[lang]["btn_reject"], key=f"rej_{req_id}", use_container_width=True):
                            res = requests.post(f"{API_URL}/reject/{req_id}")
                            if res.status_code == 200: st.rerun()

    st.write("---")
    st.markdown(f"**{DASHBOARD_LABELS[lang]['sub_tv1_history']}**")
    history_requests = fetch_history_requests()
    if history_requests:
        history_data = []
        for h in history_requests:
            status_text = DASHBOARD_LABELS[lang]["status_approved"] if h.get('status') == "approved" else DASHBOARD_LABELS[lang]["status_rejected"]
            raw_time = h.get("updated_at", h.get("created_at", ""))
            try:
                time_str = pd.to_datetime(raw_time).strftime("%d/%m/%Y %H:%M") if raw_time else ("Chưa rõ" if lang == "vi" else "Unknown")
            except:
                time_str = raw_time
                
            history_data.append({
                DASHBOARD_LABELS[lang]["table_teacher"]: h.get("teacher_name", ""),
                DASHBOARD_LABELS[lang]["table_type"]: h.get("type", ""),
                DASHBOARD_LABELS[lang]["table_detail"]: h.get("details", h.get("class_name", "")), 
                DASHBOARD_LABELS[lang]["table_time"]: time_str,
                DASHBOARD_LABELS[lang]["table_status"]: status_text
            })
        st.dataframe(pd.DataFrame(history_data), use_container_width=True, hide_index=True)

# --- CỘT PHẢI: TV2 & TV3 ---
with right_col:
    st.subheader(DASHBOARD_LABELS[lang]["section_tv2_tv3"])
    with st.container(border=True):
        st.markdown(f"**{DASHBOARD_LABELS[lang]['sub_tv2']}**")
        if st.session_state.admin_tv2_view == "list":
            try: quizzes = requests.get(f"{API_URL}/api/tv2/quizzes").json()
            except: quizzes = []
            try: videos = requests.get(f"{API_URL}/api/tv2/videos").json()
            except: videos = []
            
            tab_quiz, tab_video = st.tabs([DASHBOARD_LABELS[lang]["tab_quiz"], DASHBOARD_LABELS[lang]["tab_video"]])
            with tab_quiz:
                if not quizzes: st.info(DASHBOARD_LABELS[lang]["no_quizzes"])
                else:
                    quiz_container = st.container(height=350) if len(quizzes) > 3 else st.container()
                    with quiz_container:
                        for q in quizzes:
                            with st.container(border=True):
                                col_q1, col_q2 = st.columns([4, 1])
                                author = q.get("author", q.get("author_email", "Hệ thống" if lang == "vi" else "System"))
                                col_q1.markdown(f"**{q.get('title', 'N/A')}**")
                                col_q1.caption(f"{DASHBOARD_LABELS[lang]['author']}: {author} | {DASHBOARD_LABELS[lang]['questions_count']}: {len(q.get('questions', []))}")
                                if col_q2.button(DASHBOARD_LABELS[lang]["btn_view"], key=f"ad_view_q_{q.get('id')}", use_container_width=True):
                                    st.session_state.admin_tv2_item, st.session_state.admin_tv2_type, st.session_state.admin_tv2_view = q, "quiz", "detail"
                                    st.rerun()
            with tab_video:
                if not videos: st.info(DASHBOARD_LABELS[lang]["no_videos"])
                else:
                    vid_container = st.container(height=350) if len(videos) > 3 else st.container()
                    with vid_container:
                        for v in videos:
                            with st.container(border=True):
                                col_v1, col_v2 = st.columns([4, 1])
                                col_v1.markdown(f"**{v.get('title', 'N/A')}**")
                                col_v1.caption(f"{DASHBOARD_LABELS[lang]['topic']}: {v.get('topic')} | {DASHBOARD_LABELS[lang]['likes']}: {v.get('likes', 0)}")
                                if col_v2.button(DASHBOARD_LABELS[lang]["btn_view"], key=f"ad_view_v_{v.get('id')}", use_container_width=True):
                                    st.session_state.admin_tv2_item, st.session_state.admin_tv2_type, st.session_state.admin_tv2_view = v, "video", "detail"
                                    st.rerun()
        else:
            if st.button(DASHBOARD_LABELS[lang]["btn_back"], type="primary"):
                st.session_state.admin_tv2_view, st.session_state.admin_tv2_item = "list", None
                st.rerun()
                
            item = st.session_state.admin_tv2_item
            if st.session_state.admin_tv2_type == "quiz":
                st.subheader(f"{item.get('title')}")
                with st.container(height=300):
                    for idx, q_item in enumerate(item.get("questions", [])):
                        st.markdown(f"**{'Câu' if lang == 'vi' else 'Question'} {idx + 1}: {q_item.get('question')}**")
                        st.success(f"{DASHBOARD_LABELS[lang]['answer']}: {q_item.get('correct_password', q_item.get('correct_answer'))}")
            elif st.session_state.admin_tv2_type == "video":
                st.subheader(f"{item.get('title')}")
                st.video(item.get('url'))

    with st.container(border=True):
        st.markdown(f"**{DASHBOARD_LABELS[lang]['sub_tv3']}**")
        if not deposit_issues: 
            st.success(DASHBOARD_LABELS[lang]["no_deposits"])
        else:
            tv3_container = st.container(height=350) if len(deposit_issues) > 2 else st.container()
            with tv3_container:
                for issue in deposit_issues:
                    with st.container(border=True):
                        st.markdown(f"### {issue.get('amount', 0):,.0f} VNĐ")
                        st.markdown(f"**{'Lý do' if lang == 'vi' else 'Reason'}:** {issue.get('content')}")
                        col_app, col_chk = st.columns(2)
                        if col_app.button(DASHBOARD_LABELS[lang]["btn_approve"], key=f"res_{issue['id']}", type="primary", use_container_width=True):
                            if approve_deposit_issue(issue['id']): 
                                st.success(DASHBOARD_LABELS[lang]["msg_success"])
                                st.rerun()
                        if col_chk.button(DASHBOARD_LABELS[lang]["btn_check"], key=f"check_{issue['id']}", use_container_width=True): 
                            st.warning(DASHBOARD_LABELS[lang]["msg_saved"])

    with st.container(border=True):
        st.markdown(f"**{DASHBOARD_LABELS[lang]['sub_parent_leave']}**")
        st.info(DASHBOARD_LABELS[lang]["info_leave_sync"])