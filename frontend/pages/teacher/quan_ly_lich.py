import streamlit as st
import datetime

st.set_page_config(page_title="Lịch Giảng Dạy", layout="wide")

# ================= CẤU HÌNH NGÀY LỄ (VIỆT NAM) =================
# Thêm các ngày lễ cố định (Ngày/Tháng) vào đây, hệ thống sẽ tự động bắt
HOLIDAYS = {
    "01/01": "Tết Dương Lịch",
    "30/04": "Giải Phóng Miền Nam",
    "01/05": "Quốc Tế Lao Động",
    "01/06": "Quốc Tế Thiếu Nhi",
    "02/09": "Quốc Khánh",
    "20/11": "Ngày Nhà Giáo VN"
}

# ================= XỬ LÝ THỜI GIAN THỰC =================
today = datetime.date.today()
# Tìm ngày Thứ 2 của tuần hiện tại
start_of_week = today - datetime.timedelta(days=today.weekday())

# Tạo danh sách các ngày trong tuần
week_dates = []
for i in range(7):
    current_day = start_of_week + datetime.timedelta(days=i)
    date_str = current_day.strftime("%d/%m")
    
    week_dates.append({
        "name": f"Thứ {i+2}" if i < 6 else "Chủ Nhật",
        "date": date_str,
        "is_holiday": date_str in HOLIDAYS,
        "holiday_name": HOLIDAYS.get(date_str, "")
    })

# ================= GIAO DIỆN =================
st.title("📅 Lịch Giảng Dạy Của Bạn")
st.markdown("*Lịch học được cập nhật theo thời gian thực. Các ngày lễ hệ thống sẽ tự động tô đỏ.*")
st.write("---")

# ================= VẼ BẢNG LỊCH BẰNG HTML/CSS CHUẨN =================
# Định nghĩa CSS cho bảng
html_content = """
<style>
    .schedule-table { width: 100%; border-collapse: collapse; font-family: sans-serif; margin-top: 10px; }
    .schedule-table th, .schedule-table td { border: 1px solid #cbd5e1; padding: 10px; text-align: center; vertical-align: middle; }
    .schedule-table th { background-color: #f1f5f9; color: #1e293b; font-weight: bold; font-size: 15px;}
    
    /* CSS cho cột Buổi */
    .session-col { font-weight: bold; background-color: #e2e8f0; color: #0f172a; writing-mode: vertical-rl; transform: rotate(180deg); width: 50px; font-size: 16px; letter-spacing: 3px;}
    .time-col { background-color: #f8fafc; font-weight: 600; font-size: 13px; color: #475569; width: 120px; }
    
    /* CSS cho Ngày Lễ */
    .holiday-header { color: #ef4444 !important; background-color: #fef2f2 !important; }
    .holiday-text { color: #ef4444; font-size: 11px; font-weight: bold; display: block; margin-top: 5px; }
    .holiday-cell { background-color: #fef2f2; color: #ef4444; font-weight: bold; }
    
    .cell-data { min-height: 50px; font-size: 14px; }
</style>

<table class="schedule-table">
    <thead>
        <tr>
            <th>Buổi</th>
            <th>Thời gian</th>
"""

# Tạo Header cho các ngày trong tuần (Tự động tô đỏ nếu là ngày lễ)
for day in week_dates:
    if day["is_holiday"]:
        html_content += f"<th class='holiday-header'>{day['name']}<br>{day['date']}<span class='holiday-text'>{day['holiday_name']}</span></th>"
    else:
        html_content += f"<th>{day['name']}<br>{day['date']}</th>"

html_content += """
        </tr>
    </thead>
    <tbody>
"""

# Hàm tạo thẻ <td> cho từng ô học (nếu là lễ thì bôi đỏ ghi "Nghỉ lễ")
def generate_cells(ca_data):
    cells = ""
    for idx, day in enumerate(week_dates):
        if day["is_holiday"]:
            cells += "<td class='holiday-cell'>Nghỉ Lễ</td>"
        else:
            # Ở đây ông có thể map dữ liệu từ Backend vào. Dưới đây là dữ liệu mẫu.
            content = ca_data[idx] if idx < len(ca_data) else ""
            cells += f"<td><div class='cell-data'>{content}</div></td>"
    return cells

# --- DÒNG BUỔI SÁNG (Gộp 2 Ca) ---
ca1_data = ["Toán<br>Phòng A1", "", "", "", "", "", ""]
ca2_data = ["", "Tiếng Anh<br>Phòng B2", "", "", "", "", ""]

html_content += f"""
        <tr>
            <td rowspan="2" class="session-col">SÁNG</td>
            <td class="time-col">Ca 1<br><small>07:30 - 09:30</small></td>
            {generate_cells(ca1_data)}
        </tr>
        <tr>
            <td class="time-col">Ca 2<br><small>09:45 - 11:45</small></td>
            {generate_cells(ca2_data)}
        </tr>
"""

# --- DÒNG BUỔI CHIỀU (Gộp 2 Ca) ---
ca3_data = ["", "", "Lập trình<br>Lab 1", "", "", "", ""]
ca4_data = ["", "", "", "Kỹ năng<br>Phòng C3", "", "", ""]

html_content += f"""
        <tr>
            <td rowspan="2" class="session-col">CHIỀU</td>
            <td class="time-col">Ca 3<br><small>13:30 - 15:30</small></td>
            {generate_cells(ca3_data)}
        </tr>
        <tr>
            <td class="time-col">Ca 4<br><small>15:45 - 17:45</small></td>
            {generate_cells(ca4_data)}
        </tr>
"""

# --- DÒNG BUỔI TỐI (1 Ca) ---
ca5_data = ["", "", "", "", "Giao tiếp<br>Phòng D1", "", ""]

html_content += f"""
        <tr>
            <td class="session-col" style="writing-mode: horizontal-tb; transform: none; letter-spacing: 0;">TỐI</td>
            <td class="time-col">Ca 5<br><small>18:30 - 20:30</small></td>
            {generate_cells(ca5_data)}
        </tr>
    </tbody>
</table>
"""

# Hiển thị bảng HTML lên Streamlit
st.markdown(html_content, unsafe_allow_html=True)