import streamlit as st
import pandas as pd
import numpy as np
import requests
import os

# ================= CRITICAL: CẤU HÌNH TRANG LUÔN ĐỂ ĐẦU FILE =================
st.set_page_config(page_title="Báo Cáo Học Tập", layout="wide", page_icon=None)

API_URL = "http://localhost:8000"
API_TV3 = "http://localhost:8000/api/tv3"

def load_css(file_name):
    current_dir = os.path.dirname(os.path.abspath(__file__))
    css_root = os.path.abspath(os.path.join(current_dir, "../../CSS"))
    full_path = os.path.join(css_root, file_name)
    if os.path.exists(full_path):
        with open(full_path, "r", encoding="utf-8") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

load_css("parent/parent_global.css")
lang = st.session_state.get("lang", "vi")

# ================= STATE & VIEW TOGGLE =================
if "report_view" not in st.session_state:
    st.session_state.report_view = "progress"

def toggle_view():
    st.session_state.report_view = "exam" if st.session_state.report_view == "progress" else "progress"

# ================= TỪ ĐIỂN SONG NGỮ =================
REPORT_LABELS = {
    "vi": {
        "err_login": "Vui lòng đăng nhập để xem báo cáo.",
        "title": "Báo Cáo Chuyên Sâu Hành Trình Lớn Khôn",
        "btn_view_exam": "Xem Kết Quả Học Tập",
        "btn_view_progress": "Quay Lại Tiến Độ",
        "select_child": "Chọn con để xem báo cáo:",
        "lbl_viewing": "Đang hiển thị dữ liệu của bé:",
        "stat_attendance": "Tỷ lệ chuyên cần",
        "stat_quiz": "Điểm trung bình Quiz",
        "stat_videos": "Video đã học",
        "stat_rank": "Hạng hiện tại",
        "chart_title": "Biểu đồ điểm số các bài tập Quiz gần đây",
        "journal_title": "Lịch Sử Điểm Danh & Nhận Xét Từ Giáo Viên",
        "comment_title": "Nhận xét định kỳ từ Giáo viên",
        "exam_title": "Bảng Điểm Tổng Kết Các Môn Học",
        "exam_desc": "Kết quả học tập dựa trên điểm chuyên cần, kiểm tra, giữa kỳ và cuối kỳ.",
        "col_subject": "Môn Học", "col_total": "Tổng Kết", "col_rank": "Xếp Loại",
        "no_grades": "Bé chưa có điểm tổng kết nào được ghi nhận."
    },
    "en": {
        "err_login": "Authentication required.",
        "title": "Growth Journey & Learning Analytics",
        "btn_view_exam": "View Academic Results",
        "btn_view_progress": "Back to Progress",
        "select_child": "Select child to view report:",
        "lbl_viewing": "Displaying data for:",
        "stat_attendance": "Attendance Rate",
        "stat_quiz": "Avg Quiz Score",
        "stat_videos": "Videos Completed",
        "stat_rank": "Current Rank",
        "chart_title": "Recent Quiz Score Trend",
        "journal_title": "Attendance History & Teacher's Remarks",
        "comment_title": "Academic Progress Comments from Instructors",
        "exam_title": "Final Grade Report",
        "exam_desc": "Academic results based on attendance, tests, midterm, and final exams.",
        "col_subject": "Subject", "col_total": "Final Grade", "col_rank": "Classification",
        "no_grades": "No grades recorded for this student yet."
    }
}

# 1. KIỂM TRA ĐĂNG NHẬP
parent_id = st.session_state.get("user_id")
token = st.session_state.get("access_token") or st.session_state.get("token")
if not parent_id or not token:
    st.error(REPORT_LABELS[lang]["err_login"])
    st.stop()

headers = {"Authorization": f"Bearer {token}", "parent-id": str(parent_id)}

# 2. LẤY DỮ LIỆU CƠ BẢN
@st.cache_data(ttl=30)
def get_my_children():
    try:
        res = requests.get(f"{API_TV3}/parent/my-children", headers=headers)
        return res.json() if res.status_code == 200 else []
    except: return []

children = get_my_children()
child_options = {c["id"]: c["name"] for c in children} if children else {}

# HÀM LẤY LỊCH SỬ ĐIỂM DANH TỪ API
def get_attendance_history(child_id, child_name):
    try:
        res = requests.get(f"{API_URL}/api/tv2/attendance/{child_id}", headers=headers, timeout=3)
        if res.status_code == 200:
            data = res.json()
            if data and isinstance(data, list):
                return pd.DataFrame(data)
    except: pass
    return pd.DataFrame()

# HÀM LẤY ĐIỂM THỰC TẾ TỪ DB
def get_student_grades_from_db(child_id):
    try:
        res = requests.get(f"{API_URL}/api/tv2/grades/{child_id}", headers=headers, timeout=5)
        if res.status_code == 200:
            return res.json()
    except: pass
    return []

