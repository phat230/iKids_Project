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

st.title("📅 Xếp lịch học - Bộ phận vận hành")
st.write("Chọn lớp học đã được tạo để lên lịch giảng dạy cho giáo viên và học sinh.")

# =========================
# HÀM GỌI API
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

# Danh sách chọn Lớp
class_options = {f"{c.get('class_name', 'Không tên')} - {c.get('subject', '')}": c for c in classes}
# Danh sách các ngày trong tuần
DAY_CHOICES = ["Thứ 2", "Thứ 3", "Thứ 4", "Thứ 5", "Thứ 6", "Thứ 7", "Chủ nhật"]

# =========================
# FORM TẠO LỊCH
# =========================
st.subheader("➕ Tạo lịch học mới")

with st.form("create_schedule_form", clear_on_submit=True):
    col1, col2 = st.columns(2)

    with col1:
        if not class_options:
            st.warning("⚠️ Chưa có lớp học nào. Vui lòng qua trang Quản Lý Lớp Học để tạo lớp trước.")
            selected_class_label = None
        else:
            selected_class_label = st.selectbox("Chọn lớp học (*)", options=list(class_options.keys()))
            if selected_class_label:
                cls_data = class_options[selected_class_label]
                st.info(f"👨‍🏫 Giáo viên phụ trách: **{cls_data.get('teacher_name', 'Chưa xếp')}**")

        # THÊM MỚI: Chọn các ngày trong tuần
        selected_days = st.multiselect("Lịch học trong tuần (*)", options=DAY_CHOICES, default=["Thứ 7", "Chủ nhật"])
        room = st.text_input("Phòng học / Hình thức", value="Online")

    with col2:
        c_date1, c_date2 = st.columns(2)
        with c_date1:
            start_date = st.date_input("Ngày bắt đầu khóa học")
        with c_date2:
            end_date = st.date_input("Ngày kết thúc khóa học")
            
        c_time1, c_time2 = st.columns(2)
        with c_time1:
            start_time = st.time_input("Giờ bắt đầu")
        with c_time2:
            end_time = st.time_input("Giờ kết thúc")

    submitted = st.form_submit_button("✅ Tạo lịch học")

    if submitted:
        if not selected_class_label:
            st.warning("Vui lòng chọn lớp học")
        elif not selected_days:
            st.warning("Vui lòng chọn ít nhất 1 ngày học trong tuần (VD: Thứ 2, Thứ 4)")
        elif start_date > end_date:
            st.error("⚠️ Ngày kết thúc không thể nhỏ hơn ngày bắt đầu!")
        else:
            cls_data = class_options[selected_class_label]
            date_range_str = f"{start_date.strftime('%d/%m/%Y')} đến {end_date.strftime('%d/%m/%Y')}"

            payload = {
                "class_id": cls_data.get("id", ""),
                "class_name": cls_data.get("class_name", ""),
                "subject": cls_data.get("subject", ""),
                "teacher_id": cls_data.get("teacher_id", ""),
                "teacher_name": cls_data.get("teacher_name", ""),
                "study_date": date_range_str,
                "days_of_week": selected_days, # Lưu danh sách thứ trong tuần
                "start_time": start_time.strftime("%H:%M"),
                "end_time": end_time.strftime("%H:%M"),
                "room": room,
                "created_by": st.session_state.get("user_id", "operator"),
                "status": "active"
            }

            res = create_schedule(payload)

            if res and res.status_code == 200:
                st.success("Tạo lịch học thành công!")
                st.rerun()
            elif res:
                try:
                    st.error(res.json().get("detail", "Tạo lịch thất bại"))
                except:
                    st.error(res.text)

st.divider()

# =========================
# DANH SÁCH LỊCH HỌC
# =========================
st.subheader("📋 Danh sách lịch học")

if not schedules:
    st.info("Chưa có lịch học nào")
