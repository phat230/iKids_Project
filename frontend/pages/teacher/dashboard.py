import streamlit as st
import requests
<<<<<<< HEAD
from datetime import datetime, timedelta

# ================= CẤU HÌNH NGÀY LỄ (VIỆT NAM) =================
HOLIDAYS = {
    "01/01": "Tết Dương Lịch",
    "30/04": "Giải Phóng Miền Nam",
    "01/05": "Quốc Tế Lao Động",
    "01/06": "Quốc Tế Thiếu Nhi",
    "02/09": "Quốc Khánh",
    "20/11": "Ngày Nhà Giáo VN"
}

def get_start_of_week(date):
    return date - timedelta(days=date.weekday())

def render_teacher_dashboard():
    st.set_page_config(layout="wide")
    st.title("📅 Bảng Tin Giáo Viên (Lịch Dạy)")

=======
from datetime import datetime, timedelta, date
from utils.role_guard import require_role

# Bảo vệ trang, chỉ giáo viên được phép truy cập
require_role(["teacher", "admin"])

API_URL = "http://localhost:8000"

def get_start_of_week(dt):
    """Tính ngày Thứ 2 của tuần chứa ngày hiện tại"""
    return dt - timedelta(days=dt.weekday())

def parse_date_range(date_str):
    """Hàm hỗ trợ bóc tách ngày bắt đầu và kết thúc từ chuỗi"""
    try:
        if "đến" in date_str:
            parts = date_str.split("đến")
            start = datetime.strptime(parts[0].strip(), "%d/%m/%Y").date()
            end = datetime.strptime(parts[1].strip(), "%d/%m/%Y").date()
            return start, end
        elif "/" in date_str:
            d = datetime.strptime(date_str.strip(), "%d/%m/%Y").date()
            return d, d
        else:
            d = datetime.strptime(date_str.strip(), "%Y-%m-%d").date()
            return d, d
    except:
        return date.min, date.max

def get_shift_id(time_str):
    """Phân loại ca học dựa trên giờ bắt đầu để xếp vào bảng"""
    try:
        h = int(time_str.split(":")[0])
        if h < 9: return 1   # Sáng sớm
        elif h < 12: return 2 # Gần trưa
        elif h < 15: return 3 # Đầu chiều
        elif h < 17: return 4 # Chiều tối
        else: return 5        # Tối (sau 17h)
    except:
        return 5

# --- LẤY LỊCH DẠY TỪ MONGODB ---
@st.cache_data(ttl=30)
def fetch_teacher_schedules(teacher_id):
    headers = {"Authorization": f"Bearer {st.session_state.get('token', '')}"}
    try:
        res = requests.get(f"{API_URL}/schedule/list", headers=headers, timeout=10)
        if res.status_code == 200:
            all_schedules = res.json()
            # Chỉ lấy các lịch dạy thuộc về giáo viên này và đang "active"
            return [s for s in all_schedules if s.get("teacher_id") == teacher_id and s.get("status") == "active"]
        return []
    except:
        return []

def render_teacher_dashboard():
    st.set_page_config(page_title="Bảng Tin Giáo Viên", page_icon="👨‍🏫", layout="wide") 
    st.title("📅 Bảng Tin Giáo Viên (Lịch Dạy)")

    # Lấy thông tin user đăng nhập
    teacher_id = st.session_state.get("user_id")
    teacher_name = st.session_state.get("user_info", {}).get("name", "Giáo viên")

    # --- 1. QUẢN LÝ TRẠNG THÁI NGÀY THÁNG ---
>>>>>>> b867fa3eeaab06e3a13728884e413c388f05024f
    if 'current_date' not in st.session_state:
        st.session_state.current_date = datetime.now()

    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col1:
        c1, c2, c3 = st.columns([1.5, 1, 1])
        if c1.button("Hôm nay", use_container_width=True):
            st.session_state.current_date = datetime.now()
        if c2.button("◀", use_container_width=True):
            st.session_state.current_date -= timedelta(days=7)
        if c3.button("▶", use_container_width=True):
            st.session_state.current_date += timedelta(days=7)
            
    with col2:
        month_names = ["", "Tháng 1", "Tháng 2", "Tháng 3", "Tháng 4", "Tháng 5", "Tháng 6", 
                       "Tháng 7", "Tháng 8", "Tháng 9", "Tháng 10", "Tháng 11", "Tháng 12"]
        current_month = month_names[st.session_state.current_date.month]
        current_year = st.session_state.current_date.year
        st.markdown(f"<h3 style='text-align: center; margin: 0; padding-top: 5px;'>{current_month} - {current_year}</h3>", unsafe_allow_html=True)

