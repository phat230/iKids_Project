import streamlit as st
import requests
import os
import time
from datetime import datetime, date

# ================= CRITICAL: CẤU HÌNH TRANG LUÔN ĐỂ ĐẦU FILE =================
st.set_page_config(
    page_title="iKids - Xếp lịch học",
    layout="wide"
)

def load_css(file_name):
    current_dir = os.path.dirname(os.path.abspath(__file__)) 
    css_root = os.path.abspath(os.path.join(current_dir, "../../CSS"))
    full_path = os.path.join(css_root, file_name)

    if os.path.exists(full_path):
        with open(full_path, "r", encoding="utf-8") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    else:
        st.warning(f"Khong tim thay file CSS tai: {full_path}")
        
load_css("operator/operator_global.css")

API = "http://127.0.0.1:8000"
TV1_API = API

# Lấy cấu hình ngôn ngữ hiện hành từ session_state (Mặc định là "vi")
lang = st.session_state.get("lang", "vi")

# ==========================================
# BỘ TỪ ĐIỂN SONG NGỮ CHI TIẾT CỦA XEP_LICH (ĐÃ XÓA ICON)
# ==========================================
SCHEDULER_LABELS = {
    "vi": {
        "err_login": "Vui lòng đăng nhập trước khi sử dụng tính năng này.",
        "err_role": "Chỉ nhân viên vận hành hoặc quản trị viên mới được quyền truy cập vùng dữ liệu này.",
        "title": "Xếp lịch học & Gửi thông báo",
        "subtitle": "Chọn lớp học để lên lịch giảng dạy và tự động gửi thông báo thay đổi thời gian cho phụ huynh/học sinh.",
        
        # Hệ thống thông báo tự động
        "sender_name": "Bộ phận Vận hành",
        "notif_auto_err": "Lỗi gửi thông báo tự động:",
        "warn_no_class": "Chưa có lớp học nào được khởi tạo.",
        "warn_no_teacher": "Chưa có danh sách giáo viên giảng dạy.",
        
        # Form tạo lịch
        "sub_create": "Tạo Lịch Học Mới",
        "lbl_select_class": "Chọn lớp học (*)",
        "lbl_teacher_assigned": "Giáo viên phụ trách:",
        "lbl_unassigned": "Chưa phân công",
        "lbl_teaching_teacher": "Giáo viên giảng dạy (*)",
        "lbl_subject": "Môn học (*)",
        "lbl_public": "Mở lớp (Công khai cho phụ huynh đăng ký)",
        "lbl_days": "Lịch học trong tuần (*)",
        "lbl_room": "Phòng học / Hình thức",
        "lbl_start_date": "Ngày bắt đầu",
        "lbl_end_date": "Ngày kết thúc",
        "lbl_start_time": "Giờ bắt đầu",
        "lbl_end_time": "Giờ kết thúc",
        "btn_submit_create": "TẠO LỊCH HỌC",
        "err_validation": "Vui lòng kiểm tra lại thông tin nhập liệu (điền đầy đủ môn học, chọn lớp, giáo viên và khoảng ngày hợp lệ)",
        "success_created": "Tạo lịch học mới thành công!",
        
        # Danh sách lịch học
        "sub_list": "Danh Sách Lịch Học Hiện Tại",
        "info_empty_list": "Hiện chưa có lịch học nào được thiết lập trong kho dữ liệu.",
        "lbl_subject_row": "Môn:",
        "lbl_room_row": "Phòng:",
        "lbl_day_row": "Thứ:",
        "lbl_date_row": "Khóa:",
        "lbl_time_row": "Giờ:",
        "lbl_teacher_row": "GV Dạy:",
        "btn_edit_row": "Sửa & Gửi Tin",
        "btn_del_row": "Xóa",
        
        # Biểu mẫu chỉnh sửa & Gửi thông báo
        "warn_auto_sms": "Hệ thống sẽ tự động gửi tin nhắn hộp thư cho Phụ huynh & Học sinh khi bạn nhấn Lưu.",
        "lbl_edit_days": "Thứ trong tuần",
        "lbl_edit_room": "Phòng học",
        "lbl_edit_teacher": "Đổi GV Giảng dạy",
        "btn_save_edit": "Lưu & Gửi Thông Báo",
        "success_updated": "Cập nhật lịch và gửi thông báo thành công!",
        
        # Dữ liệu động thông báo thay đổi lịch
        "notif_title": "Thay đổi lịch học lớp",
        "notif_content_1": "Thông báo: Lớp",
        "notif_content_2": "đổi lịch sang các ngày",
        "notif_content_3": "lúc",
        "notif_content_4": "Phòng học:",
        "notif_content_5": "Giáo viên phụ trách:"
    },
    "en": {
        "err_login": "Authentication required. Please log in to continue.",
        "err_role": "Access denied. Only system operators or administrators have permission to access this page.",
        "title": "Class Scheduler & Auto Notifications",
        "subtitle": "Select a class to set up timetables and automatically dispatch real-time update alerts to parents and students.",
        
        # Auto notifications
        "sender_name": "Operations Department",
        "notif_auto_err": "Auto-dispatch alert notification error:",
        "warn_no_class": "No active classes available in the database.",
        "warn_no_teacher": "No valid instructor registries found.",
        
        # Schedule Form
        "sub_create": "Schedule New Class Session",
        "lbl_select_class": "Select Class (*)",
        "lbl_teacher_assigned": "In-charge Instructor:",
        "lbl_unassigned": "Unassigned",
        "lbl_teaching_teacher": "Assigned Lecturer (*)",
        "lbl_subject": "Subject / Course Title (*)",
        "lbl_public": "Open Enrollment (Publicly visible for parents to enroll)",
        "lbl_days": "Weekly Class Days (*)",
        "lbl_room": "Classroom / Format",
        "lbl_start_date": "Start Date",
        "lbl_end_date": "End Date",
        "lbl_start_time": "Start Time",
        "lbl_end_time": "End Time",
        "btn_submit_create": "GENERATE TIMETABLE",
        "err_validation": "Input validation failed. Please check fields (Subject name, select class, teacher, and logical date bounds).",
        "success_created": "Timetable session scheduled successfully!",
        
        # Timetable Directories
        "sub_list": "Current Academic Timetable",
        "info_empty_list": "There are currently no active class schedules created.",
        "lbl_subject_row": "Course:",
        "lbl_room_row": "Room:",
        "lbl_day_row": "Days:",
        "lbl_date_row": "Term:",
        "lbl_time_row": "Time:",
        "lbl_teacher_row": "Lecturer:",
        "btn_edit_row": "Edit & Dispatch SMS",
        "btn_del_row": "Delete",
        
        # Inline Modifier & Notification form
        "warn_auto_sms": "The system will automatically broadcast instant inbox messages to Parents & Students upon saving changes.",
        "lbl_edit_days": "Weekly Schedule Days",
        "lbl_edit_room": "Classroom ID",
        "lbl_edit_teacher": "Reassign Lecturer",
        "btn_save_edit": "Save & Broadcast Alerts",
        "success_updated": "Schedule updated and alert notifications dispatched!",
        
        # Dynamic Notification Translation payload
        "notif_title": "Schedule changes for class",
        "notif_content_1": "Alert Notice: Class",
        "notif_content_2": "has rescheduled to",
        "notif_content_3": "at",
        "notif_content_4": "Room / Venue:",
        "notif_content_5": "Assigned Instructor:"
    }
}

