import streamlit as st
import requests
from datetime import datetime, date

API = "http://127.0.0.1:8000"
TV1_API = API

st.set_page_config(
    page_title="iKids - Xếp lịch học",
    page_icon="📅",
    layout="wide"
)

# =========================
# CHECK LOGIN
# =========================
if "token" not in st.session_state:
    st.error("Vui lòng đăng nhập")
    st.stop()

if "role" not in st.session_state:
    st.error("Không tìm thấy quyền tài khoản")
    st.stop()

if st.session_state["role"] not in ["operator", "admin"]:
    st.error("Chỉ nhân viên vận hành hoặc admin được truy cập")
    st.stop()

headers = {
    "Authorization": f"Bearer {st.session_state['token']}"
}

st.title("📅 Xếp lịch học & Gửi thông báo")
st.write("Chọn lớp học để lên lịch và tự động gửi thông báo thay đổi cho phụ huynh/học sinh.")

# =========================
# HÀM HỖ TRỢ THÔNG BÁO TỰ ĐỘNG
# =========================
def send_auto_notification(class_id, class_name, title, content):
    """Gửi thông báo tới toàn bộ học sinh và phụ huynh trong lớp khi sửa lịch"""
    try:
        # 1. Lấy danh sách học viên thực tế của lớp
        res = requests.get(f"{API}/classes/{class_id}/students/details", headers=headers)
        if res.status_code == 200:
            students = res.json()
            for s in students:
                stu_id = s.get("Mã HS")
                
                # A. Thông báo cho Học sinh
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

                # B. Thông báo cho Phụ huynh (Gửi theo ID nếu có hoặc gửi theo role)
                payload_parent = payload_stu.copy()
                payload_parent["receiver_role"] = "parent"
                payload_parent["receiver_id"] = "all" # Đảm bảo phụ huynh của bé thấy tin
                requests.post(f"{API}/api/notifications/send", json=payload_parent)
    except Exception as e:
        st.error(f"Lỗi gửi thông báo tự động: {e}")

# =========================
# HÀM GỌI API DỮ LIỆU
# =========================
@st.cache_data(ttl=30)
def get_classes():
    try:
        res = requests.get(f"{TV1_API}/classes", timeout=10)
        if res.status_code == 200:
            data = res.json()
            return [c for c in data if isinstance(c, dict)]
        return []
    except Exception as e:
        st.error(f"Lỗi lấy danh sách lớp học: {e}")
        return []

def get_schedules():
    try:
        res = requests.get(f"{TV1_API}/schedule/list", headers=headers, timeout=10)
        if res.status_code == 200:
            return res.json()
        return []
    except Exception as e:
        st.error(f"Lỗi lấy lịch học: {e}")
        return []

def create_schedule(data):
    try:
        return requests.post(f"{TV1_API}/schedule/create", json=data, headers=headers, timeout=10)
    except Exception as e:
        st.error(f"Lỗi tạo lịch: {e}")
        return None

def update_schedule(schedule_id, data):
    try:
        return requests.put(f"{TV1_API}/schedule/{schedule_id}", json=data, headers=headers, timeout=10)
    except Exception as e:
        st.error(f"Lỗi cập nhật lịch: {e}")
        return None

def delete_schedule(schedule_id):
    try:
        return requests.delete(f"{TV1_API}/schedule/{schedule_id}", headers=headers, timeout=10)
    except Exception as e:
        st.error(f"Lỗi xóa lịch: {e}")
        return None

# =========================
# LOAD DATA
# =========================
classes = get_classes()
schedules = get_schedules()
class_options = {f"{c.get('class_name', 'Không tên')} - {c.get('subject', '')}": c for c in classes}
DAY_CHOICES = ["Thứ 2", "Thứ 3", "Thứ 4", "Thứ 5", "Thứ 6", "Thứ 7", "Chủ nhật"]

