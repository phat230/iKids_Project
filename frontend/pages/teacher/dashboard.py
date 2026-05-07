import streamlit as st
import requests  # Bổ sung thư viện này để gọi API
from datetime import datetime, timedelta

def get_start_of_week(date):
    """Tính ngày Thứ 2 của tuần chứa ngày hiện tại"""
    return date - timedelta(days=date.weekday())

def render_teacher_dashboard():
    st.set_page_config(layout="wide") # Mở rộng toàn màn hình để bảng to rõ
    st.title("📅 Bảng Tin Giáo Viên (Lịch Dạy)")

    # --- 1. QUẢN LÝ TRẠNG THÁI NGÀY THÁNG (SESSION STATE) ---
    if 'current_date' not in st.session_state:
        st.session_state.current_date = datetime.now()
    if 'view_mode' not in st.session_state:
        st.session_state.view_mode = "week"

    # --- 2. THANH ĐIỀU HƯỚNG LỊCH (HEADER) ---
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col1:
        # Nút Hôm nay, Trái, Phải
        c1, c2, c3 = st.columns([1.5, 1, 1])
        if c1.button("Hôm nay", use_container_width=True):
            st.session_state.current_date = datetime.now()
        if c2.button("◀", use_container_width=True):
            st.session_state.current_date -= timedelta(days=7)
        if c3.button("▶", use_container_width=True):
            st.session_state.current_date += timedelta(days=7)
            
    with col2:
        # Hiển thị Tháng - Năm ở giữa
        month_names = ["", "Tháng 1", "Tháng 2", "Tháng 3", "Tháng 4", "Tháng 5", "Tháng 6", 
                       "Tháng 7", "Tháng 8", "Tháng 9", "Tháng 10", "Tháng 11", "Tháng 12"]
        current_month = month_names[st.session_state.current_date.month]
        current_year = st.session_state.current_date.year
        st.markdown(f"<h3 style='text-align: center; margin: 0; padding-top: 5px;'>{current_month} - {current_year}</h3>", unsafe_allow_html=True)

    with col3:
        # Nút chuyển chế độ xem (Tuần/Tháng)
        c4, c5 = st.columns(2)
        if c4.button("Tuần", type="primary" if st.session_state.view_mode == "week" else "secondary", use_container_width=True):
            st.session_state.view_mode = "week"
        if c5.button("Tháng", type="primary" if st.session_state.view_mode == "month" else "secondary", use_container_width=True):
            st.session_state.view_mode = "month"

    st.markdown("<br>", unsafe_allow_html=True)

    # --- 3. DỮ LIỆU LỊCH GIẢ LẬP TỪ ADMIN ---
    # Trong thực tế, bạn sẽ query database lọc theo ID Giáo Viên đang đăng nhập
    start_of_week = get_start_of_week(st.session_state.current_date)
    
    schedule_data = [
        {"day_offset": 0, "shift": 1, "subject": "Toán Cao Cấp", "room": "Phòng A.201", "teachers": "Minh Tran"}, # Thứ 2, Ca 1
        {"day_offset": 1, "shift": 2, "subject": "Dữ liệu AI", "room": "P.Máy M.101", "teachers": "Minh Tran vs Duc Phat"}, # Thứ 3, Ca 2
        {"day_offset": 3, "shift": 3, "subject": "Lập trình Scratch", "room": "Phòng Lab 2", "teachers": "Minh Tran"}, # Thứ 5, Ca 3
        {"day_offset": 4, "shift": 4, "subject": "Tiếng Anh Giao Tiếp", "room": "Phòng 105", "teachers": "Minh Tran"}, # Thứ 6, Ca 4
    ]

    # --- 4. VẼ BẢNG LỊCH BẰNG HTML/CSS ---
    if st.session_state.view_mode == "week":
        # Tạo CSS cho bảng
        html_table = """
        <style>
            .custom-calendar { width: 100%; border-collapse: collapse; font-family: sans-serif; background-color: white; }
            .custom-calendar th { border: 1px solid #e2e8f0; padding: 12px; text-align: center; background-color: #f8fafc; color: #0f172a; font-weight: bold; }
            .custom-calendar td { border: 1px solid #e2e8f0; padding: 15px; text-align: center; vertical-align: middle; height: 100px; width: 12.5%; }
            .shift-header { font-weight: bold; background-color: #f8fafc; }
            .shift-time { font-size: 0.85em; color: #64748b; font-weight: normal; }
            .class-cell { background-color: #eff6ff; border: 1px solid #bfdbfe; border-radius: 6px; padding: 10px; box-shadow: 0 1px 2px rgba(0,0,0,0.05); }
            .class-subject { color: #1e3a8a; font-weight: 500; margin-bottom: 5px; }
            .class-room { color: #475569; font-size: 0.9em; margin-bottom: 8px; }
            .class-teacher { color: #0f172a; font-weight: bold; font-size: 0.95em; }
        </style>
        <table class="custom-calendar">
            <thead>
                <tr>
                    <th></th>
        """
        # Tạo tiêu đề cột (Thứ Hai -> Chủ Nhật) kèm ngày
        day_names = ["Thứ Hai", "Thứ Ba", "Thứ Tư", "Thứ Năm", "Thứ Sáu", "Thứ Bảy", "Chủ Nhật"]
        for i in range(7):
            current_day = start_of_week + timedelta(days=i)
            html_table += f"<th>{day_names[i]}<br><span style='font-size: 0.85em; color: #64748b;'>({current_day.strftime('%d/%m')})</span></th>"
        html_table += "</tr></thead><tbody>"

        # Định nghĩa 4 Ca
        shifts = [
            {"id": 1, "name": "Ca 1 (Tiết 1,2,3)", "time": "6:30 - 9:00"},
            {"id": 2, "name": "Ca 2 (Tiết 4,5,6)", "time": "9:00 - 11:30"},
            {"id": 3, "name": "Ca 3 (Tiết 7,8,9)", "time": "12:30 - 15:00"},
            {"id": 4, "name": "Ca 4 (Tiết 10,11,12)", "time": "15:00 - 17:30"}
        ]

        # Đổ dữ liệu vào từng ô
        for shift in shifts:
            html_table += f"<tr><td class='shift-header'>{shift['name']}<br><span class='shift-time'>{shift['time']}</span></td>"
            for day_idx in range(7):
                cell_content = ""
                # Kiểm tra xem có lớp nào vào Ca này, Thứ này không
                for item in schedule_data:
                    if item['day_offset'] == day_idx and item['shift'] == shift['id']:
                        cell_content = f"""
                        <div class="class-cell">
                            <div class="class-subject">{item['subject']}</div>
                            <div class="class-room">({item['room']})</div>
                            <div class="class-teacher">{item['teachers']}</div>
                        </div>
                        """
                        break
                html_table += f"<td>{cell_content}</td>"
            html_table += "</tr>"
            
        html_table += "</tbody></table>"
        st.markdown(html_table, unsafe_allow_html=True)

    else:
        st.info("Chế độ xem Tháng đang được phát triển. Vui lòng sử dụng chế độ Tuần để xem chi tiết Ca dạy.")

    st.divider()

    # --- 5. TƯƠNG TÁC GỬI ĐƠN NGHỈ / ĐỔI CA ---
    st.markdown("### 🛠️ Xét duyệt & Gửi đơn hỗ trợ")
    st.caption("Điền thông tin dưới đây để gửi yêu cầu thay đổi lịch dạy đến Giám đốc trung tâm.")
    
    # Tạo danh sách dropdown chọn lớp
    active_classes = []
    for item in schedule_data:
        date_str = (start_of_week + timedelta(days=item['day_offset'])).strftime('%d/%m/%Y')
        shift_name = f"Ca {item['shift']}"
        active_classes.append(f"{date_str} | {shift_name} | {item['subject']} ({item['room']})")
        
    st.markdown("**📌 Bước 1: Chọn ca dạy đang gặp vấn đề**")
    selected_class = st.selectbox("Chọn ca dạy", ["-- Vui lòng chọn ca dạy dưới đây --"] + active_classes, label_visibility="collapsed")
    
    if selected_class != "-- Vui lòng chọn ca dạy dưới đây --":
        st.markdown("---")
        
        # Tách thông tin lớp để hiển thị đẹp hơn
        parts = selected_class.split('|')
        class_date = parts[0].strip()
        class_shift = parts[1].strip()
        class_info = parts[2].strip()

        # Chia 2 cột: Cột trái hiện thông tin chốt, Cột phải để điền đơn
        col_info, col_form = st.columns([1, 1.8])
        
        with col_info:
            st.success(f"**Mục tiêu xử lý:**\n\n"
                       f"📚 **Lớp:** {class_info}\n\n"
                       f"🗓️ **Ngày:** {class_date}\n\n"
                       f"⏱️ **Giờ:** {class_shift}")
            
        with col_form:
            st.markdown("**📌 Bước 2: Chi tiết yêu cầu**")
            # Dùng radio button ngang cho dễ nhìn
            req_type = st.radio(
                "Loại đơn", 
                ["🛑 Xin nghỉ dạy", "🔄 Xin đổi ca", "🏫 Xin đổi phòng"], 
                horizontal=True, 
                label_visibility="collapsed"
            )
            
            # Hiển thị thêm ô chọn ngày nếu là đơn xin đổi ca
            if "đổi ca" in req_type.lower():
                st.date_input("Đề xuất đổi sang ngày (Tuỳ chọn)")
                
            reason = st.text_area("Lý do cụ thể (Bắt buộc)", placeholder="Ví dụ: Bệnh đột xuất, vướng lịch thi trên trường, xe hỏng...")
            
            # --- CẬP NHẬT LOGIC API Ở ĐÂY ---
            if st.button("🚀 Gửi Đơn Lên Giám Đốc Xét Duyệt", type="primary", use_container_width=True):
                if not reason.strip():
                    st.error("⚠️ Vui lòng nhập lý do cụ thể để Admin dễ dàng xem xét!")
                else:
                    # Lọc bỏ icon để gửi tên loại đơn chuẩn lên DB
                    clean_req_type = req_type.replace('🛑', '').replace('🔄', '').replace('🏫', '').strip()
                    
                    # 1. Lấy tên user đang đăng nhập từ session_state (Đã sửa từ Fix cứng thành Tên Động)
                    current_user_name = "Giáo Viên Ẩn Danh"
                    if "user_info" in st.session_state:
                        current_user_name = st.session_state["user_info"].get("name", "Giáo Viên Ẩn Danh")
                    
                    # 2. Chuẩn bị dữ liệu Payload
                    payload = {
                        "teacher_name": current_user_name, # <-- Tên sẽ lấy đúng theo người đang đăng nhập
                        "class_name": class_info,
                        "type": clean_req_type,
                        "reason": reason,
                        "date": class_date
                    }
                    
                    # 3. Gọi API đến Backend
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