import streamlit as st
import requests
import pandas as pd

st.set_page_config(page_title="Admin Dashboard - iKids", layout="wide", initial_sidebar_state="expanded")

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
    """Lấy đơn từ Giáo viên (TV1)"""
    try:
        res = requests.get(f"{API_URL}/pending-requests")
        return res.json() if res.status_code == 200 else []
    except: return []

def fetch_history_requests():
    """Lấy lịch sử đơn Giáo viên (TV1)"""
    try:
        res = requests.get(f"{API_URL}/request-history")
        return res.json() if res.status_code == 200 else []
    except: return []

def fetch_deposit_issues():
    """Lấy danh sách sự cố nạp tiền thực tế từ TV3 (Chỉ lấy status=pending)"""
    try:
        res = requests.get(f"{API_TV3}/admin/deposit-issues")
        return res.json() if res.status_code == 200 else []
    except: return []

def approve_deposit_issue(issue_id):
    """Gửi lệnh duyệt: Cộng tiền vào ví và đổi status thành resolved"""
    try:
        res = requests.post(f"{API_TV3}/admin/resolve-deposit/{issue_id}")
        return res.status_code == 200
    except: return False

# --- CSS CUSTOM ---
st.markdown("""
<style>
    .metric-card {
        background-color: #ffffff; border-radius: 10px; padding: 20px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05); border-left: 5px solid;
    }
    .tv1-border { border-color: #3b82f6; }
    .tv2-border { border-color: #10b981; }
    .tv3-border { border-color: #8b5cf6; }
</style>
""", unsafe_allow_html=True)

# --- HEADER ---
st.title("🛡️ Bảng Điều Khiển Quản Trị Trung Tâm")
st.markdown("*Hệ thống giám sát vận hành đồng bộ: Lịch dạy (TV1), Học thuật & AI (TV2), Cộng đồng (TV3)*")
st.write("---")

# --- 1. CHỈ SỐ TỔNG QUAN ---
pending_requests = fetch_pending_requests()
total_pending_tv1 = len(pending_requests)

# Lấy dữ liệu sự cố nạp tiền thực tế
deposit_issues = fetch_deposit_issues()
total_pending_tv3 = len(deposit_issues)

col1, col2, col3, col4 = st.columns(4)
with col1:
    st.markdown(f"""<div class="metric-card tv1-border">
        <p style="color:#64748b; margin:0; font-size:14px; font-weight:bold;">ĐƠN GV CHỜ DUYỆT (TV1)</p>
        <h2 style="color:#0f172a; margin:0; font-size:32px;">{total_pending_tv1}</h2>
        <p style="color:#ef4444; margin:0; font-size:12px;">Dữ liệu trực tiếp từ MongoDB</p></div>""", unsafe_allow_html=True)
with col2:
    st.markdown("""<div class="metric-card tv1-border">
        <p style="color:#64748b; margin:0; font-size:14px; font-weight:bold;">CA DẠY HÔM NAY (TV1)</p>
        <h2 style="color:#0f172a; margin:0; font-size:32px;">--</h2>
        <p style="color:#10b981; margin:0; font-size:12px;">Đang cập nhật luồng API</p></div>""", unsafe_allow_html=True)
with col3:
    st.markdown("""<div class="metric-card tv2-border">
        <p style="color:#64748b; margin:0; font-size:14px; font-weight:bold;">NHẬT KÝ ĐÃ NỘP (TV2)</p>
        <h2 style="color:#0f172a; margin:0; font-size:32px;">--</h2>
        <p style="color:#f59e0b; margin:0; font-size:12px;">Đang cập nhật luồng API</p></div>""", unsafe_allow_html=True)
with col4:
    st.markdown(f"""<div class="metric-card tv3-border">
        <p style="color:#64748b; margin:0; font-size:14px; font-weight:bold;">SỰ CỐ NẠP TIỀN (TV3)</p>
        <h2 style="color:#0f172a; margin:0; font-size:32px;">{total_pending_tv3}</h2>
        <p style="color:#3b82f6; margin:0; font-size:12px;">Dữ liệu từ deposit_issues</p></div>""", unsafe_allow_html=True)

st.write("<br>", unsafe_allow_html=True)