# =========================
# FORM TẠO LỊCH (GIỮ NGUYÊN)
# =========================
st.subheader("➕ Tạo lịch học mới")
with st.form("create_schedule_form", clear_on_submit=True):
    col1, col2 = st.columns(2)
    with col1:
        if not class_options:
            st.warning("⚠️ Chưa có lớp học nào.")
            selected_class_label = None
        else:
            selected_class_label = st.selectbox("Chọn lớp học (*)", options=list(class_options.keys()))
            if selected_class_label:
                cls_data = class_options[selected_class_label]
                st.info(f"👨‍🏫 Giáo viên phụ trách: **{cls_data.get('teacher_name', 'Chưa xếp')}**")
        selected_days = st.multiselect("Lịch học trong tuần (*)", options=DAY_CHOICES, default=["Thứ 7", "Chủ nhật"])
        room = st.text_input("Phòng học / Hình thức", value="Online")
    with col2:
        c_date1, c_date2 = st.columns(2)
        with c_date1: start_date = st.date_input("Ngày bắt đầu")
        with c_date2: end_date = st.date_input("Ngày kết thúc")
        c_time1, c_time2 = st.columns(2)
        with c_time1: start_time = st.time_input("Giờ bắt đầu")
        with c_time2: end_time = st.time_input("Giờ kết thúc")
    if st.form_submit_button("✅ Tạo lịch học"):
        if not selected_class_label or not selected_days or start_date > end_date:
            st.error("Vui lòng kiểm tra lại thông tin nhập liệu")
        else:
            cls_data = class_options[selected_class_label]
            payload = {
                "class_id": cls_data.get("id", ""),
                "class_name": cls_data.get("class_name", ""),
                "subject": cls_data.get("subject", ""),
                "teacher_id": cls_data.get("teacher_id", ""),
                "teacher_name": cls_data.get("teacher_name", ""),
                "study_date": f"{start_date.strftime('%d/%m/%Y')} đến {end_date.strftime('%d/%m/%Y')}",
                "days_of_week": selected_days,
                "start_time": start_time.strftime("%H:%M"),
                "end_time": end_time.strftime("%H:%M"),
                "room": room,
                "created_by": st.session_state.get("user_id", "operator"),
                "status": "active"
            }
            res = create_schedule(payload)
            if res and res.status_code == 200:
                st.success("Tạo lịch thành công!")
                st.rerun()

st.divider()

# =========================
# DANH SÁCH LỊCH HỌC & SỬA GỬI THÔNG BÁO
# =========================
st.subheader("📋 Danh sách lịch học")
if not schedules:
    st.info("Chưa có lịch học nào")
else:
    for item in schedules:
        with st.container(border=True):
            col1, col2, col3 = st.columns([3, 4, 2])
            with col1:
                st.markdown(f"### 🏫 {item.get('class_name', '')}")
                st.write(f"**Môn:** {item.get('subject', '')}")
                st.write(f"**Phòng:** {item.get('room', '')}")
            with col2:
                st.write(f"**Thứ:** {', '.join(item.get('days_of_week', []))}")
                st.write(f"**Khóa:** {item.get('study_date', '')}")
                st.write(f"**Giờ:** {item.get('start_time')} - {item.get('end_time')}")
            with col3:
                schedule_id = item.get("id", item.get("_id"))
                if st.button("✏️ Sửa & Gửi Thông báo", key=f"edit_{schedule_id}"):
                    st.session_state["editing_schedule"] = schedule_id
                if st.button("🗑️ Xóa", key=f"del_{schedule_id}"):
                    if delete_schedule(schedule_id).status_code == 200: st.rerun()

            # FORM SỬA VÀ TỰ ĐỘNG GỬI TIN
            if st.session_state.get("editing_schedule") == schedule_id:
                with st.form(f"edit_form_{schedule_id}"):
                    st.warning("💡 Lưu ý: Khi nhấn Lưu, hệ thống sẽ tự động nhắn tin cho Phụ huynh & Học sinh lớp này.")
                    c1, c2 = st.columns(2)
                    with c1:
                        new_days = st.multiselect("Thứ trong tuần", options=DAY_CHOICES, default=item.get("days_of_week", []))
                        new_room = st.text_input("Phòng học", value=item.get("room", "Online"))
                    with c2:
                        new_start_time = st.time_input("Giờ bắt đầu", value=datetime.strptime(item.get("start_time"), "%H:%M").time())
                        new_end_time = st.time_input("Giờ kết thúc", value=datetime.strptime(item.get("end_time"), "%H:%M").time())
                    
                    if st.form_submit_button("💾 Lưu & Gửi Thông Báo", type="primary"):
                        payload = item.copy()
                        payload.update({
                            "days_of_week": new_days,
                            "room": new_room,
                            "start_time": new_start_time.strftime("%H:%M"),
                            "end_time": new_end_time.strftime("%H:%M")
                        })
                        
                        res = update_schedule(schedule_id, payload)
                        if res and res.status_code == 200:
                            # --- GỬI THÔNG BÁO TỰ ĐỘNG ---
                            msg_title = f"🔔 Thay đổi lịch học lớp {item.get('class_name')}"
                            msg_content = (f"Thông báo: Lớp {item.get('class_name')} đã đổi sang lịch học mới: "
                                          f"{', '.join(new_days)} lúc {new_start_time.strftime('%H:%M')}. "
                                          f"Phòng học: {new_room}. Vui lòng kiểm tra lại thời khóa biểu.")
                            
                            send_auto_notification(item.get("class_id"), item.get("class_name"), msg_title, msg_content)
                            
                            st.success("Cập nhật và gửi tin nhắn thành công!")
                            st.session_state["editing_schedule"] = None
                            st.rerun()