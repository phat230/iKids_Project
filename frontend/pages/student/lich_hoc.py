import streamlit as st
import pandas as pd
import requests
import os
from datetime import datetime
from utils.role_guard import require_role

# Bảo vệ trang, chỉ học sinh được vào
require_role(["student"])

# ================= CRITICAL: CẤU HÌNH TRANG LUÔN ĐỂ ĐẦU FILE =================
st.set_page_config(page_title="Lịch Học Của Tôi", page_icon="📅", layout="wide")

# ================= HÀM ĐỌC FILE CSS (SỬA LỖI ĐƯỜNG DẪN) =================
def load_css(file_name):
    """
    Tự động tìm file CSS trong thư mục frontend/CSS/
    file_name: tên file kèm thư mục con, ví dụ 'student/lich_hoc.css'
    """
    # Lấy đường dẫn tuyệt đối đến thư mục chứa file lich_hoc.py hiện tại
    current_dir = os.path.dirname(os.path.abspath(__file__)) # frontend/pages/student
    
    # Tìm đường dẫn đến thư mục CSS (lùi 2 cấp rồi vào CSS/)
    css_root = os.path.abspath(os.path.join(current_dir, "../../CSS"))
    full_path = os.path.join(css_root, file_name)

    if os.path.exists(full_path):
        with open(full_path, "r", encoding="utf-8") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    else:
        st.warning(f"⚠️ Không tìm thấy file CSS tại: {full_path}")

# Tải CSS (Chỉ truyền phần tên thư mục con và file)
load_css("student/student_global.css")

# ĐÃ SỬA: Lấy BACKEND_URL chung từ session_state và cấu hình URL theo module
BACKEND_URL = st.session_state.get("api_url", "http://localhost:8000")
API_TV1 = f"{BACKEND_URL}/api/tv1"

# Lấy cấu hình ngôn ngữ hiện hành từ session_state toàn cục (Mặc định là "vi")
lang = st.session_state.get("lang", "vi")

# ==========================================
# BỘ TỪ ĐIỂN SONG NGỮ CHI TIẾT CHO STUDENT LICH_HOC
# ==========================================
STUDENT_SCHEDULE_LABELS = {
    "vi": {
        "title": "📅 Thời Khóa Biểu Của Tôi",
        "subtitle": "Theo dõi lịch học để không bỏ lỡ buổi học nào nhé!",
        "spinner_loading": "Đang tải thời khóa biểu của bạn...",
        "info_empty": "ℹ️ Bạn chưa có lịch học nào. Vui lòng đợi Nhân viên vận hành xếp lịch hoặc nhờ Phụ huynh đăng ký lớp mới nhé!",
        "caption_footer": "💡 Lịch học sẽ tự động cập nhật nếu Nhân viên vận hành thay đổi thời gian hoặc phòng học.",
        "err_connection": "Lỗi kết nối máy chủ:",
        
        # Tiêu đề cột DataFrame
        "col_subject": "Môn học",
        "col_class": "Tên lớp",
        "col_teacher": "Giáo viên",
        "col_days": "Thứ trong tuần",
        "col_slot": "Ca học",
        "col_duration": "Khóa học",
        "col_room": "Phòng học",
        "col_status": "Trạng thái",
        
        # Giá trị ô dữ liệu tĩnh
        "val_unknown": "Chưa rõ",
        "val_updating": "Đang cập nhật",
        "val_not_assigned": "Chưa xếp thứ",
        "status_active": "🟢 Đang diễn ra",
        "status_ended": "🔴 Đã kết thúc"
    },
    "en": {
        "title": "📅 My Class Schedule",
        "subtitle": "Keep track of your classes and never miss a single lesson!",
        "spinner_loading": "Loading your class timetable...",
        "info_empty": "ℹ️ You do not have any classes scheduled yet. Please wait for the academic staff to assign your schedule or ask your Parents to enroll in a new class!",
        "caption_footer": "💡 Your schedule updates automatically whenever operators change the time slots or classrooms.",
        "err_connection": "Server connection failure:",
        
        # DataFrame Table Header Config
        "col_subject": "Subject",
        "col_class": "Class Name",
        "col_teacher": "Teacher",
        "col_days": "Days of Week",
        "col_slot": "Time Slot",
        "col_duration": "Course Duration",
        "col_room": "Room/Classroom",
        "col_status": "Status",
        
        # Data cell static values mapping
        "val_unknown": "Unknown",
        "val_updating": "Updating...",
        "val_not_assigned": "Not Assigned Yet",
        "status_active": "🟢 Ongoing",
        "status_ended": "🔴 Completed"
    }
}