<<<<<<< HEAD
    st.markdown("<br>", unsafe_allow_html=True)

    start_of_week = get_start_of_week(st.session_state.current_date)
    week_dates = []
    for i in range(7):
        current_day = start_of_week + timedelta(days=i)
        date_str = current_day.strftime("%d/%m")
        week_dates.append({
            "name": f"Thứ {i+2}" if i < 6 else "Chủ Nhật",
            "date": date_str,
            "is_holiday": date_str in HOLIDAYS,
            "holiday_name": HOLIDAYS.get(date_str, "")
        })

    schedule_data = [
        {"day_offset": 0, "shift": 1, "subject": "Toán Cao Cấp", "room": "Phòng A.201", "teachers": "Minh Tran"},
        {"day_offset": 1, "shift": 2, "subject": "Dữ liệu AI", "room": "P.Máy M.101", "teachers": "Minh Tran vs Duc Phat"},
        {"day_offset": 3, "shift": 3, "subject": "Lập trình Scratch", "room": "Phòng Lab 2", "teachers": "Minh Tran"},
        {"day_offset": 4, "shift": 4, "subject": "Tiếng Anh Giao Tiếp", "room": "Phòng 105", "teachers": "Minh Tran"},
        {"day_offset": 4, "shift": 5, "subject": "Kỹ năng mềm", "room": "Phòng D1", "teachers": "Minh Tran"}
    ]

# ÉP SÁT LỀ TRÁI TOÀN BỘ HTML ĐỂ STREAMLIT KHÔNG NHẬN DIỆN LÀ KHỐI CODE
    html_table = """<style>
.custom-calendar { width: 100%; border-collapse: collapse; font-family: sans-serif; background-color: white; margin-top: 10px;}
.custom-calendar th, .custom-calendar td { border: 1px solid #cbd5e1; padding: 10px; text-align: center; vertical-align: middle; }
.custom-calendar th { background-color: #f1f5f9; color: #1e293b; font-weight: bold; font-size: 15px;}
.session-col { font-weight: bold; background-color: #e2e8f0; color: #0f172a; writing-mode: vertical-rl; transform: rotate(180deg); width: 50px; font-size: 16px; letter-spacing: 3px;}
.time-col { background-color: #f8fafc; font-weight: 600; font-size: 13px; color: #475569; width: 120px; }
.holiday-header { color: #ef4444 !important; background-color: #fef2f2 !important; }
.holiday-text { color: #ef4444; font-size: 11px; font-weight: bold; display: block; margin-top: 5px; }
.holiday-cell { background-color: #fef2f2; color: #ef4444; font-weight: bold; height: 100px; font-size: 14px;}
.class-cell { background-color: #eff6ff; border: 1px solid #bfdbfe; border-radius: 6px; padding: 10px; box-shadow: 0 1px 2px rgba(0,0,0,0.05); min-height: 80px;}
.class-subject { color: #1e3a8a; font-weight: bold; margin-bottom: 5px; font-size: 14px;}
.class-room { color: #475569; font-size: 0.9em; margin-bottom: 8px; }
.class-teacher { color: #0f172a; font-weight: bold; font-size: 0.95em; }
</style>
<table class="custom-calendar">
<thead>
<tr>
<th>Buổi</th>
<th>Thời gian</th>"""
    
    for day in week_dates:
        if day["is_holiday"]:
            html_table += f"<th class='holiday-header'>{day['name']}<br><span style='font-size: 0.85em;'>({day['date']})</span><span class='holiday-text'>{day['holiday_name']}</span></th>"
        else:
            html_table += f"<th>{day['name']}<br><span style='font-size: 0.85em; color: #64748b;'>({day['date']})</span></th>"