# --- KIỂM TRA ĐĂNG NHẬP & PHÂN QUYỀN BIẾN TOÀN CỤC ---
if "token" not in st.session_state:
    st.error(SCHEDULER_LABELS[lang]["err_login"])
    st.stop()

if st.session_state.get("role") not in ["operator", "admin"]:
    st.error(SCHEDULER_LABELS[lang]["err_role"])
    st.stop()

headers = {"Authorization": f"Bearer {st.session_state['token']}"}

st.title(SCHEDULER_LABELS[lang]["title"])
st.write(SCHEDULER_LABELS[lang]["subtitle"])

def send_auto_notification(class_id, class_name, title, content):
    try:
        res = requests.get(f"{API}/classes/{class_id}/students/details", headers=headers)
        if res.status_code == 200:
            students = res.json()
            for s in students:
                stu_id = s.get("Mã HS")
                payload_stu = {
                    "sender_id": st.session_state.get("user_id"),
                    "sender_role": "operator",
                    "sender_name": SCHEDULER_LABELS[lang]["sender_name"],
                    "receiver_id": stu_id,
                    "receiver_role": "student",
                    "type": "schedule",
                    "title": title,
                    "content": content
                }
                requests.post(f"{API}/api/notifications/send", json=payload_stu)
                
                payload_parent = payload_stu.copy()
                payload_parent["receiver_role"] = "parent"
                payload_parent["receiver_id"] = "all"
                requests.post(f"{API}/api/notifications/send", json=payload_parent)
    except Exception as e:
        st.error(f"{SCHEDULER_LABELS[lang]['notif_auto_err']} {e}")