st.title(STUDENT_SCHEDULE_LABELS[lang]["title"])
st.write(STUDENT_SCHEDULE_LABELS[lang]["subtitle"])
st.divider()

# Lấy ID của học sinh đang đăng nhập
student_id = st.session_state.get("user_id")

# =========================
# HÀM LẤY LỊCH HỌC TỰ ĐỘNG
# =========================
@st.cache_data(ttl=30)
def get_my_schedules(current_student_id):
    try:
        # ĐÃ SỬA: Gọi API thông qua module TV1 vì Lịch/Lớp thuộc module TV1
        res_classes = requests.get(f"{API_TV1}/classes", timeout=10)
        if res_classes.status_code != 200:
            return []
        all_classes = res_classes.json()
        
        # Lọc ra các Lớp mà học sinh này CÓ TÊN trong danh sách
        my_class_ids = [
            c.get("id", c.get("_id")) for c in all_classes 
            if isinstance(c, dict) and current_student_id in c.get("student_ids", [])
        ]

        if not my_class_ids:
            return []

        # Lấy toàn bộ lịch học và chỉ giữ lại lịch của các lớp bé đang học
        headers = {"Authorization": f"Bearer {st.session_state.get('token', '')}"}
        # ĐÃ SỬA: Gọi API thông qua module TV1
        res_schedules = requests.get(f"{API_TV1}/schedule/list", headers=headers, timeout=10)
        
        if res_schedules.status_code != 200:
            return []
        all_schedules = res_schedules.json()

        # Chỉ lấy lịch có class_id nằm trong danh sách lớp của bé, và lịch đó chưa bị hủy
        my_schedules = [
            s for s in all_schedules 
            if s.get("class_id") in my_class_ids and s.get("status") == "active"
        ]
        return my_schedules
    except Exception as e:
        st.error(f"{STUDENT_SCHEDULE_LABELS[lang]['err_connection']} {e}")
        return []

# Mảng các đầu cột chuẩn hóa theo ngôn ngữ lựa chọn
columns_list = [
    STUDENT_SCHEDULE_LABELS[lang]["col_subject"],
    STUDENT_SCHEDULE_LABELS[lang]["col_class"],
    STUDENT_SCHEDULE_LABELS[lang]["col_teacher"],
    STUDENT_SCHEDULE_LABELS[lang]["col_days"],
    STUDENT_SCHEDULE_LABELS[lang]["col_slot"],
    STUDENT_SCHEDULE_LABELS[lang]["col_duration"],
    STUDENT_SCHEDULE_LABELS[lang]["col_room"],
    STUDENT_SCHEDULE_LABELS[lang]["col_status"]
]

# =========================
# HIỂN THỊ DỮ LIỆU LÊN BẢNG
# =========================
with st.spinner(STUDENT_SCHEDULE_LABELS[lang]["spinner_loading"]):
    schedules = get_my_schedules(student_id)

if not schedules:
    st.info(STUDENT_SCHEDULE_LABELS[lang]["info_empty"])
    
    # Hiển thị bảng trống định dạng chuẩn cho thẩm mỹ giao diện
    empty_df = pd.DataFrame(columns=columns_list)
    st.dataframe(empty_df, use_container_width=True, hide_index=True)
