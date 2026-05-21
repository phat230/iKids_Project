import streamlit as st
import pandas as pd
import requests
import os
import time
from datetime import date

# ================= CRITICAL: CẤU HÌNH TRANG LUÔN ĐỂ ĐẦU FILE =================
st.set_page_config(page_title="Nhật Ký & Điểm Danh", page_icon="📓", layout="wide")

API_URL = "http://localhost:8000"

def load_css(file_name):
    current_dir = os.path.dirname(os.path.abspath(__file__)) 
    css_root = os.path.abspath(os.path.join(current_dir, "../../CSS"))
    full_path = os.path.join(css_root, file_name)
    if os.path.exists(full_path):
        with open(full_path, "r", encoding="utf-8") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

load_css("teacher/teacher_global.css")

# Lấy cấu hình ngôn ngữ hiện hành từ session_state (Mặc định là "vi")
lang = st.session_state.get("lang", "vi")

# ================= BỘ TỪ ĐIỂN SONG NGỮ =================
JOURNAL_LABELS = {
    "vi": {
        "title": "📓 Nhật Ký Giảng Dạy & Điểm Danh",
        "subtitle": "Ghi nhận điểm danh và đánh giá học sinh từ danh sách lớp thực tế.",
        "lbl_date": "Ngày dạy:",
        "lbl_select_class": "Chọn ca dạy từ lịch học:",
        "warn_no_sched": "Bạn không có lịch dạy nào trong hệ thống.",
        "sub_attendance": "👥 Điểm danh lớp: `{}`",
        "lbl_student": "Học sinh",
        "lbl_status": "Trạng thái",
        "lbl_attitude": "Thái độ",
        "lbl_comment": "Nhận xét",
        "att_options": ["Có mặt", "Vắng", "Đi trễ"],
        "emo_options": ["Xuất Sắc", "Tốt", "Bình Thường", "Kém"],
        "sub_lesson_journal": "📝 Nhật Ký Bài Giảng",
        "input_topic": "Chủ đề giảng dạy:",
        "input_videos": "Video Bài Tập Đã Dùng:",
        "input_quizzes": "Giao Bài Tập Về Nhà:",
        "input_content": "Chi Tiết Nội Dung Giảng Dạy:",
        "content_placeholder": "Nhập nội dung đã dạy tại đây...",
        "btn_save": "LƯU & GỬI BÁO CÁO",
        "err_content": "⚠️ Vui lòng nhập nội dung đã dạy.",
        "success_sent": "✅ Đã lưu nhật ký và gửi thông báo thành công!",
        "err_sent": "❌ Lỗi hệ thống:",
        "spinner_msg": "Đang gửi báo cáo cho Phụ huynh..."
    },
    "en": {
        "title": "📓 Teaching Journal & Attendance",
        "subtitle": "Record attendance and student performance from your scheduled classes.",
        "lbl_date": "Teaching Date:",
        "lbl_select_class": "Select class from schedule:",
        "warn_no_sched": "No teaching schedule found in the system.",
        "sub_attendance": "👥 Attendance for Class: `{}`",
        "lbl_student": "Student",
        "lbl_status": "Status",
        "lbl_attitude": "Behavior",
        "lbl_comment": "Comments",
        "att_options": ["Present", "Absent", "Late"],
        "emo_options": ["Outstanding", "Good", "Normal", "Needs Work"],
        "sub_lesson_journal": "📝 Lesson Journal",
        "input_topic": "Lesson Topic:",
        "input_videos": "Videos Used:",
        "input_quizzes": "Homework Assigned:",
        "input_content": "Detailed Lesson Content:",
        "content_placeholder": "Enter lesson content here...",
        "btn_save": "SAVE & DISPATCH REPORT",
        "err_content": "⚠️ Please enter the lesson content.",
        "success_sent": "✅ Journal saved and notification dispatched successfully!",
        "err_sent": "❌ System error:",
        "spinner_msg": "Dispatching report to Parents..."
    }
}

# --- KIỂM TRA QUYỀN TRUY CẬP ---
if "token" not in st.session_state or st.session_state.get("role") not in ["teacher", "admin"]:
    st.error("🔒 Bạn không có quyền truy cập trang này." if lang == "vi" else "🔒 Access Denied.")
    st.stop()

# ================= LẤY THÔNG TIN GIÁO VIÊN ĐĂNG NHẬP =================
user_info = st.session_state.get("user_info", {})
teacher_id = str(user_info.get("id", user_info.get("_id", "")))
headers = {"Authorization": f"Bearer {st.session_state.get('token', '')}"}

st.title(JOURNAL_LABELS[lang]["title"])
st.write(JOURNAL_LABELS[lang]["subtitle"])

@st.cache_data(ttl=60)
def fetch_teacher_classes():
    try:
        res = requests.get(f"{API_URL}/schedule/list", headers=headers, timeout=10)
        if res.status_code == 200:
            all_schedules = res.json()
            return [s for s in all_schedules if s.get('teacher_id') == teacher_id]
        return []
    except: return []

