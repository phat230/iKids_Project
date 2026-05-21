import streamlit as st
import pandas as pd
import requests
import os
import time

# ================= CRITICAL: CẤU HÌNH TRANG LUÔN ĐỂ ĐẦU FILE =================
st.set_page_config(page_title="Đăng Ký Lớp Học", page_icon=None, layout="wide")

# Cấu hình API Backend
API_URL = "http://localhost:8000"
API_TV3 = "http://localhost:8000/api/tv3"

# ================= HÀM ĐỌC FILE CSS =================
def load_css(file_name):
    current_dir = os.path.dirname(os.path.abspath(__file__))
    css_root = os.path.abspath(os.path.join(current_dir, "../../CSS"))
    full_path = os.path.join(css_root, file_name)

    if os.path.exists(full_path):
        with open(full_path, "r", encoding="utf-8") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    else:
        st.warning(f"Không tìm thấy file CSS tại: {full_path}")

load_css("parent/parent_global.css")

lang = st.session_state.get("lang", "vi")

# ==========================================
# BỘ TỪ ĐIỂN SONG NGỮ CHI TIẾT
# ==========================================
ENROLL_LABELS = {
    "vi": {
        "title": "Đăng Ký Lớp Học Cho Con",
        "subtitle": "Dưới đây là danh sách các lớp học đang mở. Phụ huynh có thể chọn lớp phù hợp cho con em mình.",
        "err_login": "Vui lòng đăng nhập với tài khoản Phụ huynh để đăng ký lớp học.",
        "warn_no_child": "Bạn chưa có hồ sơ học sinh nào. Vui lòng sang trang 'Quản Lý Con Em' để tạo tài khoản cho bé trước khi đăng ký lớp!",
        "err_connection": "Không thể kết nối đến máy chủ Backend:",
        
        "expander_schedule": "Thời Khóa Biểu Hiện Tại Của Bé",
        "expander_desc": "Vui lòng kiểm tra lịch học hiện tại của các bé dưới đây để tránh đăng ký lớp mới bị trùng thời gian.",
        "info_no_schedule": "Bé hiện chưa có lịch học nào.",
        "session_morning": "SÁNG",
        "session_afternoon": "CHIỀU",
        "session_evening": "TỐI",
        "session_label": "Buổi",
        
        "sub_enroll_section": "Danh Sách Lớp Học Đang Mở",
        "select_child_global": "Chọn học sinh để xem các môn học mới:",
        "lbl_registering_for": "Đăng ký cho bé:",
        "info_all_enrolled": "Học sinh này đã tham gia tất cả các lớp đang mở hoặc hiện chưa có lớp mới.",
        "info_empty_classes": "Hiện tại hệ thống chưa có lớp học nào đang mở đăng ký công khai.",
        "lbl_class_unknown": "Tên lớp chưa rõ",
        "lbl_subject": "Môn học:",
        "lbl_sub_unassigned": "Chưa cập nhật",
        "lbl_teacher": "Giáo viên phụ trách:",
        "lbl_teacher_arranging": "Đang xếp",
        "btn_enroll": "Xác Nhận Đăng Ký Lớp",
        "success_enrolled": "Đã đăng ký thành công cho bé",
        "err_failed_enroll": "Đăng ký thất bại. Lớp học có thể đã đầy hoặc đóng sổ.",
        "err_post_connection": "Lỗi kết nối khi gửi yêu cầu đăng ký học."
    },
    "en": {
        "title": "Course Enrollment for Children",
        "subtitle": "Below is the list of active open classes. Parents can review and select the most suitable option for their children.",
        "err_login": "Authentication required. Please log in with a Parent account to enroll in classes.",
        "warn_no_child": "No student profiles found associated with your account. Please go to 'Manage Children' to create a profile for your child first!",
        "err_connection": "Unable to establish a connection to the Backend server:",
        
        "expander_schedule": "Children's Current Timetable",
        "expander_desc": "Please review your children's current schedules below to avoid enrolling in conflicting time slots.",
        "info_no_schedule": "This child currently has no scheduled classes.",
        "session_morning": "MORNING",
        "session_afternoon": "AFTERNOON",
        "session_evening": "EVENING",
        "session_label": "Session",
        
        "sub_enroll_section": "Open Classes for Registration",
        "select_child_global": "Select a child to view available new courses:",
        "lbl_registering_for": "Enrolling:",
        "info_all_enrolled": "This student is already enrolled in all available classes or no new classes are open.",
        "info_empty_classes": "There are currently no open classes available for public registration.",
        "lbl_class_unknown": "Unknown Class Title",
        "lbl_subject": "Subject:",
        "lbl_sub_unassigned": "Unassigned",
        "lbl_teacher": "Instructor:",
        "lbl_teacher_arranging": "TBD",
        "btn_enroll": "Confirm Enrollment",
        "success_enrolled": "Registration successful for",
        "err_failed_enroll": "Enrollment failed. The selected class might be fully occupied.",
        "err_post_connection": "Connection error occurred while submitting enrollment request."
    }
}