# --- LAYOUT CHÍNH: CHIA 2 CỘT ---
left_col, right_col = st.columns([1.6, 1])

# =========================================================
# CỘT TRÁI: TV1 (VẬN HÀNH & NHÂN SỰ)
# =========================================================
with left_col:
    st.subheader("📑 1. Phê duyệt & Điều phối (Thành viên 1)")
    
    st.markdown(f"**A. Yêu cầu đang chờ duyệt ({total_pending_tv1})**")
    if not pending_requests:
        st.success("✨ Tuyệt vời! Hiện tại không có đơn hỗ trợ nào cần xử lý.")
    else:
        # LOGIC CONTAINER ĐỘNG: Ít đơn thì tự co lại, nhiều đơn mới bật Scrollbar (cao 400px)
        tv1_container = st.container(height=400) if len(pending_requests) > 3 else st.container()
        
        with tv1_container:
            for req in pending_requests:
                with st.container(border=True):
                    c_info, c_btn = st.columns([3, 1])
                    with c_info:
                        icon = "🔴" if "nghỉ" in req.get('type', '').lower() else "🔄"
                        st.markdown(f"<h6 style='margin-bottom: 5px;'>{icon} {req.get('type', '')} - GV: {req.get('teacher_name', '')}</h6>", unsafe_allow_html=True)
                        st.caption(f"**Lớp:** {req.get('class_name', '')} | **Ngày:** {req.get('date', '')}")
                        st.markdown(f"**Lý do:** {req.get('reason', '')}")
                    with c_btn:
                        if st.button("✅ Phê duyệt", key=f"app_{req['id']}", type="primary", use_container_width=True):
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