else:
    # Xử lý và làm đẹp dữ liệu cho bảng
    table_data = []
    
    for s in schedules:
        study_date_str = s.get('study_date', STUDENT_SCHEDULE_LABELS[lang]["val_unknown"])
        days_list = s.get('days_of_week', [])
        
        # Bản dịch các Thứ trong tuần nếu hiển thị Tiếng Anh
        if lang == "en" and days_list:
            day_mapping = {
                "Thứ 2": "Monday", "Thứ 3": "Tuesday", "Thứ 4": "Wednesday",
                "Thứ 5": "Thursday", "Thứ 6": "Friday", "Thứ 7": "Saturday", "Chủ Nhật": "Sunday", "Chủ nhật": "Sunday"
            }
            days_list = [day_mapping.get(d, d) for d in days_list]

        days_str = ", ".join(days_list) if days_list else STUDENT_SCHEDULE_LABELS[lang]["val_not_assigned"]
        time_str = f"{s.get('start_time', '--:--')} - {s.get('end_time', '--:--')}"
        
        # Bản dịch nhãn thời lượng Khóa học nếu có ký tự chuỗi kết nối
        if lang == "en" and isinstance(study_date_str, str) and "đến" in study_date_str:
            study_date_str = study_date_str.replace("đến", "to")

        # Tính toán Trạng thái (Đang học / Đã kết thúc) giống phân hệ Vận hành
        try:
            now = datetime.now()
            end_time_str = s.get('end_time', '23:59')
            if "đến" in s.get('study_date', ''):
                end_date_str = s.get('study_date', '').split("đến")[1].strip()
                end_datetime = datetime.strptime(f"{end_date_str} {end_time_str}", "%d/%m/%Y %H:%M")
            elif "to" in study_date_str:
                end_date_str = s.get('study_date', '').split("to")[1].strip()
                end_datetime = datetime.strptime(f"{end_date_str} {end_time_str}", "%d/%m/%Y %H:%M")
            elif "/" in study_date_str:
                end_datetime = datetime.strptime(f"{study_date_str} {end_time_str}", "%d/%m/%Y %H:%M")
            else:
                end_datetime = datetime.strptime(f"{study_date_str} {end_time_str}", "%Y-%m-%d %H:%M")
            
            if now > end_datetime:
                status = STUDENT_SCHEDULE_LABELS[lang]["status_ended"]
            else:
                status = STUDENT_SCHEDULE_LABELS[lang]["status_active"]
        except:
            status = STUDENT_SCHEDULE_LABELS[lang]["status_active"]

        table_data.append({
            STUDENT_SCHEDULE_LABELS[lang]["col_subject"]: s.get("subject", STUDENT_SCHEDULE_LABELS[lang]["val_unknown"]),
            STUDENT_SCHEDULE_LABELS[lang]["col_class"]: s.get("class_name", STUDENT_SCHEDULE_LABELS[lang]["val_unknown"]),
            STUDENT_SCHEDULE_LABELS[lang]["col_teacher"]: s.get("teacher_name", STUDENT_SCHEDULE_LABELS[lang]["val_updating"]),
            STUDENT_SCHEDULE_LABELS[lang]["col_days"]: days_str,
            STUDENT_SCHEDULE_LABELS[lang]["col_slot"]: time_str,
            STUDENT_SCHEDULE_LABELS[lang]["col_duration"]: study_date_str,
            STUDENT_SCHEDULE_LABELS[lang]["col_room"]: s.get("room", "Online"),
            STUDENT_SCHEDULE_LABELS[lang]["col_status"]: status
        })

    # Đưa vào Pandas DataFrame để kết xuất giao diện
    df = pd.DataFrame(table_data)
    
    # Sắp xếp để các môn lớp "Đang diễn ra" luôn nằm trên cùng, các môn đã đóng lớp đẩy xuống dưới
    df = df.sort_values(by=STUDENT_SCHEDULE_LABELS[lang]["col_status"], ascending=False)

    # Hiển thị bảng dữ liệu (Table/Dataframe)
    st.dataframe(df, use_container_width=True, hide_index=True)
    
    st.caption(STUDENT_SCHEDULE_LABELS[lang]["caption_footer"])