else:
    for item in schedules:
        with st.container(border=True):
            col1, col2, col3 = st.columns([3, 4, 2]) # Mở rộng cột giữa để dễ nhìn

            with col1:
                st.markdown(f"### 🏫 {item.get('class_name', '')}")
                st.write(f"**Môn:** {item.get('subject', '')}")
                st.write(f"**Giáo viên:** {item.get('teacher_name', '')}")
                st.write(f"**Phòng:** {item.get('room', '')}")

            with col2:
                study_date_str = item.get('study_date', '')
                start_time_str = item.get('start_time', '00:00')
                end_time_str = item.get('end_time', '23:59')
                days_list = item.get('days_of_week', [])
                days_str = ", ".join(days_list) if days_list else "Chưa xác định"
                
                st.write(f"**Lịch trong tuần:** {days_str}")
                st.write(f"**Khóa học:** {study_date_str}")
                st.write(f"**Khung giờ:** {start_time_str} - {end_time_str}")
                
                # --- LOGIC XỬ LÝ 3 TRẠNG THÁI (THÔNG MINH HƠN) ---
                try:
                    now = datetime.now()
                    current_date = now.date()
                    current_time = now.time()
                    
                    # Ánh xạ weekday() của Python (0=Thứ 2, 6=CN) sang tên tiếng Việt
                    day_map = {0: "Thứ 2", 1: "Thứ 3", 2: "Thứ 4", 3: "Thứ 5", 4: "Thứ 6", 5: "Thứ 7", 6: "Chủ nhật"}
                    current_weekday = day_map[now.weekday()]
                    
                    # Tách ngày bắt đầu và kết thúc
                    if "đến" in study_date_str:
                        parts = study_date_str.split("đến")
                        start_date_obj = datetime.strptime(parts[0].strip(), "%d/%m/%Y").date()
                        end_date_obj = datetime.strptime(parts[1].strip(), "%d/%m/%Y").date()
                    elif "/" in study_date_str:
                        start_date_obj = datetime.strptime(study_date_str.strip(), "%d/%m/%Y").date()
                        end_date_obj = start_date_obj
                    else:
                        start_date_obj = datetime.strptime(study_date_str.strip(), "%Y-%m-%d").date()
                        end_date_obj = start_date_obj

                    start_time_obj = datetime.strptime(start_time_str, "%H:%M").time()
                    end_time_obj = datetime.strptime(end_time_str, "%H:%M").time()

                    # Logic kiểm tra trạng thái
                    if current_date > end_date_obj or (current_date == end_date_obj and current_time > end_time_obj):
                        display_status = "Kết thúc lớp học"
                        status_color = "gray"
                    # Kiểm tra xem hôm nay có nằm trong khóa học + đúng Thứ + đúng Giờ không
                    elif (start_date_obj <= current_date <= end_date_obj) and (current_weekday in days_list) and (start_time_obj <= current_time <= end_time_obj):
                        display_status = "Đang trong giờ dạy"
                        status_color = "green"
                    else:
                        display_status = "Lớp học hiện không hoạt động"
                        status_color = "orange"
                        
                except Exception:
                    display_status = "Lớp học hiện không hoạt động"
                    status_color = "orange"

                # Trạng thái trong DB
                db_status = item.get('status', 'active')
                if db_status != "active":
                    display_status = db_status
                    status_color = "red"
                
                st.markdown(f"**Trạng thái:** :{status_color}[{display_status}]")

            with col3:
                schedule_id = item.get("id", item.get("_id"))

                if st.button("✏️ Sửa thời gian", key=f"edit_{schedule_id}"):
                    st.session_state["editing_schedule"] = schedule_id

                if st.button("🗑️ Xóa lịch", key=f"delete_{schedule_id}"):
                    res = delete_schedule(schedule_id)
                    if res and res.status_code == 200:
                        st.success("Đã xóa lịch học")
                        st.rerun()
                    elif res:
                        st.error(res.text)

            # =========================
            # FORM SỬA LỊCH
            # =========================
            if st.session_state.get("editing_schedule") == schedule_id:
                st.warning("Đang cập nhật lịch học")

                with st.form(f"edit_form_{schedule_id}"):
                    st.text_input("Tên lớp (Cố định)", value=item.get("class_name", ""), disabled=True)
                    
                    c1, c2 = st.columns(2)
                    with c1:
                        new_days = st.multiselect("Lịch học trong tuần", options=DAY_CHOICES, default=item.get("days_of_week", []))
                        new_room = st.text_input("Phòng học", value=item.get("room", "Online"))

                    with c2:
                        old_study_str = item.get("study_date", "")
                        try:
                            if "đến" in old_study_str:
                                parts = old_study_str.split("đến")
                                old_start_date = datetime.strptime(parts[0].strip(), "%d/%m/%Y").date()
                                old_end_date = datetime.strptime(parts[1].strip(), "%d/%m/%Y").date()
                            else:
                                old_start_date = datetime.strptime(old_study_str, "%Y-%m-%d").date()
                                old_end_date = old_start_date
                        except:
                            old_start_date = date.today()
                            old_end_date = date.today()

                        ce1, ce2 = st.columns(2)
                        with ce1:
                            new_start_date = st.date_input("Ngày bắt đầu", value=old_start_date)
                        with ce2:
                            new_end_date = st.date_input("Ngày kết thúc", value=old_end_date)

                        old_start = datetime.strptime(item.get("start_time", "18:00"), "%H:%M").time()
                        old_end = datetime.strptime(item.get("end_time", "20:00"), "%H:%M").time()
                        
                        ct1, ct2 = st.columns(2)
                        with ct1:
                            new_start_time = st.time_input("Giờ bắt đầu", value=old_start)
                        with ct2:
                            new_end_time = st.time_input("Giờ kết thúc", value=old_end)

                    col_save, col_cancel = st.columns(2)

                    with col_save:
                        save_btn = st.form_submit_button("💾 Lưu thay đổi")

                    with col_cancel:
                        cancel_btn = st.form_submit_button("❌ Hủy")

                    if save_btn:
                        if new_start_date > new_end_date:
                            st.error("⚠️ Ngày kết thúc không thể nhỏ hơn ngày bắt đầu!")
                        elif not new_days:
                            st.warning("Vui lòng chọn ít nhất 1 ngày học trong tuần")
                        else:
                            new_date_range_str = f"{new_start_date.strftime('%d/%m/%Y')} đến {new_end_date.strftime('%d/%m/%Y')}"
                            payload = {
                                "class_id": item.get("class_id", ""),
                                "class_name": item.get("class_name", ""),
                                "subject": item.get("subject", ""),
                                "teacher_id": item.get("teacher_id", ""),
                                "teacher_name": item.get("teacher_name", ""),
                                "room": new_room,
                                "study_date": new_date_range_str,
                                "days_of_week": new_days,
                                "start_time": new_start_time.strftime("%H:%M"),
                                "end_time": new_end_time.strftime("%H:%M"),
                                "status": item.get("status", "active")
                            }

                            res = update_schedule(schedule_id, payload)

                            if res and res.status_code == 200:
                                st.success("Đã cập nhật lịch học")
                                st.session_state["editing_schedule"] = None
                                st.rerun()
                            elif res:
                                st.error(res.text)

                    if cancel_btn:
                        st.session_state["editing_schedule"] = None
                        st.rerun()