@st.cache_data(ttl=30)
def get_classes():
    try:
        res = requests.get(f"{TV1_API}/classes", timeout=10)
        return res.json() if res.status_code == 200 else []
    except: return []

def get_teachers():
    """Gọi API lấy toàn bộ User để lọc tự do bằng Python (Chống sót & chống trùng lặp)"""
    try:
        res = requests.get(f"{API}/api/auth/users", headers=headers, timeout=5)
        if res.status_code == 200:
            raw_data = res.json()
            valid_teachers = []
            seen_emails = set()
            
            for user in raw_data:
                role = str(user.get("role", user.get("quyen", ""))).lower()
                # Bao quát tất cả các Role có thể ghi nhầm
                if "teacher" in role or "giáo viên" in role or "gv" in role:
                    status = str(user.get("status", "Đang làm việc")).lower()
                    
                    # Xử lý trường hợp DB thiếu is_active (mặc định cho là True)
                    is_active = user.get("is_active", True)
                    
                    # Lọc bỏ những người nghỉ việc hoặc vô hiệu hóa
                    if status not in ["nghỉ việc", "đã nghỉ việc", "vô hiệu hóa"] and str(is_active).lower() != "false":
                        email = user.get("email", "")
                        # Chống trùng lặp 2 tài khoản y chang nhau
                        if email not in seen_emails:
                            valid_teachers.append(user)
                            seen_emails.add(email)
                            
            if valid_teachers:
                return valid_teachers
    except: pass
    
    # Fallback dự phòng
    try:
        res = requests.get(f"{API}/teachers", headers=headers, timeout=5)
        if res.status_code == 200:
            return res.json()
    except: pass
    return []

def get_schedules():
    try:
        res = requests.get(f"{TV1_API}/schedule/list", headers=headers, timeout=10)
        return res.json() if res.status_code == 200 else []
    except: return []

def create_schedule(data):
    return requests.post(f"{TV1_API}/schedule/create", json=data, headers=headers)

def update_schedule(schedule_id, data):
    return requests.put(f"{TV1_API}/schedule/{schedule_id}", json=data, headers=headers)

def delete_schedule(schedule_id):
    return requests.delete(f"{TV1_API}/schedule/{schedule_id}", headers=headers)

classes = get_classes()
schedules = get_schedules()
teachers = get_teachers()

class_options = {str(c.get("id", c.get("_id", ""))): c for c in classes if isinstance(c, dict)}
teacher_options = {str(t.get("id", t.get("_id", ""))): f"{t.get('full_name', t.get('name', ''))} ({t.get('email', '')})" for t in teachers}

DAY_CHOICES_VI = ["Thứ 2", "Thứ 3", "Thứ 4", "Thứ 5", "Thứ 6", "Thứ 7", "Chủ nhật"]
DAY_CHOICES_EN = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
DAY_CHOICES = DAY_CHOICES_VI if lang == "vi" else DAY_CHOICES_EN

time_slots = []
for hour in range(7, 22):
    for minute in [0, 30]:
        if hour == 21 and minute == 30:
            continue
        time_slots.append(f"{hour:02d}:{minute:02d}")

