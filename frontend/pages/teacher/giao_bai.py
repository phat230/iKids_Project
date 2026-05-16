import streamlit as st
import requests
import os
from datetime import datetime, timedelta

st.set_page_config(page_title="Giao Bài Tập", page_icon="📤", layout="wide")

# ================= HÀM ĐỌC FILE CSS (SỬA LỖI ĐƯỜNG DẪN TUYỆT ĐỐI) =================
def load_css(file_name):
    """Tự động tìm file CSS trong thư mục frontend/CSS/"""
    # Lấy đường dẫn tuyệt đối đến thư mục chứa file giao_bai.py hiện tại
    current_dir = os.path.dirname(os.path.abspath(__file__)) # pages/teacher
    
    # Tìm đường dẫn đến thư mục CSS (lùi 2 cấp rồi vào CSS/)
    css_root = os.path.abspath(os.path.join(current_dir, "../../CSS"))
    full_path = os.path.join(css_root, file_name)

    if os.path.exists(full_path):
        with open(full_path, "r", encoding="utf-8") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    else:
        st.warning(f"⚠️ Không tìm thấy file CSS tại: {full_path}")

# Tải CSS làm đẹp (Truyền folder con teacher/)
load_css("teacher/giao_bai.css")

# ================= KẾT NỐI API BACKEND =================
API_URL_QUIZZES = "http://127.0.0.1:8000/api/tv2/quizzes"
API_URL_ASSIGNMENTS = "http://127.0.0.1:8000/api/tv2/assign-quiz"

def get_teacher_info():
    if "user_info" in st.session_state:
        info = st.session_state.user_info
        email = info.get("email", "khach@gmail.com")
        # Quét tên thật từ các key có thể có
        name = info.get("full_name", info.get("name", info.get("ho_ten", info.get("username", email.split('@')[0]))))
        return email, name
    return "khach@gmail.com", "Khách"

teacher_email, teacher_name = get_teacher_info()

@st.cache_data(ttl=5)
def fetch_quizzes_from_db():
    try:
        response = requests.get(API_URL_QUIZZES)
        if response.status_code == 200:
            return response.json()
        return []
    except:
        return []

st.title("Giao Bài Tập Cho Lớp")
st.write(f"Đang đăng nhập: **{teacher_name}**")

# Lấy dữ liệu từ DB
quizzes_db = fetch_quizzes_from_db()

# Lọc chỉ lấy những bộ đề do chính giáo viên này tạo
my_quizzes = [q for q in quizzes_db if q.get("author_email") == teacher_email or q.get("author") == teacher_email]

if not my_quizzes:
    st.warning("⚠️ Kho học liệu của bạn hiện chưa có bộ đề nào do chính bạn tạo!")
    st.info("Hãy sử dụng AI để tạo bộ đề trước khi giao bài cho lớp nhé.")
    st.page_link("pages/teacher/tao_quiz.py", label="👉 Đi tới trang Tạo Bài Tập AI", icon="🤖")

else:
    with st.container(border=True):
        st.subheader(" Giao Bài Tập Hôm Nay")
        
        quiz_dict = {q['title']: q.get('id') for q in my_quizzes}
        danh_sach_de = list(quiz_dict.keys())
        
        # Xử lý index mặc định nếu chuyển từ trang Kho học liệu
        default_index = 0
        if "selected_quiz_to_assign" in st.session_state:
            if st.session_state.selected_quiz_to_assign in danh_sach_de:
                default_index = danh_sach_de.index(st.session_state.selected_quiz_to_assign)
        
        selected_quiz_title = st.selectbox(" Chọn Bài Tập Giao Cho Lớp:", options=danh_sach_de, index=default_index)
        
        # Danh sách lớp (Giả lập do DB TV1 đang hoàn thiện)
        selected_classes = st.multiselect(" Chọn Lớp Nhận Bài:", ["Lớp Tiếng Anh T6", "Lớp Toán Tư Duy T7", "Lớp Năng khiếu M1"])
        
        col1, col2 = st.columns(2)
        with col1:
            deadline_date = st.date_input(" Hạn chót:", datetime.now() + timedelta(days=3))
        with col2:
            deadline_time = st.time_input(" Giờ khóa đề:", datetime.strptime("23:59", "%H:%M").time())
            
        note = st.text_area(" Lời Nhắn Cho Lớp:", placeholder="Ví dụ: Các con nhớ xem kỹ bài trước khi làm nhé!")

        if st.button(" XÁC NHẬN GIAO BÀI", type="primary", use_container_width=True):
            if not selected_classes:
                st.error("❌ Vui lòng chọn ít nhất 1 lớp để nhận bài!")
            else:
                selected_quiz_id = quiz_dict[selected_quiz_title]
                
                assign_payload = {
                    "quiz_id": selected_quiz_id,
                    "quiz_title": selected_quiz_title,
                    "teacher_id": teacher_email,
                    "class_id": ", ".join(selected_classes),
                    "deadline": f"{deadline_date} {deadline_time}",
                    "note": note
                }
                
                try:
                    res = requests.post(API_URL_ASSIGNMENTS, json=assign_payload)
                    if res.status_code in [200, 201]:
                        st.success(f"✅ Đã giao thành công bộ đề '{selected_quiz_title}'!")
                        st.info("🔔 Thông báo đã được gửi đến Phụ huynh và Học sinh.")
                        st.balloons()
                        
                        if "selected_quiz_to_assign" in st.session_state:
                            del st.session_state["selected_quiz_to_assign"]
                    else:
                        st.error(f"Lỗi hệ thống: {res.text}")
                except Exception as e:
                    st.error(f"Lỗi kết nối Backend: {e}")