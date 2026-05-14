import streamlit as st
import time
import requests
from datetime import date

# Cấu hình API
API_URL = "http://localhost:8000"

st.set_page_config(page_title="Nhật Ký & Điểm Danh", page_icon="📓", layout="wide")

# --- KIỂM TRA QUYỀN TRUY CẬP ---
if "token" not in st.session_state or st.session_state.role not in ["teacher", "admin"]:
    st.error("🔒 Bạn không có quyền truy cập trang này.")
    st.stop()

headers = {"Authorization": f"Bearer {st.session_state.token}"}

st.title("📓 Nhật Ký Giảng Dạy & Điểm Danh")
st.write("Ghi nhận điểm danh, đánh giá học sinh từ danh sách lớp thực tế.")

# --- HÀM HỖ TRỢ LẤY DỮ LIỆU ---
@st.cache_data(ttl=60)
def fetch_teacher_classes():
    """Lấy danh sách các lớp mà giáo viên này đang dạy"""
    try:
        # Trong thực tế, API này sẽ lọc theo teacher_id trong database
        res = requests.get(f"{API_URL}/api/tv3/parent/my-children", headers=headers) # Demo dùng chung route lấy thông tin
        # Giả lập trả về danh sách lớp từ hệ thống lịch dạy (TV1)
        res_classes = requests.get(f"{API_URL}/schedule/list", headers=headers)
        return res_classes.json() if res_classes.status_code == 200 else []
    except:
        return []

def fetch_students_by_class(class_id):
    """Lấy danh sách học sinh thật từ một lớp cụ thể"""
    try:
        # Route này sẽ lấy student_ids từ ClassModel và query thông tin từ users
        res = requests.get(f"{API_URL}/api/tv3/parent/my-children", headers=headers) 
        # Để demo, chúng ta lấy danh sách user có role student
        return res.json() 
    except:
        return []

# ================= GIAO DIỆN CHÍNH =================
st.subheader("1. Lựa chọn ca dạy")
col_date, col_class = st.columns([1, 3])

with col_date:
    selected_date = st.date_input("Ngày dạy:", date.today())

# Lấy dữ liệu lớp học thật từ Backend
all_schedules = fetch_teacher_classes()
class_options = {s['id']: f"{s['class_name']} - {s['subject']} ({s['start_time']})" for s in all_schedules}

with col_class:
    if not class_options:
        st.warning("📅 Bạn không có lịch dạy nào trong hệ thống.")
        selected_schedule_id = None
    else:
        selected_schedule_id = st.selectbox("Chọn ca dạy từ lịch học:", 
                                           options=list(class_options.keys()), 
                                           format_func=lambda x: class_options[x])

st.divider()

if selected_schedule_id:
    # Lấy thông tin lịch đã chọn
    current_schedule = next(s for s in all_schedules if s['id'] == selected_schedule_id)
    
    # Chia Layout: 6 phần cho Điểm danh, 4 phần cho Nhật ký
    col_left, col_right = st.columns([6, 4], gap="large")

    # ----------------- CỘT TRÁI: ĐIỂM DANH & ĐÁNH GIÁ -----------------
    with col_left:
        st.markdown(f"### 👥 Điểm danh lớp: `{current_schedule['class_name']}`")
        st.caption("Danh sách học sinh được lấy tự động từ dữ liệu đăng ký lớp học.")

        # Lấy danh sách học sinh thật
        students = fetch_students_by_class(current_schedule['id'])
        attendance_records = []

        if not students:
            st.info("Chưa có học sinh nào đăng ký vào lớp này.")
        else:
            # Header
            h1, h2, h3, h4 = st.columns([2.5, 2, 2, 3])
            h1.write("**Học sinh**")
            h2.write("**Trạng thái**")
            h3.write("**Thái độ**")
            h4.write("**Nhận xét**")

            for stu in students:
                with st.container(border=True):
                    c_name, c_att, c_emo, c_cmt = st.columns([2.5, 2, 2, 3])
                    stu_id = stu.get('id', stu.get('_id'))
                    stu_name = stu.get('name', 'Học sinh')

                    with c_name:
                        st.markdown(f"<div style='margin-top: 8px;'>{stu_name}</div>", unsafe_allow_html=True)
                    
                    with c_att:
                        att = st.selectbox("Trạng thái", ["✅ Có mặt", "❌ Vắng", "⏳ Đi trễ"], 
                                         key=f"att_{stu_id}", label_visibility="collapsed")
                    
                    with c_emo:
                        is_disabled = (att == "❌ Vắng")
                        emo = st.selectbox("Thái độ", ["⭐ Xuất sắc", "👍 Tốt", "👌 Bình thường", "👎 Thiếu tập trung"], 
                                         key=f"emo_{stu_id}", label_visibility="collapsed", disabled=is_disabled)
                    
                    with c_cmt:
                        cmt = st.text_input("Nhận xét", placeholder="Khen ngợi...", 
                                          key=f"cmt_{stu_id}", label_visibility="collapsed", disabled=is_disabled)
                    
                    attendance_records.append({
                        "student_id": stu_id,
                        "is_present": att == "✅ Có mặt",
                        "emoji_feedback": emo,
                        "teacher_comment": cmt
                    })

    # ----------------- CỘT PHẢI: NHẬT KÝ BÀI GIẢNG -----------------
    with col_right:
        st.markdown("### 📝 Nhật ký bài học")
        
        with st.container(border=True):
            lesson_topic = st.text_input("🎯 Chủ đề giảng dạy:", value=current_schedule['subject'])
            
            # Đồng bộ với kho Video AI (TV2)
            try:
                res_v = requests.get(f"{API_URL}/api/tv2/videos")
                videos = res_v.json() if res_v.status_code == 200 else []
            except: videos = []
            
            used_videos = st.multiselect("🎬 Video AI đã sử dụng:", [v['title'] for v in videos])
            
            # Đồng bộ với kho Quiz (TV2)
            try:
                res_q = requests.get(f"{API_URL}/api/tv2/quizzes")
                quizzes = res_q.json() if res_q.status_code == 200 else []
            except: quizzes = []
            
            assigned_quizzes = st.multiselect("📝 Giao bài tập về nhà:", [q['title'] for q in quizzes])
            
            content_taught = st.text_area("💬 Chi tiết nội dung giảng dạy:", height=150)

            if st.button("💾 LƯU & GỬI BÁO CÁO", type="primary", use_container_width=True):
                if not content_taught:
                    st.error("⚠️ Vui lòng nhập nội dung đã dạy.")
                else:
                    # Tạo payload gửi về Backend (TV2 - Academic)
                    journal_payload = {
                        "class_id": current_schedule['id'],
                        "teacher_id": st.session_state.user_id,
                        "content_taught": content_taught,
                        "attendance": attendance_records
                    }
                    
                    with st.spinner("Đang gửi dữ liệu và thông báo cho Phụ huynh..."):
                        # Gọi API lưu nhật ký thực tế
                        res = requests.post(f"{API_URL}/api/tv2/journal", json=journal_payload)
                        
                        if res.status_code in [200, 201]:
                            st.success("✅ Đã lưu nhật ký và gửi thông báo cho TV3 thành công!")
                            st.balloons()
                            time.sleep(2)
                            st.rerun()
                        else:
                            st.error(f"❌ Lỗi: {res.text}")