=======
    with col3:
        c4, c5 = st.columns(2)
        if c4.button("Tuần", type="primary" if st.session_state.view_mode == "week" else "secondary", use_container_width=True):
            st.session_state.view_mode = "week"
        if c5.button("Tháng", type="primary" if st.session_state.view_mode == "month" else "secondary", use_container_width=True):
            st.session_state.view_mode = "month"

    st.markdown("<br>", unsafe_allow_html=True)

    # --- 3. TIẾN HÀNH BÓC TÁCH DỮ LIỆU TỪ MONGODB VÀO BẢNG ---
    start_of_week = get_start_of_week(st.session_state.current_date)
    start_of_week_date = start_of_week.date()
    
    raw_schedules = fetch_teacher_schedules(teacher_id)
    schedule_data = []
    
    # Từ điển dịch Thứ
    day_map = {0: "Thứ 2", 1: "Thứ 3", 2: "Thứ 4", 3: "Thứ 5", 4: "Thứ 6", 5: "Thứ 7", 6: "Chủ nhật"}

    # Xử lý logic để tìm các lớp học rơi trúng vào tuần đang xem
    for s in raw_schedules:
        s_start_date, s_end_date = parse_date_range(s.get("study_date", ""))
        s_days = s.get("days_of_week", [])
        
        # Duyệt 7 ngày trong tuần hiển thị trên Calendar
        for i in range(7):
            check_date = start_of_week_date + timedelta(days=i)
            day_name = day_map[i]
            
            # Nếu ngày này nằm trong khoảng khóa học VÀ nằm trong các thứ được xếp lịch
            if s_start_date <= check_date <= s_end_date and day_name in s_days:
                shift_id = get_shift_id(s.get("start_time", "00:00"))
                schedule_data.append({
                    "day_offset": i, 
                    "shift": shift_id, 
                    "subject": s.get("subject", "Không tên"), 
                    "class_name": s.get("class_name", ""),
                    "class_id": s.get("id", s.get("_id", "")),
                    "room": s.get("room", "Online"), 
                    "time_str": f"{s.get('start_time')} - {s.get('end_time')}"
                })

    # --- 4. VẼ BẢNG LỊCH BẰNG HTML/CSS ---
    if st.session_state.view_mode == "week":
        html_table = """
        <style>
            .custom-calendar { width: 100%; border-collapse: collapse; font-family: sans-serif; background-color: white; }
            .custom-calendar th { border: 1px solid #e2e8f0; padding: 12px; text-align: center; background-color: #f8fafc; color: #0f172a; font-weight: bold; }
            .custom-calendar td { border: 1px solid #e2e8f0; padding: 10px; text-align: center; vertical-align: middle; height: 110px; width: 12.5%; }
            .shift-header { font-weight: bold; background-color: #f8fafc; }
            .shift-time { font-size: 0.85em; color: #64748b; font-weight: normal; }
            .class-cell { background-color: #eff6ff; border: 1px solid #bfdbfe; border-radius: 6px; padding: 8px; box-shadow: 0 1px 2px rgba(0,0,0,0.05); height: 100%; display: flex; flex-direction: column; justify-content: center;}
            .class-subject { color: #1e3a8a; font-weight: bold; font-size: 0.95em; margin-bottom: 3px; }
            .class-name { color: #475569; font-size: 0.85em; font-weight: bold; margin-bottom: 3px; }
            .class-room { color: #b91c1c; font-size: 0.8em; }
        </style>
        <table class="custom-calendar">
            <thead>
                <tr>
                    <th></th>
        """
        day_names = ["Thứ Hai", "Thứ Ba", "Thứ Tư", "Thứ Năm", "Thứ Sáu", "Thứ Bảy", "Chủ Nhật"]
        for i in range(7):
            current_day = start_of_week + timedelta(days=i)
            html_table += f"<th>{day_names[i]}<br><span style='font-size: 0.85em; color: #64748b;'>({current_day.strftime('%d/%m')})</span></th>"
        html_table += "</tr></thead><tbody>"

        # Định nghĩa 5 Ca học (Bao gồm buổi tối)
        shifts = [
            {"id": 1, "name": "Ca 1 (Sáng)", "time": "07:30 - 09:30"},
            {"id": 2, "name": "Ca 2 (Sáng)", "time": "09:30 - 11:30"},
            {"id": 3, "name": "Ca 3 (Chiều)", "time": "13:30 - 15:30"},
            {"id": 4, "name": "Ca 4 (Chiều)", "time": "15:30 - 17:30"},
            {"id": 5, "name": "Ca 5 (Tối)", "time": "18:00 - 20:00"}
        ]

        for shift in shifts:
            html_table += f"<tr><td class='shift-header'>{shift['name']}<br><span class='shift-time'>{shift['time']}</span></td>"
            for day_idx in range(7):
                cell_content = ""
                for item in schedule_data:
                    if item['day_offset'] == day_idx and item['shift'] == shift['id']:
                        cell_content += f"""
                        <div class="class-cell">
                            <div class="class-subject">{item['subject']}</div>
                            <div class="class-name">{item['class_name']}</div>
                            <div class="class-room">🏫 {item['room']} <br> 🕒 {item['time_str']}</div>
                        </div>
                        """
                html_table += f"<td>{cell_content}</td>"
            html_table += "</tr>"
