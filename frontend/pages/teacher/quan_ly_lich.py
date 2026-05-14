import streamlit as st
import requests
import os
from datetime import datetime, timedelta, date

# Tạm thời import bảo vệ role
try:
    from utils.role_guard import require_role
    require_role(["teacher", "admin"])
except ImportError:
    pass

# ================= HÀM ĐỌC FILE CSS (SỬA LỖI ĐƯỜNG DẪN) =================
def load_css(file_name):
    """Tự động tìm file CSS trong thư mục frontend/CSS/"""
    # Lấy đường dẫn tuyệt đối đến thư mục chứa file hiện tại
    current_dir = os.path.dirname(os.path.abspath(__file__)) # pages/teacher
    
    # Tìm đường dẫn đến thư mục CSS (lùi 2 cấp rồi vào CSS/)
    css_root = os.path.abspath(os.path.join(current_dir, "../../CSS"))
    full_path = os.path.join(css_root, file_name)

    if os.path.exists(full_path):
        with open(full_path, "r", encoding="utf-8") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    else:
        st.warning(f"⚠️ Không tìm thấy file CSS tại: {full_path}")

# ================= CẤU HÌNH HỆ THỐNG & NGÀY LỄ =================
API_URL = "http://127.0.0.1:8000"

HOLIDAYS = {
    "01/01": "Tết Dương Lịch", "30/04": "Giải Phóng MN", "01/05": "Quốc Tế Lao Động",
    "01/06": "Quốc Tế Thiếu Nhi", "02/09": "Quốc Khánh", "20/11": "Ngày Nhà Giáo VN"
}

# ================= CÁC HÀM HỖ TRỢ XỬ LÝ LỊCH =================
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
    except: return date.min, date.max

def get_shift_id(time_str):
    try:
        h = int(time_str.split(":")[0])
        if h < 9: return 1
        elif h < 12: return 2
        elif h < 15: return 3
        elif h < 17: return 4
        return 5
    except: return 5

@st.cache_data(ttl=30)
def fetch_teacher_schedules(teacher_id):
    headers = {"Authorization": f"Bearer {st.session_state.get('token', '')}"}
    try:
        res = requests.get(f"{API_URL}/schedule/list", headers=headers, timeout=10)
        if res.status_code == 200:
            all_s = res.json()
            return [s for s in all_s if s.get("teacher_id") == teacher_id and s.get("status") == "active"]
        return []
    except: return []

