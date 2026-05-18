import streamlit as st
import requests
import os
import time
from datetime import datetime, date

API = "http://127.0.0.1:8000"
TV1_API = API

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

load_css("operator/xep_lich.css")

if "token" not in st.session_state:
    st.error("Vui lòng đăng nhập")
    st.stop()

if st.session_state.get("role") not in ["operator", "admin"]:
    st.error("Chỉ nhân viên vận hành hoặc admin được truy cập")
    st.stop()

headers = {"Authorization": f"Bearer {st.session_state['token']}"}

st.title("Xếp lịch học & Gửi thông báo")
st.write("Chọn lớp học để lên lịch và tự động gửi thông báo thay đổi cho phụ huynh/học sinh.")

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
                    "sender_name": "Bộ phận Vận hành",
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
        st.error(f"Lỗi gửi thông báo tự động: {e}")

@st.cache_data(ttl=30)
def get_classes():
    try:
        res = requests.get(f"{TV1_API}/classes", timeout=10)
        return res.json() if res.status_code == 200 else []
    except: return []

def get_teachers():
    try:
        res = requests.get(f"{API}/api/auth/users", headers=headers, timeout=10)
        if res.status_code == 200:
            raw_data = res.json()
            valid_teachers = []
            for user in raw_data:
                role = str(user.get("role", user.get("quyen", ""))).lower()
                if "teacher" in role or "giáo viên" in role or "giao vien" in role:
                    status = str(user.get("status", user.get("trang_thai", "Đang làm việc")))
                    is_active = user.get("is_active", True)
                    if status not in ["Nghỉ việc", "Vô hiệu hóa", "Nghi viec", "Vo hieu hoa"] and is_active is not False:
                        valid_teachers.append(user)
            return valid_teachers
        return []
    except: return []

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

DAY_CHOICES = ["Thứ 2", "Thứ 3", "Thứ 4", "Thứ 5", "Thứ 6", "Thứ 7", "Chủ nhật"]

time_slots = []
for hour in range(7, 22):
    for minute in [0, 30]:
        if hour == 21 and minute == 30:
            continue
        time_slots.append(f"{hour:02d}:{minute:02d}")

# --- FORM TẠO LỊCH ---
st.subheader("Tạo Lịch Học Mới")
with st.form("create_schedule_form", clear_on_submit=True):
    col1, col2 = st.columns(2)
    with col1:
        if not class_options:
            st.warning("Chưa có lớp học nào.")
            selected_class_id = None
        else:
            class_labels = {k: v.get("class_name", "N/A") for k, v in class_options.items()}
            selected_class_id = st.selectbox("Chọn lớp học (*)", options=list(class_labels.keys()), format_func=lambda x: class_labels[x])
            
            if selected_class_id:
                cls_data = class_options[selected_class_id]
                st.info(f"Giáo viên phụ trách: {cls_data.get('teacher_name', 'Chưa phân công')}")
                
        if not teacher_options:
            st.warning("Chưa có danh sách giáo viên giảng dạy.")
            selected_teaching_teacher_id = None
        else:
            selected_teaching_teacher_id = st.selectbox("Giáo viên giảng dạy (*)", options=list(teacher_options.keys()), format_func=lambda x: teacher_options[x])

        subject = st.text_input("Môn học (*)")
        is_public = st.checkbox("Mở lớp (Công khai cho phụ huynh đăng ký)", value=True)

        selected_days = st.multiselect("Lịch học trong tuần (*)", options=DAY_CHOICES, default=["Thứ 7", "Chủ nhật"])
        room = st.text_input("Phòng học / Hình thức", value="Online")
        
    with col2:
        c_date1, c_date2 = st.columns(2)
        with c_date1: start_date = st.date_input("Ngày bắt đầu")
        with c_date2: end_date = st.date_input("Ngày kết thúc")
        
        c_time1, c_time2 = st.columns(2)
        with c_time1: 
            start_time = st.selectbox("Giờ bắt đầu", options=time_slots, index=time_slots.index("18:00") if "18:00" in time_slots else 0)
        with c_time2: 
            end_time = st.selectbox("Giờ kết thúc", options=time_slots, index=time_slots.index("19:30") if "19:30" in time_slots else 0)
    
    if st.form_submit_button("TẠO LỊCH HỌC"):
        if not selected_class_id or not selected_teaching_teacher_id or not subject or not selected_days or start_date > end_date:
            st.error("Vui lòng kiểm tra lại thông tin nhập liệu (điền đầy đủ môn học, chọn lớp, giáo viên và ngày hợp lệ)")
        else:
            cls_data = class_options[selected_class_id]
            payload = {
                "class_id": cls_data.get("id", cls_data.get("_id", "")),
                "class_name": cls_data.get("class_name", ""),
                "subject": subject,
                "is_public": is_public,
                "teacher_id": cls_data.get("teacher_id", ""),
                "teacher_name": cls_data.get("teacher_name", ""),
                "teaching_teacher_id": selected_teaching_teacher_id,
                "teaching_teacher_name": teacher_options[selected_teaching_teacher_id],
                "study_date": f"{start_date.strftime('%d/%m/%Y')} đến {end_date.strftime('%d/%m/%Y')}",
                "days_of_week": selected_days,
                "start_time": start_time,
                "end_time": end_time,
                "room": room,
                "created_by": st.session_state.get("user_id", "operator"),
                "status": "active"
            }
            if create_schedule(payload).status_code == 200:
                st.success("Tạo lịch thành công!")
                time.sleep(0.5)
                st.rerun()

