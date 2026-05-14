import streamlit as st
import requests
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
    st.caption("Điền thông tin dưới đây để gửi yêu cầu thay đổi lịch dạy đến Giám đốc trung tâm.")
    
    active_classes = []
    for item in schedule_data:
        date_str = (start_of_week + timedelta(days=item['day_offset'])).strftime('%d/%m/%Y')
        shift_name = f"Ca {item['shift']}"
        active_classes.append(f"{date_str} | {shift_name} | {item['subject']} ({item['room']})")
        
    st.markdown("**📌 Bước 1: Chọn ca dạy đang gặp vấn đề**")
    selected_class = st.selectbox("Chọn ca dạy", ["-- Vui lòng chọn ca dạy dưới đây --"] + active_classes, label_visibility="collapsed")
    
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

if __name__ == "__main__":
    render_teacher_dashboard()