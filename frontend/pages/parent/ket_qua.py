import streamlit as st
import pandas as pd
import numpy as np
import requests
import os
import altair as alt
import urllib.parse

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

# ================= TỪ ĐIỂN SONG NGỮ MỞ RỘNG =================
REPORT_LABELS = {
    "vi": {
        "err_login": "Vui lòng đăng nhập để xem báo cáo.",
        "title": "Báo Cáo Chuyên Sâu Hành Trình Lớn Khôn",
        "btn_view_exam": "Xem Bảng Điểm Chi Tiết",
        "btn_view_progress": "Quay Lại Phân Tích",
        "select_child": "Chọn con để xem báo cáo:",
        "lbl_viewing": "Đang hiển thị dữ liệu của bé:",
        "stat_attendance": "Tỷ lệ chuyên cần",
        "stat_quiz": "TB Kiểm Tra",
        "stat_quiz_progress": "Bài tập hoàn thành",
        "stat_rank": "Hạng hiện tại",
        "chart_title": "📊 Sơ Đồ Phân Tích Điểm Tổng Kết Các Môn Học",
        "quiz_chart_title": "🎯 Tỷ Lệ Hoàn Thành Bài Tập Về Nhà",
        "line_chart_title": "📈 Sơ Đồ Tiến Trình Điểm Số Từng Môn",
        "select_subject": "🔍 Chọn môn học để xem tiến trình:",
        "journal_title": "Lịch Sử Điểm Danh & Nhận Xét Từ Giáo Viên",
        "exam_title": "Bảng Điểm Tổng Kết Các Môn Học",
        "exam_desc": "Kết quả học tập dựa trên điểm chuyên cần, kiểm tra, giữa kỳ và cuối kỳ.",
        "no_grades": "Bé chưa có điểm tổng kết nào được ghi nhận.",
        "ai_title": "🤖 AI Phân Tích & Tư Vấn Hành Vi",
        "lbl_done": "Đã làm",
        "lbl_missing": "Chưa làm",
        
        # Cột dữ liệu
        "col_subject": "Môn Học", 
        "col_attend": "Chuyên Cần",
        "col_test": "Kiểm Tra",
        "col_mid": "Giữa Kỳ",
        "col_final": "Cuối Kỳ",
        "col_total": "Tổng Kết", 
        "col_rank": "Xếp Loại"
    },
    "en": {
        "err_login": "Authentication required.",
        "title": "Growth Journey & Learning Analytics",
        "btn_view_exam": "View Detailed Grades",
        "btn_view_progress": "Back to Analytics",
        "select_child": "Select child to view report:",
        "lbl_viewing": "Displaying data for:",
        "stat_attendance": "Attendance Rate",
        "stat_quiz": "Avg Test Score",
        "stat_quiz_progress": "Quizzes Completed",
        "stat_rank": "Current Rank",
        "chart_title": "📊 Final Grades Overview",
        "quiz_chart_title": "🎯 Homework Completion Ratio",
        "line_chart_title": "📈 Subject Score Progression Trend",
        "select_subject": "🔍 Select subject to view progress:",
        "journal_title": "Attendance History & Teacher's Remarks",
        "exam_title": "Final Grade Report",
        "exam_desc": "Academic results based on attendance, tests, midterm, and final exams.",
        "no_grades": "No grades recorded for this student yet.",
        "ai_title": "🤖 AI Insights & Recommendations",
        "lbl_done": "Completed",
        "lbl_missing": "Pending",
        
        # Cột dữ liệu
        "col_subject": "Subject", 
        "col_attend": "Attendance",
        "col_test": "Tests",
        "col_mid": "Midterm",
        "col_final": "Final",
        "col_total": "Final Grade", 
        "col_rank": "Classification"
    }
}

# 1. KIỂM TRA ĐĂNG NHẬP
parent_id = st.session_state.get("user_id")
token = st.session_state.get("access_token") or st.session_state.get("token")
if not parent_id or not token:
    st.error(REPORT_LABELS[lang]["err_login"])
    st.stop()