# ================= GIAO DIỆN CHÍNH =================
def render_teacher_dashboard():
    # Tải CSS làm đẹp (Chỉ truyền phần sau thư mục CSS/)
    load_css("teacher/quan_ly_lich.css")

    st.title("📅 Lịch Giảng Dạy & Gửi Yêu Cầu")

    teacher_id = st.session_state.get("user_id", "gv_demo_id")
    teacher_name = st.session_state.get("user_info", {}).get("name", "Giáo viên")

    if 'current_date' not in st.session_state:
        st.session_state.current_date = datetime.now()

    # --- 1. ĐIỀU HƯỚNG THỜI GIAN ---
    col_nav, col_title, col_empty = st.columns([1, 2, 1])
    with col_nav:
        c1, c2, c3 = st.columns([1.5, 1, 1])
        if c1.button("Hôm nay", use_container_width=True): st.session_state.current_date = datetime.now()
        if c2.button("◀", use_container_width=True): st.session_state.current_date -= timedelta(days=7)
        if c3.button("▶", use_container_width=True): st.session_state.current_date += timedelta(days=7)
            
    with col_title:
        m_names = ["", "Tháng 1", "Tháng 2", "Tháng 3", "Tháng 4", "Tháng 5", "Tháng 6", 
                   "Tháng 7", "Tháng 8", "Tháng 9", "Tháng 10", "Tháng 11", "Tháng 12"]
        curr_m = m_names[st.session_state.current_date.month]
        st.markdown(f"<h3 style='text-align: center; margin: 0;'>{curr_m} - {st.session_state.current_date.year}</h3>", unsafe_allow_html=True)

    # --- 2. XỬ LÝ DỮ LIỆU ĐỔ VÀO BẢNG ---
    start_of_week = get_start_of_week(st.session_state.current_date)
    start_of_week_date = start_of_week.date()
    
    week_dates = []
    for i in range(7):
        curr_day = start_of_week + timedelta(days=i)
        d_str = curr_day.strftime("%d/%m")
        week_dates.append({
            "name": f"Thứ {i+2}" if i < 6 else "Chủ Nhật",
            "date": d_str,
            "is_holiday": d_str in HOLIDAYS,
            "holiday_name": HOLIDAYS.get(d_str, "")
        })

    raw_schedules = fetch_teacher_schedules(teacher_id)
    schedule_data = []
    active_classes = []
    class_map = {} 
    day_map = {0: "Thứ 2", 1: "Thứ 3", 2: "Thứ 4", 3: "Thứ 5", 4: "Thứ 6", 5: "Thứ 7", 6: "Chủ nhật"}

    for s in raw_schedules:
        s_start, s_end = parse_date_range(s.get("study_date", ""))
        s_days = s.get("days_of_week", [])
        label = f"{s.get('class_name')} - {s.get('subject')} | Khóa: {s.get('study_date')}"
        
        if label not in active_classes:
            active_classes.append(label)
            class_map[label] = {"class_id": s.get("class_id", s.get("id", "")), "class_name": s.get("class_name", "")}

        for i in range(7):
            check_d = start_of_week_date + timedelta(days=i)
            if s_start <= check_d <= s_end and day_map[i] in s_days:
                schedule_data.append({
                    "day_offset": i, "shift": get_shift_id(s.get("start_time", "00:00")),
                    "subject": s.get("subject", "N/A"), "class_name": s.get("class_name", ""),
                    "room": s.get("room", "Online"), "time_str": f"{s.get('start_time')} - {s.get('end_time')}"
                })

    # Dữ liệu demo nếu trống
    if not schedule_data:
        schedule_data = [{"day_offset": 0, "shift": 1, "subject": "Demo", "class_name": "Lớp 1", "room": "A1", "time_str": "07:30-09:30"}]

    # --- 3. VẼ BẢNG LỊCH (Sử dụng class từ file CSS tách riêng) ---
    html_table = '<table class="custom-calendar"><thead><tr><th>Buổi</th><th>Thời gian</th>'
    for day in week_dates:
        if day["is_holiday"]:
            html_table += f"<th class='holiday-header'>{day['name']}<br><small>({day['date']})</small><span class='holiday-text'>{day['holiday_name']}</span></th>"
        else:
            html_table += f"<th>{day['name']}<br><small>({day['date']})</small></th>"
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
                            <div class="class-room">🏫 {item['room']} <br> 🕒 {item['time_str']}</div>
                        </div>"""
                cells += f"<td>{content}</td>"
        return cells

    # Render các hàng (Ca học)
    rows = [("SÁNG", 1, "07:30 - 09:30"), ("SÁNG", 2, "09:45 - 11:45"), 
            ("CHIỀU", 3, "13:30 - 15:30"), ("CHIỀU", 4, "15:45 - 17:45"), 
            ("TỐI", 5, "18:30 - 20:30")]
    
    for label, sid, t_range in rows:
        session_td = ""
        if sid in [1, 3]: session_td = f'<td rowspan="2" class="session-col">{label}</td>'
        elif sid == 5: session_td = '<td class="session-col" style="writing-mode:horizontal-tb;transform:none;letter-spacing:0;width:auto;">TỐI</td>'
        html_table += f'<tr>{session_td}<td class="time-col">Ca {sid}<br><small>{t_range}</small></td>{generate_cells(sid)}</tr>'

    st.markdown(html_table + "</tbody></table>", unsafe_allow_html=True)
    st.divider()

    # --- 4. TƯƠNG TÁC GỬI ĐƠN HỖ TRỢ ---
    st.markdown("### 🛠️ Gửi Đơn Xin Hỗ Trợ (Vận Hành)")
    sel_label = st.selectbox("📌 Bước 1: Chọn Lớp/Ca dạy đang gặp vấn đề", ["-- Vui lòng chọn --"] + active_classes)
    
    col_info, col_form = st.columns([1, 1.8])
    with col_info:
        if sel_label != "-- Vui lòng chọn --":
            info = class_map[sel_label]
            st.success(f"**Thông tin Lớp:**\n\n🏫 {info['class_name']}\n\n📚 {sel_label.split('|')[0]}")
    
    with col_form:
        req_type = st.radio("Loại đơn", ["🛑 Xin nghỉ dạy", "🔄 Xin đổi ngày/ca", "🏫 Xin đổi phòng", "💻 Đổi PT dạy"], horizontal=True)
        r_date = st.date_input("Ngày áp dụng thay đổi")
        reason = st.text_area("Lý do cụ thể (Bắt buộc)", placeholder="Nhập lý do...")
        
        if st.button("🚀 Gửi Đơn Hỗ Trợ", type="primary", use_container_width=True):
            if sel_label == "-- Vui lòng chọn --" or not reason.strip():
                st.error("⚠️ Vui lòng điền đầy đủ thông tin!")
            else:
                payload = {
                    "teacher_id": teacher_id, "teacher_name": teacher_name,
                    "class_id": class_map[sel_label]['class_id'], "class_name": class_map[sel_label]['class_name'],
                    "type": req_type[2:].strip(), "reason": reason, "date": str(r_date), "status": "pending"
                }
                try:
                    res = requests.post(f"{API_URL}/submit-request", json=payload)
                    if res.status_code == 200:
                        st.success("✅ Gửi đơn thành công!"); st.balloons()
                except: st.error("❌ Không thể kết nối đến Backend.")

if __name__ == "__main__":
    render_teacher_dashboard()