def fetch_students_by_class(class_id):
    try:
        res = requests.get(f"{API_URL}/classes/{class_id}/students/details", headers=headers)
        return res.json() if res.status_code == 200 else []
    except: return []

# ================= GIAO DIỆN CHÍNH =================
col_date, col_class = st.columns([1, 3])
with col_date:
    selected_date = st.date_input(JOURNAL_LABELS[lang]["lbl_date"], date.today())
my_classes = fetch_teacher_classes()
class_options = {s.get('id', s.get('_id')): f"{s['class_name']} - {s['subject']} ({s['start_time']})" for s in my_classes}

with col_class:
    if not class_options:
        st.warning(JOURNAL_LABELS[lang]["warn_no_sched"])
        selected_sid = None
    else:
        selected_sid = st.selectbox(JOURNAL_LABELS[lang]["lbl_select_class"], options=list(class_options.keys()), format_func=lambda x: class_options[x])

st.divider()

if selected_sid:
    current_schedule = next(s for s in my_classes if (s.get('id') or s.get('_id')) == selected_sid)
    col_left, col_right = st.columns([6, 4], gap="large")

    with col_left:
        st.markdown(f"### {JOURNAL_LABELS[lang]['sub_attendance'].format(current_schedule['class_name'])}")
        students = fetch_students_by_class(selected_sid)
        attendance_records = []

        if not students:
            st.info("Chưa có học sinh nào đăng ký." if lang == "vi" else "No students enrolled.")
        else:
            h1, h2, h3, h4 = st.columns([2.5, 2, 2, 3])
            h1.markdown(f"**{JOURNAL_LABELS[lang]['lbl_student']}**")
            h2.markdown(f"**{JOURNAL_LABELS[lang]['lbl_status']}**")
            h3.markdown(f"**{JOURNAL_LABELS[lang]['lbl_attitude']}**")
            h4.markdown(f"**{JOURNAL_LABELS[lang]['lbl_comment']}**")

            for student in students:
                sid = student.get("id", student.get("_id", ""))
                sname = student.get("full_name", student.get("name", "Unknown"))
                
                c_name, c_att, c_emo, c_cmt = st.columns([2.5, 2, 2, 3])
                c_name.markdown(f"<div style='padding-top: 5px;'>{sname}</div>", unsafe_allow_html=True)
                
                att = c_att.selectbox("Status", JOURNAL_LABELS[lang]["att_options"], key=f"att_{sid}", label_visibility="collapsed")
                
                is_absent = (att == JOURNAL_LABELS[lang]["att_options"][1])
                emo = c_emo.selectbox("Attitude", JOURNAL_LABELS[lang]["emo_options"], key=f"emo_{sid}", label_visibility="collapsed", disabled=is_absent)
                cmt = c_cmt.text_input("Comment", placeholder="..." if lang=="en" else "Khen ngợi...", key=f"cmt_{sid}", label_visibility="collapsed", disabled=is_absent)
                
                attendance_records.append({
                    "student_id": sid, "student_name": sname, "status": att, "feedback": emo, "comment": cmt
                })

    with col_right:
        st.markdown(f"### {JOURNAL_LABELS[lang]['sub_lesson_journal']}")
        with st.container(border=True):
            lesson_topic = st.text_input(JOURNAL_LABELS[lang]["input_topic"], value=current_schedule['subject'])
            
            try:
                res_v = requests.get(f"{API_URL}/api/tv2/videos")
                vids = res_v.json() if res_v.status_code == 200 else []
                res_q = requests.get(f"{API_URL}/api/tv2/quizzes")
                quizzes = res_q.json() if res_q.status_code == 200 else []
            except: vids, quizzes = [], []
            
            used_v = st.multiselect(JOURNAL_LABELS[lang]["input_videos"], [v['title'] for v in vids])
            assigned_q = st.multiselect(JOURNAL_LABELS[lang]["input_quizzes"], [q['title'] for q in quizzes])
            content = st.text_area(JOURNAL_LABELS[lang]["input_content"], placeholder=JOURNAL_LABELS[lang]["content_placeholder"], height=150)

            if st.button(JOURNAL_LABELS[lang]["btn_save"], type="primary", use_container_width=True):
                if not content.strip():
                    st.error(JOURNAL_LABELS[lang]["err_content"])
                else:
                    payload = {
                        "class_id": selected_sid, "class_name": current_schedule['class_name'],
                        "teacher_id": teacher_id, "date": str(selected_date),
                        "topic": lesson_topic, "content_taught": content,
                        "attendance": attendance_records, "materials": {"videos": used_v, "quizzes": assigned_q}
                    }
                    with st.spinner(JOURNAL_LABELS[lang]["spinner_msg"]):
                        res = requests.post(f"{API_URL}/api/tv2/journal", json=payload, headers=headers)
                        if res.status_code in [200, 201]:
                            st.success(JOURNAL_LABELS[lang]["success_sent"])
                            st.balloons()
                            time.sleep(2); st.rerun()
                        else:
                            st.error(f"{JOURNAL_LABELS[lang]['err_sent']} {res.text}")