# Ánh xạ từ điển Thứ trong tuần
DAY_MAP_EN = {
    "Thứ 2": "Monday", "Thứ 3": "Tuesday", "Thứ 4": "Wednesday", 
    "Thứ 5": "Thursday", "Thứ 6": "Friday", "Thứ 7": "Saturday", "Chủ nhật": "Sunday"
}

st.title(ENROLL_LABELS[lang]["title"])
st.write(ENROLL_LABELS[lang]["subtitle"])

# 1. KIỂM TRA ĐĂNG NHẬP
parent_id = st.session_state.get("user_id")
token = st.session_state.get("access_token") or st.session_state.get("token")

if not parent_id or not token:
    st.error(ENROLL_LABELS[lang]["err_login"])
    st.stop()

headers = {"Authorization": f"Bearer {token}", "parent-id": str(parent_id)}

# 2. LẤY DANH SÁCH CÁC CON CỦA PHỤ HUYNH
@st.cache_data(ttl=30)
def get_my_children():
    try:
        res = requests.get(f"{API_TV3}/parent/my-children", headers=headers)
        return res.json() if res.status_code == 200 else []
    except:
        return []

children = get_my_children()

if not children:
    st.warning(ENROLL_LABELS[lang]["warn_no_child"])
    st.stop()

child_options = {c["id"]: c["name"] for c in children}

# 3. LẤY TOÀN BỘ DỮ LIỆU LỚP VÀ LỊCH ĐỂ XỬ LÝ
try:
    res_public = requests.get(f"{API_URL}/classes/public")
    public_classes = res_public.json() if res_public.status_code == 200 else []
except Exception as e:
    st.error(f"{ENROLL_LABELS[lang]['err_connection']} {e}")
    public_classes = []

try:
    res_all = requests.get(f"{API_URL}/classes", headers=headers, timeout=5)
    all_classes = res_all.json() if res_all.status_code == 200 else public_classes
except:
    all_classes = public_classes

try:
    res_sched = requests.get(f"{API_URL}/schedule/list", headers=headers, timeout=5)
    schedules = res_sched.json() if res_sched.status_code == 200 else []
except:
    schedules = []

schedule_subject_map = {}
for s in schedules:
    c_id = str(s.get("class_id", ""))
    subj = s.get("subject", "")
    if c_id and subj:
        schedule_subject_map[c_id] = subj

# =======================================================
# THỜI KHÓA BIỂU DẠNG LƯỚI (GRID TIMETABLE)
# =======================================================
def render_child_timetable(child_data):
    child_id = child_data["id"]
    
    day_names_vi = ["Thứ 2", "Thứ 3", "Thứ 4", "Thứ 5", "Thứ 6", "Thứ 7", "Chủ nhật"]
    day_names_en = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    display_days = day_names_vi if lang == "vi" else day_names_en
    
    sessions_vi = ["SÁNG", "CHIỀU", "TỐI"]
    sessions_en = ["MORNING", "AFTERNOON", "EVENING"]
    display_sessions = sessions_vi if lang == "vi" else sessions_en
    
    schedule_map = {
        sessions_vi[0]: {d: [] for d in day_names_vi},
        sessions_vi[1]: {d: [] for d in day_names_vi},
        sessions_vi[2]: {d: [] for d in day_names_vi}
    }
    
    has_classes = False

    for cls in all_classes:
        if child_id in cls.get("student_ids", []):
            c_id = str(cls.get("id", cls.get("_id", "")))
            sched = next((s for s in schedules if str(s.get("class_id")) == c_id), None)
            
            if sched:
                has_classes = True
                start_time = sched.get("start_time", "00:00")
                try:
                    hour = int(start_time.split(":")[0])
                except:
                    hour = 8
                
                if hour < 12: session = sessions_vi[0]
                elif hour < 17: session = sessions_vi[1]
                else: session = sessions_vi[2]
                
                for d in sched.get("days_of_week", []):
                    if d in day_names_vi:
                        schedule_map[session][d].append({
                            "class_name": cls.get("class_name"),
                            "subject": sched.get("subject", cls.get("subject", "")),
                            "time": f"{start_time} - {sched.get('end_time', '')}",
                            "room": sched.get("room", "Online")
                        })
    
    if not has_classes:
        st.info(ENROLL_LABELS[lang]["info_no_schedule"])
        return

    css_style = """
    <style>
    .tt-table { width: 100%; border-collapse: collapse; text-align: center; margin-bottom: 20px; font-family: sans-serif; table-layout: fixed; }
    .tt-table th { background-color: #f8fafc; padding: 12px 4px; border: 1px solid #cbd5e1; font-weight: 600; color: #334155; font-size: 0.9em; }
    .tt-table td { border: 1px solid #cbd5e1; padding: 8px; vertical-align: top; }
    .tt-table th:first-child { width: 6%; }
    .tt-session { font-weight: bold; background-color: #f1f5f9; vertical-align: middle !important; color: #475569; writing-mode: vertical-rl; transform: rotate(180deg); text-align: center; letter-spacing: 2px;}
    .tt-card { background-color: #f0f9ff; border-left: 4px solid #0284c7; border-radius: 4px; padding: 8px; margin-bottom: 8px; text-align: left; }
    .tt-title { font-weight: 700; color: #0369a1; font-size: 0.85em; margin-bottom: 4px; line-height: 1.2;}
    .tt-subj { font-size: 0.8em; color: #334155; margin-bottom: 4px; font-weight: 500;}
    .tt-meta { font-size: 0.75em; color: #64748b; margin-top: 2px; }
    </style>
    """
    
    html_content = f"{css_style}<table class='tt-table'><thead><tr><th>{ENROLL_LABELS[lang]['session_label']}</th>"
    for d in display_days:
        html_content += f"<th>{d}</th>"
    html_content += "</tr></thead><tbody>"

    for idx, session_vi in enumerate(sessions_vi):
        session_label = display_sessions[idx]
        html_content += f"<tr><td class='tt-session'>{session_label}</td>"
        
        for day_vi in day_names_vi:
            html_content += "<td>"
            classes_in_slot = schedule_map[session_vi][day_vi]
            for c in classes_in_slot:
                html_content += f"<div class='tt-card'>"
                html_content += f"<div class='tt-title'>{c['class_name']}</div>"
                html_content += f"<div class='tt-subj'>{c['subject']}</div>"
                html_content += f"<div class='tt-meta'>{c['time']} | {c['room']}</div>"
                html_content += "</div>"
            html_content += "</td>"
        html_content += "</tr>"

    html_content += "</tbody></table>"
    st.markdown(html_content, unsafe_allow_html=True)