>>>>>>> b867fa3eeaab06e3a13728884e413c388f05024f
            
    html_table += "</tr></thead><tbody>"

    def generate_cells(shift_id):
        cells = ""
        for idx, day in enumerate(week_dates):
            if day["is_holiday"]:
                cells += "<td class='holiday-cell'>Nghỉ Lễ</td>"
            else:
                cell_content = ""
                for item in schedule_data:
                    if item['day_offset'] == idx and item['shift'] == shift_id:
                        cell_content = f"""<div class="class-cell">
<div class="class-subject">{item['subject']}</div>
<div class="class-room">({item['room']})</div>
<div class="class-teacher">{item['teachers']}</div>
</div>"""
                        break
                cells += f"<td>{cell_content}</td>"
        return cells

    html_table += f"""<tr>
<td rowspan="2" class="session-col">SÁNG</td>
<td class="time-col">Ca 1<br><small>07:30 - 09:30</small></td>
{generate_cells(1)}
</tr>
<tr>
<td class="time-col">Ca 2<br><small>09:45 - 11:45</small></td>
{generate_cells(2)}
</tr>"""

    html_table += f"""<tr>
<td rowspan="2" class="session-col">CHIỀU</td>
<td class="time-col">Ca 3<br><small>13:30 - 15:30</small></td>
{generate_cells(3)}
</tr>
<tr>
<td class="time-col">Ca 4<br><small>15:45 - 17:45</small></td>
{generate_cells(4)}
</tr>"""

    html_table += f"""<tr>
<td class="session-col" style="writing-mode: horizontal-tb; transform: none; letter-spacing: 0;">TỐI</td>
<td class="time-col">Ca 5<br><small>18:30 - 20:30</small></td>
{generate_cells(5)}
</tr>
</tbody>
</table>"""

    st.markdown(html_table, unsafe_allow_html=True)

    st.divider()

    # --- TƯƠNG TÁC GỬI ĐƠN NGHỈ / ĐỔI CA ---
    st.markdown("### 🛠️ Xét duyệt & Gửi đơn hỗ trợ")
    st.caption("Điền thông tin dưới đây để gửi yêu cầu thay đổi lịch dạy đến Nhân viên vận hành/Giám đốc.")
    
<<<<<<< HEAD
=======
    # Tạo danh sách lớp học mà giáo viên này ĐANG dạy để họ làm đơn
>>>>>>> b867fa3eeaab06e3a13728884e413c388f05024f
    active_classes = []
    class_map_for_form = {} # Dùng để lưu trữ class_id ẩn bên dưới
    
<<<<<<< HEAD
    if selected_class != "-- Vui lòng chọn ca dạy dưới đây --":
        st.markdown("---")
        parts = selected_class.split('|')
        class_date = parts[0].strip()
        class_shift = parts[1].strip()
        class_info = parts[2].strip()

        col_info, col_form = st.columns([1, 1.8])
        
        with col_info:
            st.success(f"**Mục tiêu xử lý:**\n\n"
                       f"📚 **Lớp:** {class_info}\n\n"
                       f"🗓️ **Ngày:** {class_date}\n\n"
                       f"⏱️ **Giờ:** {class_shift}")
            
        with col_form:
            st.markdown("**📌 Bước 2: Chi tiết yêu cầu**")
            req_type = st.radio(
                "Loại đơn", 
                ["🛑 Xin nghỉ dạy", "🔄 Xin đổi ca", "🏫 Xin đổi phòng"], 
                horizontal=True, 
                label_visibility="collapsed"
            )
            
            if "đổi ca" in req_type.lower():
                st.date_input("Đề xuất đổi sang ngày (Tuỳ chọn)")
                
            reason = st.text_area("Lý do cụ thể (Bắt buộc)", placeholder="Ví dụ: Bệnh đột xuất, vướng lịch thi trên trường, xe hỏng...")
            
            if st.button("🚀 Gửi Đơn Lên Giám Đốc Xét Duyệt", type="primary", use_container_width=True):
                if not reason.strip():
                    st.error("⚠️ Vui lòng nhập lý do cụ thể để Admin dễ dàng xem xét!")
                else:
                    clean_req_type = req_type.replace('🛑', '').replace('🔄', '').replace('🏫', '').strip()
                    
                    current_user_name = "Giáo Viên Ẩn Danh"
                    if "user_info" in st.session_state:
                        current_user_name = st.session_state["user_info"].get("name", "Giáo Viên Ẩn Danh")
                    
                    payload = {
                        "teacher_name": current_user_name,
                        "class_name": class_info,
                        "type": clean_req_type,
                        "reason": reason,
                        "date": class_date
                    }
                    
                    API_URL = "http://127.0.0.1:8000/submit-request"
                    try:
                        response = requests.post(API_URL, json=payload)
                        if response.status_code == 200:
                            st.success(f"✅ Đã gửi đơn **{clean_req_type}** thành công! Dữ liệu đã lưu vào MongoDB.")
                        else:
                            st.error(f"❌ Lỗi từ Server: {response.text}")
                    except requests.exceptions.RequestException:
                        st.error("❌ Không thể kết nối đến Backend. Hãy đảm bảo uvicorn đang chạy.")
