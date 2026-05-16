import streamlit as st
import requests
import pandas as pd
import os

st.set_page_config(page_title="Admin Dashboard - iKids", layout="wide", initial_sidebar_state="expanded", page_icon="🛡️")

# ================= HÀM ĐỌC FILE CSS (SỬA LỖI ĐƯỜNG DẪN TUYỆT ĐỐI) =================
def load_css(file_name):
    """
    Tự động tìm file CSS trong thư mục frontend/CSS/
    file_name: tên file kèm thư mục con, ví dụ 'admin/dashboard.css'
    """
    # Lấy đường dẫn tuyệt đối của thư mục hiện tại (frontend/pages/admin)
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Tìm đường dẫn đến thư mục CSS (lùi 2 cấp rồi vào CSS/)
    css_root = os.path.abspath(os.path.join(current_dir, "../../CSS"))
    full_path = os.path.join(css_root, file_name)

    if os.path.exists(full_path):
        with open(full_path, "r", encoding="utf-8") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    else:
        st.warning(f"⚠️ Không tìm thấy file CSS tại: {full_path}")

# Tải CSS làm đẹp (Chỉ truyền phần sau thư mục CSS/)
load_css("admin/dashboard.css")

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
st.title(" Bảng Điều Khiển Quản Trị Trung Tâm")
st.markdown("*Hệ thống giám sát vận hành đồng bộ: Lịch dạy (TV1), Học thuật & AI (TV2), Cộng đồng (TV3)*")
st.write("---")

# --- 1. CHỈ SỐ TỔNG QUAN ---
pending_requests = fetch_pending_requests()
total_pending_tv1 = len(pending_requests)
deposit_issues = fetch_deposit_issues()
total_pending_tv3 = len(deposit_issues)

col1, col2, col3, col4 = st.columns(4)
with col1:
    st.markdown(f"""<div class="metric-card tv1-border">
        <p class="metric-label">ĐƠN GV CHỜ DUYỆT (TV1)</p>
        <h2 class="metric-value">{total_pending_tv1}</h2>
        <p class="metric-caption caption-red">Dữ liệu trực tiếp từ MongoDB</p></div>""", unsafe_allow_html=True)
with col2:
    st.markdown("""<div class="metric-card tv1-border">
        <p class="metric-label">CA DẠY HÔM NAY (TV1)</p>
        <h2 class="metric-value">--</h2>
        <p class="metric-caption caption-green">Đang cập nhật luồng API</p></div>""", unsafe_allow_html=True)
with col3:
    st.markdown("""<div class="metric-card tv2-border">
        <p class="metric-label">NHẬT KÝ ĐÃ NỘP (TV2)</p>
        <h2 class="metric-value">--</h2>
        <p class="metric-caption caption-orange">Đang cập nhật luồng API</p></div>""", unsafe_allow_html=True)
with col4:
    st.markdown(f"""<div class="metric-card tv3-border">
        <p class="metric-label">SỰ CỐ NẠP TIỀN (TV3)</p>
        <h2 class="metric-value">{total_pending_tv3}</h2>
        <p class="metric-caption caption-blue">Dữ liệu từ deposit_issues</p></div>""", unsafe_allow_html=True)

st.write("<br>", unsafe_allow_html=True)

# --- LAYOUT CHÍNH: CHIA 2 CỘT ---
left_col, right_col = st.columns([1.6, 1])

# --- CỘT TRÁI: TV1 ---
with left_col:
    st.subheader("1. Phê duyệt & Điều phối ")
    st.markdown(f"**A. Yêu cầu đang chờ duyệt ({total_pending_tv1})**")
    if not pending_requests:
        st.success("✨ Không có đơn hỗ trợ nào cần xử lý.")
    else:
        tv1_container = st.container(height=400) if len(pending_requests) > 3 else st.container()
        with tv1_container:
            for req in pending_requests:
                with st.container(border=True):
                    c_info, c_btn = st.columns([3, 1])
                    with c_info:
                        icon = "🤒" if "nghỉ" in req.get('type', '').lower() else ""
                        st.markdown(f"{icon} {req.get('type', '')} - GV: {req.get('teacher_name', '')}")
                        st.caption(f"**Lớp:** {req.get('class_name', '')} | **Ngày:** {req.get('date', '')}")
                        st.markdown(f"**Lý do:** {req.get('reason', '')}")
                    with c_btn:
                        if st.button("✅ Duyệt", key=f"app_{req['id']}", type="primary", use_container_width=True):
                            res = requests.post(f"{API_URL}/approve/{req['id']}")
                            if res.status_code == 200: st.rerun()
                        if st.button("❌ Từ chối", key=f"rej_{req['id']}", use_container_width=True):
                            res = requests.post(f"{API_URL}/reject/{req['id']}")
                            if res.status_code == 200: st.rerun()

    st.write("---")
    st.markdown("**B. Lịch sử xét duyệt gần đây**")
    history_requests = fetch_history_requests()
    if history_requests:
        history_data = []
        for h in history_requests:
            status_text = "✅ Đã duyệt" if h.get('status') == "approved" else "❌ Từ chối"
            raw_time = h.get("updated_at")
            time_str = pd.to_datetime(raw_time).strftime("%d/%m/%Y %H:%M") if raw_time else "Chưa rõ"
            history_data.append({
                "Giáo viên": h.get("teacher_name", ""),
                "Loại đơn": h.get("type", ""),
                "Lớp học": h.get("class_name", ""),
                "Thời gian xử lý": time_str,
                "Trạng thái": status_text
            })
        st.dataframe(pd.DataFrame(history_data), use_container_width=True, hide_index=True)

