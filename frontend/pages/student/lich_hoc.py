import streamlit as st
import pandas as pd
import requests
import os
from datetime import datetime
from utils.role_guard import require_role

# Bảo vệ trang, chỉ học sinh được vào
require_role(["student"])

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
load_css("student/lich_hoc.css")

API_URL = "http://localhost:8000"

st.title("📅 Thời Khóa Biểu Của Tôi")
st.write("Theo dõi lịch học để không bỏ lỡ buổi học nào nhé!")
st.divider()

# Lấy ID của học sinh đang đăng nhập
student_id = st.session_state.get("user_id")

# =========================
# HÀM LẤY LỊCH HỌC TỰ ĐỘNG
# =========================
@st.cache_data(ttl=30)
def get_my_schedules(current_student_id):
    try:
        # 1. Gọi API lấy danh sách toàn bộ lớp học
        res_classes = requests.get(f"{API_URL}/classes", timeout=10)
        if res_classes.status_code != 200:
            return []
        all_classes = res_classes.json()
        
        # 2. Lọc ra các Lớp mà học sinh này CÓ TÊN trong danh sách (student_ids)
        my_class_ids = [
            c.get("id", c.get("_id")) for c in all_classes 
            if isinstance(c, dict) and current_student_id in c.get("student_ids", [])
        ]

        if not my_class_ids:
            return []

        # 3. Lấy toàn bộ lịch học và chỉ giữ lại lịch của các lớp bé đang học
        headers = {"Authorization": f"Bearer {st.session_state.get('token', '')}"}
        res_schedules = requests.get(f"{API_URL}/schedule/list", headers=headers, timeout=10)
        
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
        st.error(f"Lỗi kết nối máy chủ: {e}")
        return []

# =========================
# HIỂN THỊ DỮ LIỆU LÊN BẢNG
# =========================
with st.spinner("Đang tải thời khóa biểu của bạn..."):
    schedules = get_my_schedules(student_id)

if not schedules:
    st.info("ℹ️ Bạn chưa có lịch học nào. Vui lòng đợi Nhân viên vận hành xếp lịch hoặc nhờ Phụ huynh đăng ký lớp mới nhé!")
    
    # Hiển thị bảng trống cho đẹp mắt
    empty_df = pd.DataFrame(columns=["Môn học", "Tên lớp", "Giáo viên", "Thứ trong tuần", "Ca học", "Khóa học", "Phòng học", "Trạng thái"])
    st.dataframe(empty_df, use_container_width=True, hide_index=True)
else:
    # Xử lý và làm đẹp dữ liệu cho bảng
    table_data = []
    
    for s in schedules:
        study_date_str = s.get('study_date', 'Chưa rõ')
        days_list = s.get('days_of_week', [])
        days_str = ", ".join(days_list) if days_list else "Chưa xếp thứ"
        time_str = f"{s.get('start_time', '--:--')} - {s.get('end_time', '--:--')}"
        
        # Tính toán Trạng thái (Đang học / Đã kết thúc) giống bên Vận hành
        try:
            now = datetime.now()
            end_time_str = s.get('end_time', '23:59')
            if "đến" in study_date_str:
                end_date_str = study_date_str.split("đến")[1].strip()
                end_datetime = datetime.strptime(f"{end_date_str} {end_time_str}", "%d/%m/%Y %H:%M")
            elif "/" in study_date_str:
                end_datetime = datetime.strptime(f"{study_date_str} {end_time_str}", "%d/%m/%Y %H:%M")
            else:
                end_datetime = datetime.strptime(f"{study_date_str} {end_time_str}", "%Y-%m-%d %H:%M")
            
            if now > end_datetime:
                status = "Đã kết thúc"
            else:
                status = "🟢 Đang diễn ra"
        except:
            status = "🟢 Đang diễn ra"

        table_data.append({
            "Môn học": s.get("subject", "Chưa rõ"),
            "Tên lớp": s.get("class_name", "Chưa rõ"),
            "Giáo viên": s.get("teacher_name", "Đang cập nhật"),
            "Thứ trong tuần": days_str,
            "Ca học": time_str,
            "Khóa học": study_date_str,
            "Phòng học": s.get("room", "Online"),
            "Trạng thái": status
        })

    # Đưa vào Pandas DataFrame để hiển thị đẹp như Excel
    df = pd.DataFrame(table_data)
    
    # Sắp xếp để các môn "Đang diễn ra" luôn nằm trên cùng, các môn "Đã kết thúc" đẩy xuống dưới
    df = df.sort_values(by="Trạng thái", ascending=False)

    # Hiển thị bảng dữ liệu (Table/Dataframe)
    st.dataframe(df, use_container_width=True, hide_index=True)
    
    st.caption("💡 Lịch học sẽ tự động cập nhật nếu Nhân viên vận hành thay đổi thời gian hoặc phòng học.")