headers = {"Authorization": f"Bearer {token}", "parent-id": str(parent_id)}

# ================= CÁC HÀM LẤY DỮ LIỆU TỪ DB =================
@st.cache_data(ttl=15)
def get_my_children():
    try:
        res = requests.get(f"{API_TV3}/parent/my-children", headers=headers)
        return res.json() if res.status_code == 200 else []
    except: return []

def get_attendance_history(child_id):
    try:
        res = requests.get(f"{API_URL}/api/tv2/attendance/{child_id}", headers=headers, timeout=3)
        if res.status_code == 200:
            data = res.json()
            if data and isinstance(data, list): return pd.DataFrame(data)
    except: pass
    return pd.DataFrame()

def get_student_grades_from_db(child_id):
    try:
        res = requests.get(f"{API_URL}/api/tv2/grades/{child_id}", headers=headers, timeout=5)
        if res.status_code == 200: return res.json()
    except: pass
    return []

# --- ĐÃ KHẮC PHỤC LỖI TẠI ĐÂY ---
# Kết hợp thông tin Game (TV3) và Bài tập Quiz (TV2) lại với nhau
def get_gamification_profile(child_id, child_email=None):
    profile_data = {}
    
    # 1. Lấy thông tin Rank và EXP từ TV3
    try:
        res1 = requests.get(f"{API_TV3}/gamification/profile/{child_id}", headers=headers, timeout=3)
        if res1.status_code == 200:
            profile_data.update(res1.json())
    except: pass

    # 2. Lấy thông tin completed_tasks từ TV2 (Nơi hệ thống học sinh Quiz trực tiếp lưu trữ)
    keys_to_test = [str(child_id)]
    if child_email:
        keys_to_test.append(child_email)
        
    for key in keys_to_test:
        try:
            encoded_name = urllib.parse.quote(key)
            res2 = requests.get(f"{API_URL}/api/tv2/student/{encoded_name}/profile", timeout=3)
            if res2.status_code == 200:
                tv2_data = res2.json()
                if "completed_tasks" in tv2_data:
                    # Gộp mảng completed_tasks vào biến trả về
                    profile_data["completed_tasks"] = tv2_data["completed_tasks"]
                    break # Dừng lại ngay khi tìm thấy dữ liệu đúng
        except: pass
        
    return profile_data

def get_all_system_quizzes():
    try:
        res = requests.get(f"{API_URL}/api/tv2/quizzes", timeout=3)
        if res.status_code == 200: return res.json()
    except: pass
    return []

# ================= GIAO DIỆN CHÍNH =================
children = get_my_children()
child_options = {c["id"]: c for c in children} if children else {}

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

selected_child_id = st.selectbox(REPORT_LABELS[lang]["select_child"], options=list(child_options.keys()), format_func=lambda x: child_options[x]["name"])
selected_child = child_options[selected_child_id]
st.write(f"{REPORT_LABELS[lang]['lbl_viewing']} **{selected_child['name']}**")
st.divider()

# KÉO DỮ LIỆU THỰC TẾ
real_grades = get_student_grades_from_db(selected_child_id)
journal_df = get_attendance_history(selected_child_id)
game_profile = get_gamification_profile(selected_child_id, child_email=selected_child.get("email"))
total_quizzes = get_all_system_quizzes()

