import streamlit as st
import requests
import os
from datetime import datetime, timedelta, date

# Import bảo vệ role
try:
    from utils.role_guard import require_role
    require_role(["teacher", "admin"])
except ImportError:
    pass

# ================= CẤU HÌNH HỆ THỐNG & NGÀY LỄ =================
API_URL = "http://localhost:8000"

HOLIDAYS = {
    "01/01": "Tết Dương Lịch",
    "30/04": "Giải Phóng Miền Nam",
    "01/05": "Quốc Tế Lao Động",
    "01/06": "Quốc Tế Thiếu Nhi",
    "02/09": "Quốc Khánh",
    "20/11": "Ngày Nhà Giáo VN"
}

# ================= HÀM HỖ TRỢ (LOAD CSS & LOGIC) =================
def load_css(file_name):
    """Tự động tìm file CSS trong thư mục frontend/CSS/"""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    css_root = os.path.abspath(os.path.join(current_dir, "../../CSS"))
    full_path = os.path.join(css_root, file_name)

    if os.path.exists(full_path):
        with open(full_path, "r", encoding="utf-8") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    else:
        st.warning(f"⚠️ Không tìm thấy file CSS tại: {full_path}")

def get_start_of_week(dt):
    return dt - timedelta(days=dt.weekday())

def parse_date_range(date_str):
    try:
        if "đến" in date_str:
            parts = date_str.split("đến")
            start = datetime.strptime(parts[0].strip(), "%d/%m/%Y").date()
            end = datetime.strptime(parts[1].strip(), "%d/%m/%Y").date()
            return start, end
        d = datetime.strptime(date_str.strip(), "%d/%m/%Y" if "/" in date_str else "%Y-%m-%d").date()
        return d, d
    except:
        return date.min, date.max

def get_shift_id(time_str):
    try:
        h = int(time_str.split(":")[0])
        if h < 9: return 1
        elif h < 12: return 2
        elif h < 15: return 3
        elif h < 17: return 4
        else: return 5
    except:
        return 5

@st.cache_data(ttl=30)
def fetch_teacher_schedules(teacher_id):
    headers = {"Authorization": f"Bearer {st.session_state.get('token', '')}"}
    try:
        res = requests.get(f"{API_URL}/schedule/list", headers=headers, timeout=10)
        if res.status_code == 200:
            all_schedules = res.json()
            return [s for s in all_schedules if s.get("teacher_id") == teacher_id and s.get("status") == "active"]
        return []
    except:
        return []

