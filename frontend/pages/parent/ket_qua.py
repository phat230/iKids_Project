import streamlit as st
import pandas as pd
import numpy as np
import requests
import os
from datetime import datetime

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

# ================= TỪ ĐIỂN SONG NGỮ (KHÔNG ICON) =================
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
        "comment_lbl_teacher": "Giáo viên",
        "comment_lbl_date": "Ngày",
        "comment_lbl_content": "Nhận xét:",
        "sub_english": "Tiếng Anh Giao Tiếp",
        "teacher_john": "Thầy John",
        "comment_john": "rất tích cực phát biểu trên lớp. Khả năng phát âm tiếng Anh ngày càng tự tin và tiến bộ rõ rệt.",
        "sub_math": "Toán Tư Duy",
        "teacher_lan": "Cô Lan",
        "comment_lan": "nắm vững các quy tắc logic rất tốt, tập trung nghe giảng và làm bài tập về nhà đầy đủ.",
        "exam_title": "Bảng Điểm Tổng Kết Các Môn Học",
        "exam_desc": "Kết quả học tập dựa trên điểm chuyên cần, kiểm tra, giữa kỳ và cuối kỳ.",
        "col_subject": "Môn Học", "col_total": "Tổng Kết", "col_rank": "Xếp Loại"
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
        "comment_lbl_teacher": "Instructor",
        "comment_lbl_date": "Date",
        "comment_lbl_content": "Feedback Notes:",
        "sub_english": "Communicative English",
        "teacher_john": "Mr. John",
        "comment_john": "participates very actively in class discussions. English pronunciation is becoming noticeably more confident and progressive.",
        "sub_math": "Critical Thinking Math",
        "teacher_lan": "Ms. Lan",
        "comment_lan": "demonstrates a solid grasp of logical reasoning rules, stays highly focused, and finishes all homework diligently.",
        "exam_title": "Final Grade Report",
        "exam_desc": "Academic results based on attendance, tests, midterm, and final exams.",
        "col_subject": "Subject", "col_total": "Final Grade", "col_rank": "Classification"
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
    # 1. Cố gắng gọi API lấy dữ liệu thực tế từ Database
    try:
        res = requests.get(f"{API_URL}/api/tv2/attendance/{child_id}", headers=headers, timeout=3)
        if res.status_code == 200:
            data = res.json()
            if data and isinstance(data, list):
                return pd.DataFrame(data)
    except:
        pass
    
    # 2. Giả lập dữ liệu liên kết chuẩn xác với những gì Giáo viên đã nhập để Demo
    current_date = datetime.now().strftime("%d/%m/%Y")
    return pd.DataFrame([
        {"Ngày": current_date, "Môn Học": "Toán Tư Duy", "Trạng Thái": "Có mặt", "Nhận Xét": "xxx"},
        {"Ngày": "20/05/2026", "Môn Học": "Tiếng Anh Giao Tiếp", "Trạng Thái": "Có mặt", "Nhận Xét": f"Bé {child_name} hăng hái phát biểu, làm bài tốt."},
        {"Ngày": "18/05/2026", "Môn Học": "Toán Tư Duy", "Trạng Thái": "Đi trễ", "Nhận Xét": "Vào lớp trễ 10 phút."}
    ])

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
    # BẢNG LỊCH SỬ ĐIỂM DANH LIÊN KẾT TỪ GIÁO VIÊN
    st.subheader(REPORT_LABELS[lang]["journal_title"])
    child_name = child_options[selected_child_id]
    
    journal_df = get_attendance_history(selected_child_id, child_name)
    
    if lang == "en":
        journal_df.rename(columns={
            "Ngày": "Date", "Môn Học": "Subject", 
            "Trạng Thái": "Status", "Nhận Xét": "Teacher's Remark"
        }, inplace=True)
        status_map = {"Có mặt": "Present", "Vắng mặt": "Absent", "Đi trễ": "Late"}
        journal_df["Status"] = journal_df["Status"].map(lambda x: status_map.get(x, x))
        
    st.dataframe(journal_df, use_container_width=True, hide_index=True)
    
    st.write("---")
    # NHẬN XÉT ĐỊNH KỲ
    st.subheader(REPORT_LABELS[lang]["comment_title"])

    comment_english_text = f"Student {child_name} {REPORT_LABELS[lang]['comment_john']}" if lang == "en" else f"Bé {child_name} {REPORT_LABELS[lang]['comment_john']}"
    comment_math_text = f"Student {child_name} {REPORT_LABELS[lang]['comment_lan']}" if lang == "en" else f"Bé {child_name} {REPORT_LABELS[lang]['comment_lan']}"

    comments = [
        {"subject": REPORT_LABELS[lang]["sub_english"], "teacher": REPORT_LABELS[lang]["teacher_john"], "date": "20/05/2026", "content": comment_english_text},
        {"subject": REPORT_LABELS[lang]["sub_math"], "teacher": REPORT_LABELS[lang]["teacher_lan"], "date": "18/05/2026", "content": comment_math_text}
    ]

    for comment in comments:
        with st.container(border=True):
            st.markdown(f"### {comment['subject']}")
            st.caption(f"{REPORT_LABELS[lang]['comment_lbl_teacher']}: {comment['teacher']} | {REPORT_LABELS[lang]['comment_lbl_date']}: {comment['date']}")
            st.markdown(f"**{REPORT_LABELS[lang]['comment_lbl_content']}**")
            st.markdown(f"> {comment['content']}")

else:
    # ---------------- VIEW 2: BẢNG KẾT QUẢ THI ĐỊNH KỲ ----------------
    st.subheader(REPORT_LABELS[lang]["exam_title"])
    st.write(REPORT_LABELS[lang]["exam_desc"])
    
    exam_data = [
        {"Môn Học": "Toán Tư Duy", "Chuyên Cần": 10.0, "TB Kiểm Tra": 8.5, "Giữa Kỳ": 9.0, "Cuối Kỳ": 9.0, "Tổng Kết": 8.95, "Xếp Loại": "Giỏi"},
        {"Môn Học": "Tiếng Anh Giao Tiếp", "Chuyên Cần": 9.0, "TB Kiểm Tra": 7.5, "Giữa Kỳ": 8.0, "Cuối Kỳ": 8.5, "Tổng Kết": 8.15, "Xếp Loại": "Khá"},
        {"Môn Học": "Lập Trình Scratch", "Chuyên Cần": 8.5, "TB Kiểm Tra": 6.5, "Giữa Kỳ": 7.0, "Cuối Kỳ": 7.5, "Tổng Kết": 7.30, "Xếp Loại": "Khá"}
    ]
    exam_df = pd.DataFrame(exam_data)
    
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