# ================= XỬ LÝ BIẾN VIEW LUỒNG DỮ LIỆU =================
if st.session_state.report_view == "progress":
    
    attendance_rate = "N/A"
    if not journal_df.empty and "Trạng Thái" in journal_df.columns:
        total_days = len(journal_df)
        present_days = len(journal_df[journal_df["Trạng Thái"] == "Có mặt"])
        attendance_rate = f"{(present_days / total_days) * 100:.0f}%"

    avg_test_score = "N/A"
    if real_grades:
        avg_test = sum(g.get("tb_kiem_tra", 0) for g in real_grades) / len(real_grades)
        avg_test_score = f"{avg_test:.1f}/10"

    # XỬ LÝ LOGIC ĐẾM QUYẾT ĐỊNH ĐỂ HIỂN THỊ
    completed_tasks = game_profile.get("completed_tasks", [])
    total_quiz_count = len(total_quizzes) if total_quizzes else 0
    done_quiz_count = len([q for q in total_quizzes if q.get("id") in completed_tasks]) if total_quizzes else 0
    quiz_progress_str = f"{done_quiz_count}/{total_quiz_count}" if total_quiz_count > 0 else "0/0"

    current_rank = game_profile.get("rank", "Beginner")

    c1, c2, c3, c4 = st.columns(4)
    c1.metric(REPORT_LABELS[lang]["stat_attendance"], attendance_rate)
    c2.metric(REPORT_LABELS[lang]["stat_quiz"], avg_test_score)
    c3.metric(REPORT_LABELS[lang]["stat_quiz_progress"], quiz_progress_str)
    c4.metric(REPORT_LABELS[lang]["stat_rank"], current_rank)
    
    st.write("---")
    
    # HIỂN THỊ SONG SONG 2 LOẠI SƠ ĐỒ ALTAIR
    col_chart1, col_chart2 = st.columns(2)
    
    with col_chart1:
        st.markdown(f"##### {REPORT_LABELS[lang]['chart_title']}")
        if real_grades:
            chart_data = pd.DataFrame(real_grades)[["subject", "tong_ket"]]
            chart_data.rename(columns={"subject": "Môn Học", "tong_ket": "Điểm"}, inplace=True)
            
            c_bar = alt.Chart(chart_data).mark_bar(
                cornerRadiusTopLeft=5, 
                cornerRadiusTopRight=5, 
                size=40,
                color="#1E88E5"
            ).encode(
                x=alt.X('Môn Học:N', title=None, axis=alt.Axis(labelAngle=0)),
                y=alt.Y('Điểm:Q', title="Điểm", scale=alt.Scale(domain=[0, 10])), 
                tooltip=['Môn Học', 'Điểm']
            ).properties(height=320)
            
            st.altair_chart(c_bar, use_container_width=True)
        else:
            st.info(REPORT_LABELS[lang]["no_grades"])
            
    with col_chart2:
        st.markdown(f"##### {REPORT_LABELS[lang]['quiz_chart_title']}")
        if total_quiz_count > 0:
            missing_quiz_count = max(0, total_quiz_count - done_quiz_count)
            quiz_chart_df = pd.DataFrame({
                "Trạng thái": [REPORT_LABELS[lang]["lbl_done"], REPORT_LABELS[lang]["lbl_missing"]],
                "Số lượng bài": [done_quiz_count, missing_quiz_count]
            })
            
            # SƠ ĐỒ VÒNG (DONUT CHART)
            c_donut = alt.Chart(quiz_chart_df).mark_arc(innerRadius=60).encode(
                theta=alt.Theta(field="Số lượng bài", type="quantitative"),
                color=alt.Color(
                    field="Trạng thái", 
                    type="nominal",
                    scale=alt.Scale(
                        domain=[REPORT_LABELS[lang]["lbl_done"], REPORT_LABELS[lang]["lbl_missing"]],
                        range=["#4CAF50", "#FF5252"] 
                    ),
                    legend=alt.Legend(title=None, orient="bottom")
                ),
                tooltip=["Trạng thái", "Số lượng bài"]
            ).properties(height=320)
            
            st.altair_chart(c_donut, use_container_width=True)
        else:
            st.info("Hệ thống chưa ghi nhận bộ đề Quiz nào.")
    
    st.write("---")
    
    # SƠ ĐỒ ĐƯỜNG (LINE CHART) THEO DÕI TIẾN TRÌNH TỪNG MÔN
    if real_grades:
        st.markdown(f"### {REPORT_LABELS[lang]['line_chart_title']}")
        
        subject_list = [g.get("subject", "N/A") for g in real_grades]
        selected_subject = st.selectbox(REPORT_LABELS[lang]["select_subject"], options=subject_list)
        
        sub_data = next((item for item in real_grades if item.get("subject") == selected_subject), None)
        
        if sub_data:
            progress_dict = {
                "Bài Thi": ["KT 1", "KT 2", "KT 3", "KT 4", "KT 5", "Giữa Kỳ", "Cuối Kỳ"],
                "Điểm Số": [
                    sub_data.get("kt_1", 0),
                    sub_data.get("kt_2", 0),
                    sub_data.get("kt_3", 0),
                    sub_data.get("kt_4", 0),
                    sub_data.get("kt_5", 0),
                    sub_data.get("giua_ky", 0),
                    sub_data.get("cuoi_ky", 0)
                ]
            }
            prog_df = pd.DataFrame(progress_dict)
            
            sort_order = ["KT 1", "KT 2", "KT 3", "KT 4", "KT 5", "Giữa Kỳ", "Cuối Kỳ"]
            
            c_line = alt.Chart(prog_df).mark_line(
                point=alt.OverlayMarkDef(filled=False, fill="white", size=80, strokeWidth=2), 
                color="#FF9800", 
                strokeWidth=3
            ).encode(
                x=alt.X("Bài Thi:N", sort=sort_order, title=None, axis=alt.Axis(labelAngle=0)), 
                y=alt.Y("Điểm Số:Q", title="Điểm", scale=alt.Scale(domain=[0, 10])), 
                tooltip=["Bài Thi", "Điểm Số"]
            ).properties(height=350)
            
            st.altair_chart(c_line, use_container_width=True)
        
        st.write("---")
    
    # Báo cáo phân tích AI
    st.subheader(REPORT_LABELS[lang]["ai_title"])
    if real_grades:
        best_sub = max(real_grades, key=lambda x: x.get("tong_ket", 0))
        weak_sub = min(real_grades, key=lambda x: x.get("tong_ket", 10))
        
        if lang == "vi":
            st.success(f"🎯 **Ưu điểm:** Bé đang học tốt nhất môn **{best_sub.get('subject')}** với điểm số đạt được là **{best_sub.get('tong_ket')}/10**.")
            if best_sub.get('subject') != weak_sub.get('subject'):
                st.warning(f"⚠️ **Điểm cần cải thiện:** Kết quả môn **{weak_sub.get('subject')}** của bé hiện đang thấp nhất lớp (**{weak_sub.get('tong_ket')}/10**). Phụ huynh hãy đôn đốc con hoàn thành thêm bài tập trên Trạm Quiz AI nhé!")
        else:
            st.success(f"🎯 **Strength:** Your child is excelling in **{best_sub.get('subject')}** with a top score of **{best_sub.get('tong_ket')}/10**.")
            if best_sub.get('subject') != weak_sub.get('subject'):
                st.warning(f"⚠️ **Area for Growth:** The final grade for **{weak_sub.get('subject')}** is currently around **{weak_sub.get('tong_ket')}/10**. Please encourage your child to complete missing homework assignments.")
    else:
        st.info(REPORT_LABELS[lang]["no_grades"])

    st.write("---")
    
    # Lịch sử điểm danh
    st.subheader(REPORT_LABELS[lang]["journal_title"])
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
        st.info("Chưa có lịch sử điểm danh được ghi nhận.")

else:
    # ---------------- VIEW 2: BẢNG KẾT QUẢ THI ĐỊNH KỲ DỮ LIỆU THẬT ----------------
    st.subheader(REPORT_LABELS[lang]["exam_title"])
    st.write(REPORT_LABELS[lang]["exam_desc"])
    
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