# ================= GIAO DIỆN CHÍNH =================
def render_teacher_dashboard():
    # Tải CSS tách riêng
    load_css("teacher/dashboard.css")

    st.title(" Lịch Dạy Tuần")

    # Thông tin đăng nhập
    teacher_id = st.session_state.get("user_id", "demo_id")
    teacher_name = st.session_state.get("user_info", {}).get("name", "Giáo viên")

    # 1. Quản lý điều hướng ngày tháng
    if 'current_date' not in st.session_state:
        st.session_state.current_date = datetime.now()

    col_nav, col_title, col_view = st.columns([1, 2, 1])
    with col_nav:
        c1, c2, c3 = st.columns([1.5, 1, 1])
        if c1.button("Hôm nay", use_container_width=True): st.session_state.current_date = datetime.now()
        if c2.button("◀", use_container_width=True): st.session_state.current_date -= timedelta(days=7)
        if c3.button("▶", use_container_width=True): st.session_state.current_date += timedelta(days=7)
            
    with col_title:
        m_names = ["", "Tháng 1", "Tháng 2", "Tháng 3", "Tháng 4", "Tháng 5", "Tháng 6", 
                   "Tháng 7", "Tháng 8", "Tháng 9", "Tháng 10", "Tháng 11", "Tháng 12"]
        curr_month = m_names[st.session_state.current_date.month]
        st.markdown(f"<h3 style='text-align: center; margin: 0;'>{curr_month} - {st.session_state.current_date.year}</h3>", unsafe_allow_html=True)

    # 2. Xử lý lịch tuần
    start_of_week = get_start_of_week(st.session_state.current_date)
    start_of_week_date = start_of_week.date()
    week_dates = []
    for i in range(7):
        current_day = start_of_week + timedelta(days=i)
        d_str = current_day.strftime("%d/%m")
        week_dates.append({
            "name": f"Thứ {i+2}" if i < 6 else "Chủ Nhật",
            "date": d_str,
            "is_holiday": d_str in HOLIDAYS,
            "holiday_name": HOLIDAYS.get(d_str, "")
        })

    # Lấy dữ liệu thật
    raw_schedules = fetch_teacher_schedules(teacher_id)
    schedule_data = []
    active_classes = []
    class_map_for_form = {}
    day_map = {0: "Thứ 2", 1: "Thứ 3", 2: "Thứ 4", 3: "Thứ 5", 4: "Thứ 6", 5: "Thứ 7", 6: "Chủ nhật"}

    for s in raw_schedules:
        s_start, s_end = parse_date_range(s.get("study_date", ""))
        label = f"{s.get('class_name')} - {s.get('subject')} | Khóa: {s.get('study_date')}"
        if label not in active_classes:
            active_classes.append(label)
            class_map_for_form[label] = {"class_id": s.get("class_id", s.get("id", "")), "class_name": s.get("class_name", "")}

        for i in range(7):
            check_date = start_of_week_date + timedelta(days=i)
            if s_start <= check_date <= s_end and day_map[i] in s.get("days_of_week", []):
                schedule_data.append({
                    "day_offset": i, 
                    "shift": get_shift_id(s.get("start_time", "00:00")),
                    "subject": s.get("subject", "N/A"), 
                    "class_name": s.get("class_name", ""),
                    "room": s.get("room", "Online"),
                    "teacher": s.get("teacher_name", teacher_name),
                    "time_str": f"{s.get('start_time')} - {s.get('end_time')}"
                })

    # 3. Vẽ bảng lịch bằng HTML sử dụng Class từ file Dashboard.css
    html_table = '<table class="custom-calendar"><thead><tr><th>Buổi</th><th>Thời gian</th>'
    for day in week_dates:
        h_class = " class='holiday-header'" if day["is_holiday"] else ""
        h_text = f"<span class='holiday-text'>{day['holiday_name']}</span>" if day["is_holiday"] else ""
        html_table += f"<th{h_class}>{day['name']}<br><small>({day['date']})</small>{h_text}</th>"
    html_table += "</tr></thead><tbody>"

    def generate_cells(shift_id):
        cells = ""
        for idx, day in enumerate(week_dates):
            if day["is_holiday"]:
                cells += "<td class='holiday-cell'>Nghỉ Lễ</td>"
            else:
                content = ""
                for item in schedule_data:
                    if item['day_offset'] == idx and item['shift'] == shift_id:
                        content += f"""<div class="class-cell">
                            <div class="class-subject">{item['subject']}</div>
                            <div class="class-name">{item['class_name']}</div>
                            <div class="class-room">🏫 {item['room']}</div>
                            <div class="class-teacher">👤 {item['teacher']}</div>
                        </div>"""
                cells += f"<td>{content}</td>"
        return cells

    # Hàng cho các Ca (Shift)
    shifts = [("SÁNG", 1, "07:30 - 09:30"), ("SÁNG", 2, "09:45 - 11:45"), 
              ("CHIỀU", 3, "13:30 - 15:30"), ("CHIỀU", 4, "15:45 - 17:45"), 
              ("TỐI", 5, "18:30 - 20:30")]
    
    for label, sid, t_range in shifts:
        session_td = ""
        if sid in [1, 3]: session_td = f'<td rowspan="2" class="session-col">{label}</td>'
        elif sid == 5: session_td = '<td class="session-col" style="writing-mode:horizontal-tb;transform:none;letter-spacing:0;width:auto;">TỐI</td>'
        html_table += f'<tr>{session_td}<td class="time-col">Ca {sid}<br><small>{t_range}</small></td>{generate_cells(sid)}</tr>'

    st.markdown(html_table + "</tbody></table>", unsafe_allow_html=True)
    st.divider()

    # 4. Gửi đơn hỗ trợ
    st.markdown("### Yêu cầu xét duyệt xin hỗ trợ")
    if not active_classes:
        st.info("Hiện tại chưa có lịch dạy nào.")
    else:
        selected_class_label = st.selectbox("📌 Bước 1: Chọn Lớp/Ca dạy đang gặp vấn đề", ["-- Vui lòng chọn --"] + active_classes)
        if selected_class_label != "-- Vui lòng chọn --":
            col_info, col_form = st.columns([1, 1.8])
            with col_info:
                selected_class_info = class_map_for_form[selected_class_label]
                st.success(f"**Thông tin Lớp:**\n\n🏫 {selected_class_info['class_name']}\n\n {selected_class_label.split('|')[0]}")
            with col_form:
                req_type = st.radio("Loại đơn", [" Xin Nghỉ Dạy", " Xin Đổi Ca", " Xin Đổi Phòng"], horizontal=True)
                request_date = st.date_input("Ngày áp dụng thay đổi", value=date.today())
                reason = st.text_area("Lý do cụ thể (Bắt buộc)", placeholder="Nhập lý do...")
                
                if st.button("Gửi Đơn Xét Duyệt", type="primary", use_container_width=True):
                    if not reason.strip():
                        st.error("⚠️ Vui lòng nhập lý do!")
                    else:
                        payload = {
                            "teacher_id": teacher_id, "teacher_name": teacher_name,
                            "class_id": selected_class_info['class_id'], "class_name": selected_class_info['class_name'],
                            "type": req_type[2:].strip(), "reason": reason, "date": str(request_date), "status": "pending"
                        }
                        try:
                            res = requests.post(f"{API_URL}/submit-request", json=payload)
                            if res.status_code == 200:
                                st.success("✅ Gửi đơn thành công!"); st.balloons()
                            else:
                                st.error("❌ Lỗi gửi đơn.")
                        except:
                            st.error("❌ Không thể kết nối Backend.")

if __name__ == "__main__":
    render_teacher_dashboard()