# --- CỘT PHẢI: TV2 & TV3 ---
with right_col:
    st.subheader(" 2. Học thuật & Tương tác")
    with st.container(border=True):
        st.markdown("A. Quản Lý Nội Dung Học Thuật ")
        if st.session_state.admin_tv2_view == "list":
            try: quizzes = requests.get(f"{API_URL}/api/tv2/quizzes").json()
            except: quizzes = []
            try: videos = requests.get(f"{API_URL}/api/tv2/videos").json()
            except: videos = []
            tab_quiz, tab_video = st.tabs([" Kho Bài Tập", " Kho Video"])
            with tab_quiz:
                if not quizzes: st.info("Chưa có bộ đề nào.")
                else:
                    quiz_container = st.container(height=350) if len(quizzes) > 3 else st.container()
                    with quiz_container:
                        for q in quizzes:
                            with st.container(border=True):
                                col_q1, col_q2 = st.columns([4, 1])
                                author = q.get("author", q.get("author_email", "Hệ thống"))
                                col_q1.markdown(f"**{q.get('title', 'N/A')}**")
                                col_q1.caption(f"Tác giả: {author} | Số câu hỏi: {len(q.get('questions', []))} câu")
                                if col_q2.button("Xem ", key=f"ad_view_q_{q.get('id')}", use_container_width=True):
                                    st.session_state.admin_tv2_item, st.session_state.admin_tv2_type, st.session_state.admin_tv2_view = q, "quiz", "detail"
                                    st.rerun()
            with tab_video:
                if not videos: st.info("Chưa có video nào.")
                else:
                    vid_container = st.container(height=350) if len(videos) > 3 else st.container()
                    with vid_container:
                        for v in videos:
                            with st.container(border=True):
                                col_v1, col_v2 = st.columns([4, 1])
                                col_v1.markdown(f"{v.get('title', 'N/A')}")
                                col_v1.caption(f"Chủ đề: {v.get('topic')} | ❤️ {v.get('likes', 0)}")
                                if col_v2.button("Xem", key=f"ad_view_v_{v.get('id')}", use_container_width=True):
                                    st.session_state.admin_tv2_item, st.session_state.admin_tv2_type, st.session_state.admin_tv2_view = v, "video", "detail"
                                    st.rerun()
        else:
            if st.button("Quay Lại", type="primary"):
                st.session_state.admin_tv2_view, st.session_state.admin_tv2_item = "list", None
                st.rerun()
            item = st.session_state.admin_tv2_item
            if st.session_state.admin_tv2_type == "quiz":
                st.subheader(f" {item.get('title')}")
                with st.container(height=300):
                    for idx, q_item in enumerate(item.get("questions", [])):
                        st.markdown(f"**Câu {idx + 1}: {q_item.get('question')}**")
                        st.success(f" Đáp án: {q_item.get('correct_answer')}")
            elif st.session_state.admin_tv2_type == "video":
                st.subheader(f" {item.get('title')}")
                st.video(item.get('url'))

    with st.container(border=True):
        st.markdown("**B. Trung tâm Tương tác Phụ huynh (TV3)**")
        if not deposit_issues: st.success("✅ Không có sự cố nạp tiền.")
        else:
            tv3_container = st.container(height=350) if len(deposit_issues) > 2 else st.container()
            with tv3_container:
                for issue in deposit_issues:
                    with st.container(border=True):
                        st.markdown(f"###  {issue.get('amount', 0):,.0f} VNĐ")
                        st.markdown(f"**Lý do:** {issue.get('content')}")
                        col_app, col_chk = st.columns(2)
                        if col_app.button("✅ Duyệt", key=f"res_{issue['id']}", type="primary", use_container_width=True):
                            if approve_deposit_issue(issue['id']): st.success("Xong!"); st.rerun()
                        if col_chk.button("⚠️ Check", key=f"check_{issue['id']}", use_container_width=True): st.warning("Đã lưu.")

    with st.container(border=True):
        st.markdown("**C. Yêu cầu xin nghỉ từ Phụ huynh**")
        st.info(" Yêu cầu xin nghỉ học sẽ được tự động đồng bộ sang bộ phận Vận hành (TV1).")