# =========================================================
# CỘT PHẢI: TV2 & TV3 (CHUYÊN MÔN & CỘNG ĐỒNG)
# =========================================================
with right_col:
    st.subheader("📊 2. Học thuật & Tương tác")
    
    with st.container(border=True):
        st.markdown("**A. Báo cáo Video AI & Kho Đề (TV2)**")
        
        # ---------------- VIEW 1: DANH SÁCH (LIST VIEW) ----------------
        if st.session_state.admin_tv2_view == "list":
            try:
                quizzes = requests.get(f"{API_URL}/api/tv2/quizzes").json()
            except:
                quizzes = []
                
            try:
                videos = requests.get(f"{API_URL}/api/tv2/videos").json()
            except:
                videos = []

            tab_quiz, tab_video = st.tabs(["📝 Bộ Đề", "🎬 Video AI"])
            
            with tab_quiz:
                if not quizzes:
                    st.info("Chưa có bộ đề nào được tạo trên hệ thống.")
                else:
                    # LOGIC CONTAINER ĐỘNG
                    quiz_container = st.container(height=350) if len(quizzes) > 3 else st.container()
                    
                    with quiz_container:
                        for q in quizzes:
                            with st.container(border=True):
                                col_q1, col_q2 = st.columns([4, 1])
                                author = q.get("author", q.get("author_email", "Hệ thống"))
                                col_q1.markdown(f"**{q.get('title', 'Chưa có tên')}**")
                                col_q1.caption(f"👤 Tác giả: {author} | 🔢 Số câu: {len(q.get('questions', []))} | 📅 {q.get('created_at', '')[:10]}")
                                
                                if col_q2.button("👁️ Xem", key=f"ad_view_q_{q.get('id')}", use_container_width=True):
                                    st.session_state.admin_tv2_item = q
                                    st.session_state.admin_tv2_type = "quiz"
                                    st.session_state.admin_tv2_view = "detail"
                                    st.rerun()

            with tab_video:
                if not videos:
                    st.info("Chưa có video nào trên hệ thống.")
                else:
                    # LOGIC CONTAINER ĐỘNG
                    vid_container = st.container(height=350) if len(videos) > 3 else st.container()
                    
                    with vid_container:
                        for v in videos:
                            with st.container(border=True):
                                col_v1, col_v2 = st.columns([4, 1])
                                col_v1.markdown(f"**{v.get('title', 'Chưa có tên')}**")
                                col_v1.caption(f"📚 Chủ đề: {v.get('topic')} | 🎓 Trình độ: {v.get('level')} | ❤️ {v.get('likes', 0)} Likes")
                                
                                if col_v2.button("👁️ Xem", key=f"ad_view_v_{v.get('id')}", use_container_width=True):
                                    st.session_state.admin_tv2_item = v
                                    st.session_state.admin_tv2_type = "video"
                                    st.session_state.admin_tv2_view = "detail"
                                    st.rerun()

        # ---------------- VIEW 2: CHI TIẾT (DETAIL VIEW) ----------------
        else:
            if st.button("🔙 Quay lại danh sách", type="primary", key="btn_back_tv2"):
                st.session_state.admin_tv2_view = "list"
                st.session_state.admin_tv2_item = None
                st.rerun()
                
            item = st.session_state.admin_tv2_item
            
            if st.session_state.admin_tv2_type == "quiz":
                author = item.get("author", item.get("author_email", "Hệ thống"))
                st.subheader(f"📖 {item.get('title')}")
                st.caption(f"👤 Người ra đề: **{author}** | 📅 Tạo ngày: {item.get('created_at', 'N/A')[:10]}")
                st.divider()
                
                # CÓ THỂ CUỘN BÊN TRONG CHI TIẾT ĐỀ
                with st.container(height=300):
                    for idx, q_item in enumerate(item.get("questions", [])):
                        st.markdown(f"**Câu {idx + 1}: {q_item.get('question')}**")
                        for opt in q_item.get('options', []):
                            if opt.startswith(q_item.get('correct_answer', '')):
                                st.success(f"✅ {opt}")
                            else:
                                st.write(opt)
                        st.write("---")
                    
            elif st.session_state.admin_tv2_type == "video":
                st.subheader(f"🎬 {item.get('title')}")
                st.caption(f"📚 Chủ đề: {item.get('topic')} | 🎓 Trình độ: {item.get('level')}")
                
                try:
                    st.video(item.get('url'))
                except:
                    st.error("Link video không hợp lệ hoặc đã bị lỗi.")
                    
                st.divider()
                st.write("**💬 Đánh giá & Bình luận chuyên môn từ Giáo viên:**")
                if not item.get('comments'):
                    st.caption("Chưa có bình luận nào.")
                else:
                    # LOGIC CONTAINER ĐỘNG CHO BÌNH LUẬN
                    cmt_container = st.container(height=150) if len(item.get('comments', [])) > 4 else st.container()
                    with cmt_container:
                        for cmt in item.get('comments', []):
                            st.caption(f"👉 {cmt}")
        
    with st.container(border=True):
        st.markdown("**B. Trung tâm Tương tác Phụ huynh (TV3)**")
        st.caption("Duyệt sự cố nạp tiền và tự động cộng tiền vào ví.")
        
        if not deposit_issues:
            st.success("🎉 Hiện tại không có sự cố nạp tiền nào cần xử lý.")
        else:
            # LOGIC CONTAINER ĐỘNG
            tv3_container = st.container(height=350) if len(deposit_issues) > 2 else st.container()
            
            with tv3_container:
                for issue in deposit_issues:
                    with st.container(border=True):
                        amount = issue.get('amount', 0)
                        st.markdown(f"### 💰 {amount:,.0f} VNĐ")
                        st.markdown(f"**Lý do:** {issue.get('content')}")
                        st.caption(f"Người gửi: {issue.get('sender_id')} | Gửi lúc: {issue.get('created_at')}")
                        
                        col_app, col_chk = st.columns(2)
                        if col_app.button("✅ Duyệt & Cộng tiền", key=f"res_{issue['id']}", type="primary", use_container_width=True):
                            with st.spinner("Đang thực thi..."):
                                if approve_deposit_issue(issue['id']):
                                    st.success("Đã cộng tiền thành công!")
                                    st.rerun()
                                    
                        if col_chk.button("⚠️ Cần kiểm tra", key=f"check_{issue['id']}", use_container_width=True):
                            st.warning("Đã ghi chú cần kiểm tra lại.")

    with st.container(border=True):
        st.markdown("**C. Yêu cầu xin nghỉ từ Phụ huynh**")
        st.info("🕒 Yêu cầu xin nghỉ học sẽ được tự động đồng bộ sang bộ phận Vận hành (TV1).")