# --- FORM TẠO LỊCH HỌC MỚI (CẤU TRÚC 2 CỘT AN TOÀN TUYỆT ĐỐI) ---
with st.container(border=True):
    st.subheader(SCHEDULER_LABELS[lang]["sub_create"])
    with st.form("create_schedule_form", clear_on_submit=True):
        
        # Dòng 1: Chọn lớp
        if not class_options:
            st.warning(SCHEDULER_LABELS[lang]["warn_no_class"])
            selected_class_id = None
        else:
            class_labels = {k: v.get("class_name", "N/A") for k, v in class_options.items()}
            selected_class_id = st.selectbox(SCHEDULER_LABELS[lang]["lbl_select_class"], options=list(class_labels.keys()), format_func=lambda x: class_labels[x])
            
            if selected_class_id:
                cls_data = class_options[selected_class_id]
                t_name_assigned = cls_data.get('teacher_name') or SCHEDULER_LABELS[lang]["lbl_unassigned"]
                st.info(f"{SCHEDULER_LABELS[lang]['lbl_teacher_assigned']} {t_name_assigned}")
                
        # Dòng 2: Môn học và GV giảng dạy
        c1, c2 = st.columns(2)
        with c1:
            if not teacher_options:
                st.warning(SCHEDULER_LABELS[lang]["warn_no_teacher"])
                selected_teaching_teacher_id = None
            else:
                t_keys = list(teacher_options.keys())
                selected_teaching_teacher_id = st.selectbox(SCHEDULER_LABELS[lang]["lbl_teaching_teacher"], options=t_keys, format_func=lambda x: teacher_options[x])
        with c2:
            subject = st.text_input(SCHEDULER_LABELS[lang]["lbl_subject"])

        # Dòng 3: Khung thời gian Ngày
        c3, c4 = st.columns(2)
        with c3: start_date = st.date_input(SCHEDULER_LABELS[lang]["lbl_start_date"])
        with c4: end_date = st.date_input(SCHEDULER_LABELS[lang]["lbl_end_date"])
        
        # Dòng 4: Khung thời gian Giờ
        c5, c6 = st.columns(2)
        with c5: start_time = st.selectbox(SCHEDULER_LABELS[lang]["lbl_start_time"], options=time_slots, index=time_slots.index("18:00") if "18:00" in time_slots else 0)
        with c6: end_time = st.selectbox(SCHEDULER_LABELS[lang]["lbl_end_time"], options=time_slots, index=time_slots.index("19:30") if "19:30" in time_slots else 0)

        # Dòng 5: Thứ trong tuần và Phòng học
        c7, c8 = st.columns(2)
        with c7:
            default_days = ["Thứ 7", "Chủ nhật"] if lang == "vi" else ["Saturday", "Sunday"]
            selected_days = st.multiselect(SCHEDULER_LABELS[lang]["lbl_days"], options=DAY_CHOICES, default=default_days)
        with c8:
            room = st.text_input(SCHEDULER_LABELS[lang]["lbl_room"], value="Online")
            
        is_public = st.checkbox(SCHEDULER_LABELS[lang]["lbl_public"], value=True)

        if st.form_submit_button(SCHEDULER_LABELS[lang]["btn_submit_create"], type="primary", use_container_width=True):
            if not selected_class_id or not selected_teaching_teacher_id or not subject.strip() or not selected_days or start_date > end_date:
                st.error(SCHEDULER_LABELS[lang]["err_validation"])
            else:
                cls_data = class_options[selected_class_id]
                
                if lang == "en":
                    saved_days = [DAY_CHOICES_VI[DAY_CHOICES_EN.index(d)] for d in selected_days]
                else:
                    saved_days = selected_days

                payload = {
                    "class_id": cls_data.get("id", cls_data.get("_id", "")),
                    "class_name": cls_data.get("class_name", ""),
                    "subject": subject.strip(),
                    "is_public": is_public,
                    "teacher_id": cls_data.get("teacher_id", ""),
                    "teacher_name": cls_data.get("teacher_name", ""),
                    "teaching_teacher_id": selected_teaching_teacher_id,
                    "teaching_teacher_name": teacher_options[selected_teaching_teacher_id],
                    "study_date": f"{start_date.strftime('%d/%m/%Y')} đến {end_date.strftime('%d/%m/%Y')}",
                    "days_of_week": saved_days,
                    "start_time": start_time,
                    "end_time": end_time,
                    "room": room.strip(),
                    "created_by": st.session_state.get("user_id", "operator"),
                    "status": "active"
                }
                if create_schedule(payload).status_code == 200:
                    st.success(SCHEDULER_LABELS[lang]["success_created"])
                    time.sleep(0.5)
                    st.rerun()

st.divider()

# --- DANH SÁCH LỊCH HỌC HOÀN CHỈNH ---
st.subheader(SCHEDULER_LABELS[lang]["sub_list"])
if not schedules:
    st.info(SCHEDULER_LABELS[lang]["info_empty_list"])