st.subheader(ENROLL_LABELS[lang]["expander_schedule"])
st.write(ENROLL_LABELS[lang]["expander_desc"])
st.write("") 

if len(children) > 1:
    tabs = st.tabs([c["name"] for c in children])
    for i, child in enumerate(children):
        with tabs[i]:
            render_child_timetable(child)
else:
    render_child_timetable(children[0])

st.divider()

# =======================================================
# BỘ LỌC ĐĂNG KÝ VÀ DANH SÁCH LỚP (ĐÃ ẨN LỚP ĐANG HỌC)
# =======================================================
st.subheader(ENROLL_LABELS[lang]["sub_enroll_section"])

# Global Child Selector
selected_child_id = st.selectbox(
    ENROLL_LABELS[lang]["select_child_global"],
    options=list(child_options.keys()),
    format_func=lambda x: child_options[x]
)

st.write("") 

if not public_classes:
    st.info(ENROLL_LABELS[lang]["info_empty_classes"])
else:
    # Lọc ẩn các lớp bé đã tham gia
    available_classes = [cls for cls in public_classes if selected_child_id not in cls.get("student_ids", [])]

    if not available_classes:
        st.info(ENROLL_LABELS[lang]["info_all_enrolled"])
    else:
        for cls in available_classes:
            with st.container(border=True):
                col1, col2 = st.columns([3, 2])
                
                class_id = str(cls.get('id', cls.get('_id', '')))
                
                with col1:
                    st.markdown(f"#### {cls.get('class_name', ENROLL_LABELS[lang]['lbl_class_unknown'])}")
                    
                    subject_raw = schedule_subject_map.get(class_id, cls.get('subject', ENROLL_LABELS[lang]['lbl_sub_unassigned']))
                    subject_display = subject_raw
                    if lang == "en" and subject_raw == "Chưa xác định":
                        subject_display = "Unassigned"
                    
                    st.write(f"**{ENROLL_LABELS[lang]['lbl_subject']}** {subject_display}")
                    
                    t_name = cls.get('teacher_name') or ENROLL_LABELS[lang]['lbl_teacher_arranging']
                    if t_name == "Chưa phân công":
                        t_name = "Unassigned" if lang == "en" else "Chưa phân công"
                    st.caption(f"{ENROLL_LABELS[lang]['lbl_teacher']} {t_name}")
                
                with col2:
                    st.write(f"**{ENROLL_LABELS[lang]['lbl_registering_for']}** {child_options[selected_child_id]}")
                    
                    if st.button(ENROLL_LABELS[lang]["btn_enroll"], key=f"btn_{class_id}", type="primary", use_container_width=True):
                        payload = {"class_id": class_id, "student_id": selected_child_id}
                        try:
                            register_res = requests.post(f"{API_URL}/classes/register", json=payload)
                            
                            if register_res.status_code in [200, 201]:
                                st.success(f"{ENROLL_LABELS[lang]['success_enrolled']} **{child_options[selected_child_id]}**!")
                                time.sleep(0.5)
                                st.rerun()
                            else:
                                st.error(ENROLL_LABELS[lang]["err_failed_enroll"])
                        except Exception:
                            st.error(ENROLL_LABELS[lang]["err_post_connection"])