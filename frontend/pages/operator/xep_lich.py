import streamlit as st
import requests
from datetime import datetime

API = "http://127.0.0.1:8000"

# Nếu backend include router tv1 là /api/tv1 thì giữ dòng này
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

# =========================
# HÀM GỌI API
# =========================
def get_teachers():
    try:
        res = requests.get(f"{TV1_API}/teachers", timeout=10)
        if res.status_code == 200:
            return res.json()
        return []
    except Exception as e:
        st.error(f"Lỗi lấy danh sách giáo viên: {e}")
        return []


def get_schedules():
    try:
        res = requests.get(
            f"{TV1_API}/schedule/list",
            headers=headers,
            timeout=10
        )
        if res.status_code == 200:
            return res.json()
        st.error(res.text)
        return []
    except Exception as e:
        st.error(f"Lỗi lấy lịch học: {e}")
        return []


def create_schedule(data):
    try:
        res = requests.post(
            f"{TV1_API}/schedule/create",
            json=data,
            headers=headers,
            timeout=10
        )
        return res
    except Exception as e:
        st.error(f"Lỗi tạo lịch: {e}")
        return None


def update_schedule(schedule_id, data):
    try:
        res = requests.put(
            f"{TV1_API}/schedule/{schedule_id}",
            json=data,
            headers=headers,
            timeout=10
        )
        return res
    except Exception as e:
        st.error(f"Lỗi cập nhật lịch: {e}")
        return None


def delete_schedule(schedule_id):
    try:
        res = requests.delete(
            f"{TV1_API}/schedule/{schedule_id}",
            headers=headers,
            timeout=10
        )
        return res
    except Exception as e:
        st.error(f"Lỗi xóa lịch: {e}")
        return None


# =========================
# LOAD DATA
# =========================
teachers = get_teachers()
schedules = get_schedules()

teacher_options = {
    f"{t.get('name', 'Không tên')} - {t.get('email', '')}": t
    for t in teachers
}

# =========================
# FORM TẠO LỊCH
# =========================
st.subheader("➕ Tạo lịch học mới")

with st.form("create_schedule_form", clear_on_submit=True):
    col1, col2 = st.columns(2)

    with col1:
        class_name = st.text_input("Tên lớp", placeholder="Ví dụ: Lớp Toán 3A")
        subject = st.text_input("Môn học", placeholder="Ví dụ: Toán tư duy")

        teacher_label = st.selectbox(
            "Chọn giáo viên",
            options=list(teacher_options.keys()) if teacher_options else []
        )

        room = st.text_input("Phòng học / Hình thức", value="Online")

    with col2:
        study_date = st.date_input("Ngày học")
        start_time = st.time_input("Giờ bắt đầu")
        end_time = st.time_input("Giờ kết thúc")

    submitted = st.form_submit_button("✅ Tạo lịch học")

    if submitted:
        if not class_name or not subject or not teacher_options:
            st.warning("Vui lòng nhập đầy đủ thông tin")
        else:
            teacher = teacher_options[teacher_label]

            payload = {
                "class_name": class_name,
                "subject": subject,
                "teacher_id": teacher["id"],
                "teacher_name": teacher["name"],
                "study_date": study_date.strftime("%Y-%m-%d"),
                "start_time": start_time.strftime("%H:%M"),
                "end_time": end_time.strftime("%H:%M"),
                "room": room,
                "created_by": st.session_state.get("user_id", "operator"),
                "status": "active"
            }

            res = create_schedule(payload)

            if res and res.status_code == 200:
                st.success("Tạo lịch học thành công")
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
            col1, col2, col3 = st.columns([3, 3, 2])

            with col1:
                st.markdown(f"### 🏫 {item.get('class_name', '')}")
                st.write(f"**Môn:** {item.get('subject', '')}")
                st.write(f"**Giáo viên:** {item.get('teacher_name', '')}")

            with col2:
                st.write(f"**Ngày học:** {item.get('study_date', '')}")
                st.write(
                    f"**Thời gian:** {item.get('start_time', '')} - {item.get('end_time', '')}"
                )
                st.write(f"**Phòng:** {item.get('room', '')}")
                st.write(f"**Trạng thái:** {item.get('status', '')}")

            with col3:
                schedule_id = item.get("id")

                if st.button("✏️ Sửa", key=f"edit_{schedule_id}"):
                    st.session_state["editing_schedule"] = schedule_id

                if st.button("🗑️ Xóa", key=f"delete_{schedule_id}"):
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
                st.warning("Đang sửa lịch học")

                with st.form(f"edit_form_{schedule_id}"):
                    c1, c2 = st.columns(2)

                    with c1:
                        new_class_name = st.text_input(
                            "Tên lớp",
                            value=item.get("class_name", "")
                        )

                        new_subject = st.text_input(
                            "Môn học",
                            value=item.get("subject", "")
                        )

                        new_room = st.text_input(
                            "Phòng học",
                            value=item.get("room", "Online")
                        )

                    with c2:
                        old_date = datetime.strptime(
                            item.get("study_date", datetime.now().strftime("%Y-%m-%d")),
                            "%Y-%m-%d"
                        ).date()

                        new_date = st.date_input(
                            "Ngày học",
                            value=old_date
                        )

                        old_start = datetime.strptime(
                            item.get("start_time", "18:00"),
                            "%H:%M"
                        ).time()

                        old_end = datetime.strptime(
                            item.get("end_time", "20:00"),
                            "%H:%M"
                        ).time()

                        new_start_time = st.time_input(
                            "Giờ bắt đầu",
                            value=old_start
                        )

                        new_end_time = st.time_input(
                            "Giờ kết thúc",
                            value=old_end
                        )

                    col_save, col_cancel = st.columns(2)

                    with col_save:
                        save_btn = st.form_submit_button("💾 Lưu thay đổi")

                    with col_cancel:
                        cancel_btn = st.form_submit_button("❌ Hủy")

                    if save_btn:
                        payload = {
                            "class_name": new_class_name,
                            "subject": new_subject,
                            "room": new_room,
                            "study_date": new_date.strftime("%Y-%m-%d"),
                            "start_time": new_start_time.strftime("%H:%M"),
                            "end_time": new_end_time.strftime("%H:%M"),
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