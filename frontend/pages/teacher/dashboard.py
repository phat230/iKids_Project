import streamlit as st
import requests
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
    if 'current_date' not in st.session_state:
        st.session_state.current_date = datetime.now()
    if 'view_mode' not in st.session_state:
        st.session_state.view_mode = "week"

    # --- 2. THANH ĐIỀU HƯỚNG LỊCH (HEADER) ---
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
            
        html_table += "</tbody></table>"
        st.markdown(html_table, unsafe_allow_html=True)

    else:
        st.info("Chế độ xem Tháng đang được phát triển. Vui lòng sử dụng chế độ Tuần để xem chi tiết Ca dạy.")

    st.divider()

    # --- 5. TƯƠNG TÁC GỬI ĐƠN NGHỈ / ĐỔI CA ---
    st.markdown("### 🛠️ Xét duyệt & Gửi đơn hỗ trợ")
    st.caption("Điền thông tin dưới đây để gửi yêu cầu thay đổi lịch dạy đến Nhân viên vận hành/Giám đốc.")
    
    # Tạo danh sách lớp học mà giáo viên này ĐANG dạy để họ làm đơn
    active_classes = []
    class_map_for_form = {} # Dùng để lưu trữ class_id ẩn bên dưới
    
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

if __name__ == "__main__":
    render_teacher_dashboard()