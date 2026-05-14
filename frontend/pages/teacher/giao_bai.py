import streamlit as st
import requests
from datetime import datetime, timedelta

st.set_page_config(page_title="Giao Bài Tập", page_icon="📤")

# ================= KẾT NỐI API BACKEND =================
API_URL_QUIZZES = "http://127.0.0.1:8000/api/tv2/quizzes"
API_URL_ASSIGNMENTS = "http://127.0.0.1:8000/api/tv2/assign-quiz"

# Hàm lấy thông tin giáo viên đang đăng nhập
def get_teacher_info():
    if "user_info" in st.session_state:
        info = st.session_state.user_info
        email = info.get("email", "khach@gmail.com")
        name = info.get("full_name", info.get("name", info.get("ho_ten", info.get("username", email.split('@')[0]))))
        return email, name
    return "khach@gmail.com", "Khách"

teacher_email, teacher_name = get_teacher_info()

# GỌI API LẤY DANH SÁCH BỘ ĐỀ TỪ DATABASE THẬT
@st.cache_data(ttl=5) # Cache 5 giây để tránh gọi API liên tục
def fetch_quizzes_from_db():
    try:
        response = requests.get(API_URL_QUIZZES)
        if response.status_code == 200:
            return response.json()
        return []
    except:
        return []

st.title("📤 Giao Bài Tập Cho Lớp")
st.write(f"Đang đăng nhập: **{teacher_name}**")

# Lấy dữ liệu từ DB
quizzes_db = fetch_quizzes_from_db()

# Lọc chỉ lấy những bộ đề DO CHÍNH GIÁO VIÊN NÀY TẠO (Khóa bảo mật phân quyền)
my_quizzes = [q for q in quizzes_db if q.get("author_email") == teacher_email or q.get("author") == teacher_email]

# NẾU CHƯA CÓ ĐỀ NÀO TRONG KHO
if len(my_quizzes) == 0:
    st.warning("⚠️ Kho học liệu của bạn hiện chưa có bộ đề nào do chính bạn tạo!")
    st.info("Hãy sử dụng AI để tạo bộ đề trước khi giao bài cho lớp nhé.")
    st.page_link("pages/teacher/tao_quiz.py", label="👉 Đi tới trang Tạo Bài Tập AI", icon="🤖")

# NẾU ĐÃ CÓ ĐỀ TRONG KHO THÌ HIỆN FORM
else:
    with st.container(border=True):
        st.subheader("⚙️ Cấu hình giao bài")
        
        # Tạo từ điển map ID với Tên bộ đề để lưu Database cho chuẩn
        quiz_dict = {q['title']: q.get('id') for q in my_quizzes}
        danh_sach_de = list(quiz_dict.keys())
        
        # Nếu được chuyển sang từ nút "Giao Bài Này" bên trang Kho học liệu
        default_index = 0
        if "selected_quiz_to_assign" in st.session_state:
            if st.session_state.selected_quiz_to_assign in danh_sach_de:
                default_index = danh_sach_de.index(st.session_state.selected_quiz_to_assign)
        
        selected_quiz_title = st.selectbox("📝 Chọn bộ đề từ kho của bạn:", options=danh_sach_de, index=default_index)
        
        # Giả lập danh sách lớp của TV1 (Do TV1 chưa làm xong DB)
        selected_classes = st.multiselect("👥 Chọn lớp nhận bài:", ["Lớp Tiếng Anh T6", "Lớp Toán Tư Duy T7", "Lớp Năng khiếu M1"])
        
        col1, col2 = st.columns(2)
        with col1:
            deadline_date = st.date_input("📅 Hạn chót:", datetime.now() + timedelta(days=3))
        with col2:
            deadline_time = st.time_input("⏰ Giờ khóa đề:", datetime.strptime("23:59", "%H:%M").time())
            
        note = st.text_area("💬 Lời nhắn cho học sinh:", placeholder="Ví dụ: Các con nhớ xem kỹ bài trước khi làm nhé!")

        if st.button("🚀 XÁC NHẬN GIAO BÀI", type="primary", use_container_width=True):
            if not selected_classes:
                st.error("❌ Vui lòng chọn ít nhất 1 lớp để nhận bài!")
            else:
                # Lấy ID của bộ đề đã chọn
                selected_quiz_id = quiz_dict[selected_quiz_title]
                
                # Gói dữ liệu gửi xuống Backend
                assign_payload = {
                    "quiz_id": selected_quiz_id,
                    "quiz_title": selected_quiz_title,
                    "teacher_id": teacher_email, # <--- ĐÃ SỬA THÀNH teacher_id Ở ĐÂY NÈ
                    "class_id": ", ".join(selected_classes),
                    "deadline": f"{deadline_date} {deadline_time}",
                    "note": note
                }
                
                try:
                    # Bắn API lưu thông tin giao bài vào Database
                    res = requests.post(API_URL_ASSIGNMENTS, json=assign_payload)
                    if res.status_code in [200, 201]:
                        st.success(f"✅ Đã giao thành công bộ đề '{selected_quiz_title}' cho {len(selected_classes)} lớp!")
                        st.info("🔔 Thông báo đã được gửi đến App của Phụ huynh và Học sinh (TV3).")
                        st.balloons()
                        # Xóa state đã giao sau khi hoàn tất
                        if "selected_quiz_to_assign" in st.session_state:
                            del st.session_state["selected_quiz_to_assign"]
                    else:
                        st.error(f"Lỗi hệ thống: {res.text}")
                except Exception as e:
                    st.error(f"Lỗi kết nối Backend: {e}")