else:
    for item in schedules:
        with st.container(border=True):
            col1, col2, col3 = st.columns([3, 4, 2])
            
            raw_days = item.get('days_of_week', [])
            if lang == "en":
                display_days = [DAY_CHOICES_EN[DAY_CHOICES_VI.index(d)] for d in raw_days if d in DAY_CHOICES_VI]
            else:
                display_days = raw_days

            with col1:
                st.markdown(f"**{item.get('class_name', '')}**")
                st.write(f"{SCHEDULER_LABELS[lang]['lbl_subject_row']} {item.get('subject', '')}")
                st.caption(f"{SCHEDULER_LABELS[lang]['lbl_room_row']} {item.get('room', '')}")
            with col2:
                st.write(f"{SCHEDULER_LABELS[lang]['lbl_day_row']} {', '.join(display_days)}")
                
                study_date_display = item.get('study_date', '')
                if lang == "en": study_date_display = study_date_display.replace("đến", "to")
                
                st.write(f"{SCHEDULER_LABELS[lang]['lbl_date_row']} {study_date_display}")
                st.write(f"{SCHEDULER_LABELS[lang]['lbl_time_row']} {item.get('start_time')} - {item.get('end_time')}")
                
                gv_day = item.get('teaching_teacher_name')
                if not gv_day:
                    gv_day = item.get('teacher_name', SCHEDULER_LABELS[lang]["lbl_unassigned"])
                st.write(f"{SCHEDULER_LABELS[lang]['lbl_teacher_row']} {gv_day}")
                
            with col3:
                sid = item.get("id", item.get("_id"))
                if st.button(SCHEDULER_LABELS[lang]["btn_edit_row"], key=f"edit_{sid}", use_container_width=True):
                    st.session_state["editing_schedule"] = sid
                if st.button(SCHEDULER_LABELS[lang]["btn_del_row"], key=f"del_{sid}", use_container_width=True):
                    if delete_schedule(sid).status_code == 200: 
                        st.rerun()

            if st.session_state.get("editing_schedule") == sid:
                with st.form(f"edit_form_{sid}"):
                    st.warning(SCHEDULER_LABELS[lang]["warn_auto_sms"])
                    c1, c2 = st.columns(2)
                    with c1:
                        item_days = item.get("days_of_week", [])
                        if lang == "en":
                            default_edit_days = [DAY_CHOICES_EN[DAY_CHOICES_VI.index(d)] for d in item_days if d in DAY_CHOICES_VI]
                        else:
                            default_edit_days = item_days

                        n_days = st.multiselect(SCHEDULER_LABELS[lang]["lbl_edit_days"], options=DAY_CHOICES, default=default_edit_days)
                        n_room = st.text_input(SCHEDULER_LABELS[lang]["lbl_edit_room"], value=item.get("room", "Online"))
                        
                        current_teach_id = item.get("teaching_teacher_id", item.get("teacher_id", ""))
                        t_keys = list(teacher_options.keys())
                        idx_teach = t_keys.index(current_teach_id) if current_teach_id in t_keys else 0
                        
                        if t_keys:
                            n_teach_id = st.selectbox(SCHEDULER_LABELS[lang]["lbl_edit_teacher"], options=t_keys, format_func=lambda x: teacher_options[x], index=idx_teach)
                        else:
                            st.warning("Lỗi API tải danh sách giáo viên")
                            n_teach_id = current_teach_id
                        
                    with c2:
                        c_s_t = item.get("start_time", "18:00")
                        c_e_t = item.get("end_time", "19:30")
                        idx_s = time_slots.index(c_s_t) if c_s_t in time_slots else 0
                        idx_e = time_slots.index(c_e_t) if c_e_t in time_slots else 0
                        
                        n_start = st.selectbox(SCHEDULER_LABELS[lang]["lbl_start_time"], options=time_slots, index=idx_s)
                        n_end = st.selectbox(SCHEDULER_LABELS[lang]["lbl_end_time"], options=time_slots, index=idx_e)
                    
                    if st.form_submit_button(SCHEDULER_LABELS[lang]["btn_save_edit"], type="primary", use_container_width=True):
                        if lang == "en":
                            saved_edit_days = [DAY_CHOICES_VI[DAY_CHOICES_EN.index(d)] for d in n_days]
                        else:
                            saved_edit_days = n_days

                        payload = item.copy()
                        payload_updates = {
                            "days_of_week": saved_edit_days, 
                            "room": n_room.strip(),
                            "start_time": n_start, 
                            "end_time": n_end
                        }
                        if t_keys:
                            payload_updates["teaching_teacher_id"] = n_teach_id
                            payload_updates["teaching_teacher_name"] = teacher_options[n_teach_id]
                            
                        payload.update(payload_updates)
                        
                        if update_schedule(sid, payload).status_code == 200:
                            gv_day_moi = teacher_options[n_teach_id] if t_keys else gv_day
                            msg_title = f"{SCHEDULER_LABELS[lang]['notif_title']} {item.get('class_name')}"
                            msg_content = f"{SCHEDULER_LABELS[lang]['notif_content_1']} {item.get('class_name')} {SCHEDULER_LABELS[lang]['notif_content_2']} {', '.join(n_days)} {SCHEDULER_LABELS[lang]['notif_content_3']} {n_start}. {SCHEDULER_LABELS[lang]['notif_content_4']} {n_room}. {SCHEDULER_LABELS[lang]['notif_content_5']} {gv_day_moi}."
                            
                            send_auto_notification(item.get("class_id"), item.get("class_name"), msg_title, msg_content)
                            
                            st.success(SCHEDULER_LABELS[lang]["success_updated"])
                            st.session_state["editing_schedule"] = None
                            time.sleep(0.5)
                            st.rerun()