st.divider()

# --- DANH SÁCH & SỬA GỬI THÔNG BÁO ---
st.subheader("Danh Sách Lịch Học")
if not schedules:
    st.info("Chưa có lịch học nào")
else:
    for item in schedules:
        with st.container(border=True):
            col1, col2, col3 = st.columns([3, 4, 2])
            with col1:
                st.markdown(f"### {item.get('class_name', '')}")
                st.write(f"**Môn:** {item.get('subject', '')}")
                st.caption(f"Phòng: {item.get('room', '')}")
            with col2:
                st.write(f"**Thứ:** {', '.join(item.get('days_of_week', []))}")
                st.write(f"**Khóa:** {item.get('study_date', '')}")
                st.write(f"**Giờ:** {item.get('start_time')} - {item.get('end_time')}")
                
                # Logic dự phòng: Nếu chưa có GV giảng dạy, lấy GV phụ trách làm mặc định
                gv_day = item.get('teaching_teacher_name')
                if not gv_day:
                    gv_day = item.get('teacher_name', 'Chưa phân công')
                st.write(f"**GV Dạy:** {gv_day}")
                
            with col3:
                sid = item.get("id", item.get("_id"))
                if st.button("Sửa & Gửi Tin", key=f"edit_{sid}"):
                    st.session_state["editing_schedule"] = sid
                if st.button("Xóa", key=f"del_{sid}"):
                    if delete_schedule(sid).status_code == 200: st.rerun()

            if st.session_state.get("editing_schedule") == sid:
                with st.form(f"edit_form_{sid}"):
                    st.warning("Hệ thống sẽ tự động nhắn tin cho Phụ huynh & Học sinh khi bạn nhấn Lưu.")
                    c1, c2 = st.columns(2)
                    with c1:
                        n_days = st.multiselect("Thứ trong tuần", options=DAY_CHOICES, default=item.get("days_of_week", []))
                        n_room = st.text_input("Phòng học", value=item.get("room", "Online"))
                        
                        # Thêm ô chọn sửa GV Giảng dạy để fix lỗi dữ liệu cũ
                        current_teach_id = item.get("teaching_teacher_id", item.get("teacher_id", ""))
                        t_keys = list(teacher_options.keys())
                        idx_teach = t_keys.index(current_teach_id) if current_teach_id in t_keys else 0
                        n_teach_id = st.selectbox("Đổi GV Giảng dạy", options=t_keys, format_func=lambda x: teacher_options[x], index=idx_teach)
                        
                    with c2:
                        c_s_t = item.get("start_time", "18:00")
                        c_e_t = item.get("end_time", "19:30")
                        idx_s = time_slots.index(c_s_t) if c_s_t in time_slots else 0
                        idx_e = time_slots.index(c_e_t) if c_e_t in time_slots else 0
                        
                        n_start = st.selectbox("Giờ bắt đầu", options=time_slots, index=idx_s)
                        n_end = st.selectbox("Giờ kết thúc", options=time_slots, index=idx_e)
                    
                    if st.form_submit_button("Lưu & Gửi Thông Báo", type="primary"):
                        payload = item.copy()
                        payload.update({
                            "days_of_week": n_days, 
                            "room": n_room,
                            "teaching_teacher_id": n_teach_id,
                            "teaching_teacher_name": teacher_options[n_teach_id],
                            "start_time": n_start, 
                            "end_time": n_end
                        })
                        if update_schedule(sid, payload).status_code == 200:
                            msg_title = f"Thay đổi lịch học lớp {item.get('class_name')}"
                            msg_content = f"Thông báo: Lớp {item.get('class_name')} đổi lịch sang {', '.join(n_days)} lúc {n_start}. Phòng: {n_room}. GV: {teacher_options[n_teach_id]}."
                            send_auto_notification(item.get("class_id"), item.get("class_name"), msg_title, msg_content)
                            st.success("Cập nhật thành công!")
                            st.session_state["editing_schedule"] = None
                            time.sleep(0.5)
                            st.rerun()