# ================= GIAO DIỆN CHÍNH =================
if not child_options:
    st.title(REPORT_LABELS[lang]["title"])
    st.warning("Bạn chưa có hồ sơ học sinh nào. Vui lòng tạo tài khoản cho bé trước.")
    st.stop()

col_title, col_btn = st.columns([8, 2])
with col_title:
    st.title(REPORT_LABELS[lang]["title"])
with col_btn:
    st.write("") 
    btn_label = REPORT_LABELS[lang]["btn_view_exam"] if st.session_state.report_view == "progress" else REPORT_LABELS[lang]["btn_view_progress"]
    if st.button(btn_label, type="primary", use_container_width=True):
        toggle_view()
        st.rerun()

selected_child_id = st.selectbox(REPORT_LABELS[lang]["select_child"], options=list(child_options.keys()), format_func=lambda x: child_options[x])
st.write(f"{REPORT_LABELS[lang]['lbl_viewing']} **{child_options[selected_child_id]}**")
st.divider()

# ================= XỬ LÝ VIEW =================
if st.session_state.report_view == "progress":
    # ---------------- VIEW 1: TIẾN ĐỘ HỌC TẬP ----------------
    c1, c2, c3, c4 = st.columns(4)
    c1.metric(REPORT_LABELS[lang]["stat_attendance"], "92%")
    c2.metric(REPORT_LABELS[lang]["stat_quiz"], "7.5/10")
    c3.metric(REPORT_LABELS[lang]["stat_videos"], "8")
    c4.metric(REPORT_LABELS[lang]["stat_rank"], "Beginner")
    
    st.write("---")
    st.subheader(REPORT_LABELS[lang]["chart_title"])
    st.line_chart(pd.DataFrame(np.array([6, 9, 8, 7, 9]), columns=["Score"]))
    
    st.write("---")
    st.subheader(REPORT_LABELS[lang]["journal_title"])
    child_name = child_options[selected_child_id]
    
    journal_df = get_attendance_history(selected_child_id, child_name)
    
    if not journal_df.empty:
        if lang == "en":
            journal_df.rename(columns={
                "Ngày": "Date", "Môn Học": "Subject", 
                "Trạng Thái": "Status", "Nhận Xét": "Teacher's Remark"
            }, inplace=True)
            status_map = {"Có mặt": "Present", "Vắng mặt": "Absent", "Đi trễ": "Late"}
            journal_df["Status"] = journal_df["Status"].map(lambda x: status_map.get(x, x))
            
        st.dataframe(journal_df, use_container_width=True, hide_index=True)
    else:
        st.info("Chưa có lịch sử điểm danh.")

else:
    # ---------------- VIEW 2: BẢNG KẾT QUẢ THI ĐỊNH KỲ (DỮ LIỆU THẬT) ----------------
    st.subheader(REPORT_LABELS[lang]["exam_title"])
    st.write(REPORT_LABELS[lang]["exam_desc"])
    
    real_grades = get_student_grades_from_db(selected_child_id)
    
    if not real_grades:
        st.info(REPORT_LABELS[lang]["no_grades"])
    else:
        formatted_grades = []
        for g in real_grades:
            formatted_grades.append({
                "Môn Học": g.get("subject", ""),
                "Chuyên Cần": g.get("chuyen_can", 0),
                "TB Kiểm Tra": g.get("tb_kiem_tra", 0),
                "Giữa Kỳ": g.get("giua_ky", 0),
                "Cuối Kỳ": g.get("cuoi_ky", 0),
                "Tổng Kết": g.get("tong_ket", 0),
                "Xếp Loại": g.get("xep_loai", "")
            })
            
        exam_df = pd.DataFrame(formatted_grades)
        
        if lang == "en":
            exam_df.rename(columns={
                "Môn Học": REPORT_LABELS[lang]["col_subject"],
                "Chuyên Cần": REPORT_LABELS[lang]["col_attend"],
                "TB Kiểm Tra": REPORT_LABELS[lang]["col_test"],
                "Giữa Kỳ": REPORT_LABELS[lang]["col_mid"],
                "Cuối Kỳ": REPORT_LABELS[lang]["col_final"],
                "Tổng Kết": REPORT_LABELS[lang]["col_total"],
                "Xếp Loại": REPORT_LABELS[lang]["col_rank"]
            }, inplace=True)
            
            rank_map = {"Giỏi": "Excellent", "Khá": "Good", "TB": "Average", "Yếu": "Poor"}
            exam_df[REPORT_LABELS[lang]["col_rank"]] = exam_df[REPORT_LABELS[lang]["col_rank"]].map(lambda x: rank_map.get(x, x))
            
        st.dataframe(exam_df, use_container_width=True, hide_index=True)