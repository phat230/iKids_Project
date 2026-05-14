import streamlit as st
import requests
from datetime import datetime, timedelta, date

# Tạm thời import bảo vệ role (nếu dự án ông đang dùng)
try:
    from utils.role_guard import require_role
    require_role(["teacher", "admin"])
except ImportError:
    pass # Bỏ qua nếu module này chưa có

# ================= CẤU HÌNH HỆ THỐNG & NGÀY LỄ =================
API_URL = "http://127.0.0.1:8000"

HOLIDAYS = {
    "01/01": "Tết Dương Lịch",
    "30/04": "Giải Phóng Miền Nam",
    "01/05": "Quốc Tế Lao Động",
    "01/06": "Quốc Tế Thiếu Nhi",
    "02/09": "Quốc Khánh",
    "20/11": "Ngày Nhà Giáo VN"
}

# ================= CÁC HÀM HỖ TRỢ XỬ LÝ LỊCH =================
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
        if h < 9: return 1   # Ca 1 Sáng
        elif h < 12: return 2 # Ca 2 Sáng
        elif h < 15: return 3 # Ca 3 Chiều
        elif h < 17: return 4 # Ca 4 Chiều
        else: return 5        # Ca 5 Tối
    except:
        return 5

# ================= LẤY DỮ LIỆU TỪ MONGODB =================
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
    st.set_page_config(page_title="Quản Lý Lịch Dạy", page_icon="📅", layout="wide") 
    st.title("📅 Lịch Giảng Dạy & Gửi Yêu Cầu")

    teacher_id = st.session_state.get("user_id", "gv_demo_id")
    teacher_name = st.session_state.get("user_info", {}).get("name", "Giáo viên")

    # --- 1. QUẢN LÝ TRẠNG THÁI NGÀY THÁNG ---
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

    st.markdown("<br>", unsafe_allow_html=True)

    # --- 2. XỬ LÝ DỮ LIỆU ĐỔ VÀO BẢNG ---
    start_of_week = get_start_of_week(st.session_state.current_date)
    start_of_week_date = start_of_week.date()
    
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

    raw_schedules = fetch_teacher_schedules(teacher_id)
    schedule_data = []
    active_classes = []
    class_map_for_form = {} 

    day_map = {0: "Thứ 2", 1: "Thứ 3", 2: "Thứ 4", 3: "Thứ 5", 4: "Thứ 6", 5: "Thứ 7", 6: "Chủ nhật"}

    for s in raw_schedules:
        s_start_date, s_end_date = parse_date_range(s.get("study_date", ""))
        s_days = s.get("days_of_week", [])
        
        label = f"{s.get('class_name')} - {s.get('subject')} | Khóa: {s.get('study_date')}"
        if label not in active_classes:
            active_classes.append(label)
            class_map_for_form[label] = {
                "class_id": s.get("class_id", s.get("id", s.get("_id", ""))),
                "class_name": s.get("class_name", "")
            }

        for i in range(7):
            check_date = start_of_week_date + timedelta(days=i)
            day_name = day_map[i]
            
            if s_start_date <= check_date <= s_end_date and day_name in s_days:
                shift_id = get_shift_id(s.get("start_time", "00:00"))
                schedule_data.append({
                    "day_offset": i, 
                    "shift": shift_id, 
                    "subject": s.get("subject", "Không tên"), 
                    "class_name": s.get("class_name", ""),
                    "room": s.get("room", "Online"), 
                    "time_str": f"{s.get('start_time')} - {s.get('end_time')}"
                })

    if not schedule_data:
        schedule_data = [
            {"day_offset": 0, "shift": 1, "subject": "Toán Cao Cấp", "class_name": "Lớp T6", "room": "A.201", "time_str": "07:30 - 09:30"},
            {"day_offset": 3, "shift": 3, "subject": "Lập trình Scratch", "class_name": "Lớp S1", "room": "Lab 2", "time_str": "13:30 - 15:30"}
        ]
        active_classes = ["Lớp T6 - Toán Cao Cấp | Khóa: Demo", "Lớp S1 - Lập trình Scratch | Khóa: Demo"]
        class_map_for_form = {
            "Lớp T6 - Toán Cao Cấp | Khóa: Demo": {"class_id": "c1", "class_name": "Lớp T6"},
            "Lớp S1 - Lập trình Scratch | Khóa: Demo": {"class_id": "c2", "class_name": "Lớp S1"}
        }

    # --- 3. VẼ BẢNG LỊCH BẰNG HTML/CSS ---
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
.class-name { color: #475569; font-size: 0.85em; font-weight: bold; margin-bottom: 3px; }
.class-room { color: #b91c1c; font-size: 0.8em; }
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
                        cell_content += f"""<div class="class-cell">
<div class="class-subject">{item['subject']}</div>
<div class="class-name">{item['class_name']}</div>
<div class="class-room">🏫 {item['room']} <br> 🕒 {item['time_str']}</div>
</div>"""
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

    # --- 4. TƯƠNG TÁC GỬI ĐƠN HỖ TRỢ ---
    st.markdown("### 🛠️ Gửi Đơn Xin Hỗ Trợ (Vận Hành)")
    st.caption("Chọn lớp học và gửi yêu cầu thay đổi lịch dạy/phòng dạy tới Admin.")
    
    # LUÔN HIỂN THỊ CỐ ĐỊNH LAYOUT FORM
    selected_class_label = st.selectbox("📌 Bước 1: Chọn Lớp/Ca dạy đang gặp vấn đề", ["-- Vui lòng chọn --"] + active_classes)
    st.markdown("---")
    
    col_info, col_form = st.columns([1, 1.8])
    
    with col_info:
        if selected_class_label == "-- Vui lòng chọn --":
            st.info("👈 Hãy chọn một lớp ở mục trên để hệ thống nạp thông tin.")
        else:
            selected_class_info = class_map_for_form[selected_class_label]
            st.success(f"**Thông tin Lớp đã chọn:**\n\n"
                       f"🏫 **Lớp:** {selected_class_info['class_name']}\n\n"
                       f"📚 **Nhận diện:** {selected_class_label.split('|')[0]}")
            
    with col_form:
        st.markdown("**📌 Bước 2: Chi tiết yêu cầu**")
        
        req_type = st.radio(
            "Loại đơn", 
            ["🛑 Xin nghỉ dạy", "🔄 Xin đổi ngày/ca", "🏫 Xin đổi phòng", "💻 Xin đổi PT dạy (On/Off)"], 
            horizontal=True, 
            label_visibility="collapsed"
        )
        
        if "đổi ngày" in req_type.lower():
            request_date = st.date_input("Đề xuất đổi sang ngày")
        else:
            request_date = st.date_input("Ngày áp dụng thay đổi")
            
        reason = st.text_area("Lý do cụ thể (Bắt buộc)", placeholder="Ví dụ: Bệnh đột xuất, vướng lịch thi trên trường, chuyển sang dạy Online do ngập đường...")
        
        if st.button("🚀 Gửi Đơn Hỗ Trợ", type="primary", use_container_width=True):
            if selected_class_label == "-- Vui lòng chọn --":
                st.error("⚠️ Vui lòng chọn Lớp/Ca dạy cần hỗ trợ ở Bước 1 trước khi gửi!")
            elif not reason.strip():
                st.error("⚠️ Vui lòng nhập lý do cụ thể để bộ phận vận hành xem xét!")
            else:
                clean_req_type = req_type.replace('🛑', '').replace('🔄', '').replace('🏫', '').replace('💻', '').strip()
                selected_class_info = class_map_for_form[selected_class_label]
                
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
                
                try:
                    response = requests.post(f"{API_URL}/submit-request", json=payload)
                    if response.status_code == 200:
                        st.success(f"✅ Đã gửi đơn **{clean_req_type}** thành công! Đơn đã được chuyển tới Admin.")
                        st.balloons()
                    else:
                        st.error(f"❌ Lỗi từ Server: {response.text}")
                except requests.exceptions.RequestException:
                    st.error("❌ Không thể kết nối đến Backend. Hãy đảm bảo uvicorn đang chạy.")

if __name__ == "__main__":
    render_teacher_dashboard()