=======
    for s in raw_schedules:
        label = f"{s.get('class_name')} - {s.get('subject')} | Khóa: {s.get('study_date')}"
        if label not in active_classes:
            active_classes.append(label)
            class_map_for_form[label] = {
                "class_id": s.get("class_id", ""),
                "class_name": s.get("class_name", "")
            }
        
    st.markdown("**📌 Bước 1: Chọn Lớp/Ca dạy đang gặp vấn đề**")
    
    if not active_classes:
        st.info("Bạn chưa có lịch dạy nào để thực hiện gửi đơn.")
    else:
        selected_class_label = st.selectbox("Chọn ca dạy", ["-- Vui lòng chọn --"] + active_classes, label_visibility="collapsed")
        
        if selected_class_label != "-- Vui lòng chọn --":
            st.markdown("---")
            selected_class_info = class_map_for_form[selected_class_label]

            col_info, col_form = st.columns([1, 1.8])
            
            with col_info:
                st.success(f"**Thông tin Lớp:**\n\n"
                           f"🏫 **Lớp:** {selected_class_info['class_name']}\n\n"
                           f"📚 **Nhận diện:** {selected_class_label.split('|')[0]}")
                
            with col_form:
                st.markdown("**📌 Bước 2: Chi tiết yêu cầu**")
                req_type = st.radio(
                    "Loại đơn", 
                    ["🛑 Xin nghỉ dạy", "🔄 Xin đổi ca", "🏫 Xin đổi phòng"], 
                    horizontal=True, 
                    label_visibility="collapsed"
                )
                
                if "đổi ca" in req_type.lower():
                    request_date = st.date_input("Đề xuất đổi sang ngày (Tuỳ chọn)")
                else:
                    request_date = st.date_input("Ngày áp dụng")
                    
                reason = st.text_area("Lý do cụ thể (Bắt buộc)", placeholder="Ví dụ: Bệnh đột xuất, vướng lịch thi trên trường, xe hỏng...")
                
                if st.button("🚀 Gửi Đơn Hỗ Trợ", type="primary", use_container_width=True):
                    if not reason.strip():
                        st.error("⚠️ Vui lòng nhập lý do cụ thể để bộ phận vận hành dễ dàng xem xét!")
                    else:
                        clean_req_type = req_type.replace('🛑', '').replace('🔄', '').replace('🏫', '').strip()
                        
                        # Sử dụng Model: TeacherRequestCreate (đã định nghĩa ở models.py)
                        payload = {
                            "teacher_id": teacher_id,
                            "teacher_name": teacher_name,
                            "class_id": selected_class_info['class_id'],
                            "class_name": selected_class_info['class_name'],
                            "type": clean_req_type,
                            "reason": reason,
                            "date": request_date.strftime("%Y-%m-%d"),
                            "status": "pending"
                        }
                        
                        # Gửi lên hệ thống API chung của bạn (VD: /api/requests)
                        # Ở đây tạo giả lập thành công để bạn kết nối API thực tế sau.
                        st.success(f"✅ Đã gửi đơn **{clean_req_type}** thành công! Đơn sẽ được chuyển đến Nhân viên vận hành.")
                        st.balloons()
>>>>>>> b867fa3eeaab06e3a13728884e413c388f05024f

if __name__ == "__main__":
    render_teacher_dashboard()