import streamlit as st
import time
import requests
import os
from datetime import date

# Cấu hình API
API_URL = "http://localhost:8000"

st.set_page_config(page_title="Nhật Ký & Điểm Danh", page_icon="📓", layout="wide")

# ================= HÀM ĐỌC FILE CSS (SỬA LỖI ĐƯỜNG DẪN TUYỆT ĐỐI) =================
def load_css(file_name):
    """Tự động tìm file CSS trong thư mục frontend/CSS/"""
    # Lấy đường dẫn tuyệt đối đến thư mục chứa file nhat_ky.py hiện tại
    current_dir = os.path.dirname(os.path.abspath(__file__)) 
    
    # Tìm đường dẫn đến thư mục CSS (lùi 2 cấp từ pages/teacher/ rồi vào CSS/)
    css_root = os.path.abspath(os.path.join(current_dir, "../../CSS"))
    full_path = os.path.join(css_root, file_name)

    if os.path.exists(full_path):
        with open(full_path, "r", encoding="utf-8") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    else:
        st.warning(f"⚠️ Không tìm thấy file CSS tại: {full_path}")

# Tải CSS (Truyền folder con teacher/)
load_css("teacher/nhat_ky.css")

# --- KIỂM TRA QUYỀN TRUY CẬP ---
if "token" not in st.session_state or st.session_state.get("role") not in ["teacher", "admin"]:
    st.error("🔒 Bạn không có quyền truy cập trang này.")
    st.stop()

headers = {"Authorization": f"Bearer {st.session_state.token}"}
teacher_id = st.session_state.get("user_id")

st.title(" Nhật Ký Giảng Dạy & Điểm Danh")
st.write("Ghi nhận điểm danh và đánh giá học sinh từ danh sách lớp thực tế.")

# --- HÀM HỖ TRỢ LẤY DỮ LIỆU ---
@st.cache_data(ttl=60)
def fetch_teacher_classes():
    """Lấy danh sách các lớp từ lịch dạy"""
    try:
        res = requests.get(f"{API_URL}/schedule/list", headers=headers)
        if res.status_code == 200:
            all_schedules = res.json()
            # Lọc lịch dạy của chính giáo viên đang đăng nhập
            return [s for s in all_schedules if s.get('teacher_id') == teacher_id]
        return []
    except:
        return []

def fetch_students_by_class(class_id):
    """Lấy danh sách học sinh thật của lớp qua API của TV1"""
    try:
        res = requests.get(f"{API_URL}/classes/{class_id}/students/details", headers=headers)
        return res.json() if res.status_code == 200 else []
    except:
        return []

# ================= GIAO DIỆN CHÍNH =================
st.subheader("1. Lựa chọn ca dạy")
col_date, col_class = st.columns([1, 3])

with col_date:
    selected_date = st.date_input("Ngày dạy:", date.today())

my_classes = fetch_teacher_classes()
class_options = {s.get('id', s.get('_id')): f"{s['class_name']} - {s['subject']} ({s['start_time']})" for s in my_classes}

with col_class:
    if not class_options:
        st.warning(" Bạn không có lịch dạy nào trong hệ thống.")
        selected_sid = None
    else:
        selected_sid = st.selectbox("Chọn ca dạy từ lịch học:", 
                                     options=list(class_options.keys()), 
                                     format_func=lambda x: class_options[x])

st.divider()

if selected_sid:
    # Tìm thông tin lịch đã chọn
    current_schedule = next(s for s in my_classes if (s.get('id') or s.get('_id')) == selected_sid)
    col_left, col_right = st.columns([6, 4], gap="large")

    # ----------------- CỘT TRÁI: ĐIỂM DANH -----------------
    with col_left:
        st.markdown(f"### 👥 Điểm danh lớp: `{current_schedule['class_name']}`")
        students = fetch_students_by_class(selected_sid)
        attendance_records = []

        if not students:
            st.info("Chưa có học sinh nào đăng ký vào lớp này.")
        else:
            h1, h2, h3, h4 = st.columns([2.5, 2, 2, 3])
            h1.markdown("**Học sinh**")
            h2.markdown("**Trạng thái**")
            h3.markdown("**Thái độ**")
            h4.markdown("**Nhận xét**")

            for stu in students:
                with st.container(border=True):
                    c_name, c_att, c_emo, c_cmt = st.columns([2.5, 2, 2, 3])
                    sid = stu.get('Mã HS', stu.get('id', stu.get('_id')))
                    sname = stu.get('Tên Học Sinh', stu.get('name', 'Học sinh'))

                    c_name.markdown(f"<div style='padding-top: 5px;'>{sname}</div>", unsafe_allow_html=True)
                    att = c_att.selectbox("Trạng thái", [" Có mặt", " Vắng", " Đi trễ"], 
                                          key=f"att_{sid}", label_visibility="collapsed")
                    
                    is_absent = (att == "❌ Vắng")
                    emo = c_emo.selectbox("Thái độ", [" Xuất Sắc", " Tốt", " Bình Thường", " Kém"], 
                                          key=f"emo_{sid}", label_visibility="collapsed", disabled=is_absent)
                    cmt = c_cmt.text_input("Nhận xét", placeholder="Khen ngợi...", 
                                           key=f"cmt_{sid}", label_visibility="collapsed", disabled=is_absent)
                    
                    attendance_records.append({
                        "student_id": sid,
                        "student_name": sname,
                        "status": att,
                        "feedback": emo,
                        "comment": cmt
                    })

    # ----------------- CỘT PHẢI: NHẬT KÝ BÀI GIẢNG -----------------
    with col_right:
        st.markdown("###  Nhật Ký Bài Giảng")
        with st.container(border=True):
            lesson_topic = st.text_input(" Chủ Đề Giảng Dạy:", value=current_schedule['subject'])
            
            try:
                res_v = requests.get(f"{API_URL}/api/tv2/videos")
                vids = res_v.json() if res_v.status_code == 200 else []
                res_q = requests.get(f"{API_URL}/api/tv2/quizzes")
                quizzes = res_q.json() if res_q.status_code == 200 else []
            except: vids, quizzes = [], []
            
            used_v = st.multiselect("Video Bài Tập Đã Dùng:", [v['title'] for v in vids])
            assigned_q = st.multiselect(" Giao Bài Tập Về Nhà:", [q['title'] for q in quizzes])
            content = st.text_area(" Chi Tiết Nội Dung Giảng Dạy:", height=150)

            if st.button(" LƯU & GỬI BÁO CÁO", type="primary", use_container_width=True):
                if not content.strip():
                    st.error("⚠️ Vui lòng nhập nội dung đã dạy.")
                else:
                    journal_payload = {
                        "class_id": selected_sid,
                        "class_name": current_schedule['class_name'],
                        "teacher_id": teacher_id,
                        "date": str(selected_date),
                        "topic": lesson_topic,
                        "content_taught": content,
                        "attendance": attendance_records,
                        "materials": {"videos": used_v, "quizzes": assigned_q}
                    }
                    
                    with st.spinner("Đang gửi báo cáo cho Phụ huynh..."):
                        res = requests.post(f"{API_URL}/api/tv2/journal", json=journal_payload, headers=headers)
                        if res.status_code in [200, 201]:
                            st.success("✅ Đã lưu nhật ký và gửi thông báo thành công!")
                            st.balloons()
                            time.sleep(2)
                            st.rerun()
                        else:
                            st.error(f"❌ Lỗi: {res.text}")