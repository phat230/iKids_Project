import streamlit as st
import requests
import os
from datetime import datetime, timedelta

# ================= CRITICAL: CẤU HÌNH TRANG LUÔN ĐỂ ĐẦU FILE =================
st.set_page_config(page_title="Giao Bài Tập", page_icon="📤", layout="wide")

# ================= HÀM ĐỌC FILE CSS =================
def load_css(file_name):
    current_dir = os.path.dirname(os.path.abspath(__file__))
    css_root = os.path.abspath(os.path.join(current_dir, "../../CSS"))
    full_path = os.path.join(css_root, file_name)

    if os.path.exists(full_path):
        with open(full_path, "r", encoding="utf-8") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    else:
        st.warning(f"⚠️ Không tìm thấy file CSS tại: {full_path}")

load_css("teacher/teacher_global.css")

# ĐÃ SỬA: Cấu hình URL động
BACKEND_URL = st.session_state.get("api_url", "http://localhost:8000")
API_TV2 = f"{BACKEND_URL}/api/tv2"
lang = st.session_state.get("lang", "vi")

# ================= BỘ TỪ ĐIỂN SONG NGỮ =================
ASSIGN_LABELS = {
    "vi": {
        "title": "📤 Giao Bài Tập Cho Lớp",
        "logined_as": "Đang đăng nhập: **{}**",
        "warn_no_quiz": "⚠️ Kho học liệu của bạn hiện chưa có bộ đề nào do chính bạn tạo!",
        "info_go_create": "Hãy sử dụng AI để tạo bộ đề trước khi giao bài cho lớp nhé.",
        "btn_go_to_create": "👉 Đi tới trang Tạo Bài Tập AI",
        "sub_assign": "🚀 Giao Bài Tập Hôm Nay",
        "select_quiz": "Chọn Bài Tập Giao Cho Lớp:",
        "select_class": "Chọn Lớp Nhận Bài:",
        "lbl_deadline": "Hạn chót:",
        "lbl_time": "Giờ khóa đề:",
        "lbl_note": "Lời Nhắn Cho Lớp:",
        "note_placeholder": "Ví dụ: Các con nhớ xem kỹ bài trước khi làm nhé!",
        "btn_submit": "XÁC NHẬN GIAO BÀI",
        "err_no_class": "❌ Vui lòng chọn ít nhất 1 lớp để nhận bài!",
        "success_msg": "✅ Đã giao thành công bộ đề '{}'!",
        "info_notif": "🔔 Thông báo đã được gửi đến Phụ huynh và Học sinh.",
        "err_backend": "Lỗi hệ thống:",
        "err_connection": "Lỗi kết nối Backend:"
    },
    "en": {
        "title": "📤 Assign Homework & Quizzes",
        "logined_as": "Logged in as: **{}**",
        "warn_no_quiz": "⚠️ Your personal library does not contain any quizzes created by you!",
        "info_go_create": "Please use the AI Quiz Generator to create content before assigning.",
        "btn_go_to_create": "👉 Go to AI Quiz Generator",
        "sub_assign": "🚀 Assign Homework Today",
        "select_quiz": "Select Quiz to Assign:",
        "select_class": "Select Classes:",
        "lbl_deadline": "Deadline Date:",
        "lbl_time": "Deadline Time:",
        "lbl_note": "Message to Class:",
        "note_placeholder": "e.g., Remember to review the lesson before starting!",
        "btn_submit": "CONFIRM ASSIGNMENT",
        "err_no_class": "❌ Please select at least one class to assign the homework!",
        "success_msg": "✅ Successfully assigned the quiz: '{}'!",
        "info_notif": "🔔 Notifications have been dispatched to parents and students.",
        "err_backend": "System error:",
        "err_connection": "Backend connection failure:"
    }
}

# ================= KẾT NỐI API BACKEND =================
# ĐÃ SỬA: Dùng API_TV2
API_URL_QUIZZES = f"{API_TV2}/quizzes"
API_URL_ASSIGNMENTS = f"{API_TV2}/assign-quiz"

def get_teacher_info():
    if "user_info" in st.session_state:
        info = st.session_state.user_info
        email = info.get("email", "khach@gmail.com")
        name = info.get("full_name", info.get("name", info.get("ho_ten", info.get("username", email.split('@')[0]))))
        return email, name
    return "khach@gmail.com", "Khách"

teacher_email, teacher_name = get_teacher_info()

@st.cache_data(ttl=5)
def fetch_quizzes_from_db():
    try:
        response = requests.get(API_URL_QUIZZES)
        return response.json() if response.status_code == 200 else []
    except:
        return []

st.title(ASSIGN_LABELS[lang]["title"])
st.write(ASSIGN_LABELS[lang]["logined_as"].format(teacher_name))

quizzes_db = fetch_quizzes_from_db()
my_quizzes = [q for q in quizzes_db if q.get("author_email") == teacher_email or q.get("author") == teacher_email]

if not my_quizzes:
    st.warning(ASSIGN_LABELS[lang]["warn_no_quiz"])
    st.info(ASSIGN_LABELS[lang]["info_go_create"])
    st.page_link("pages/teacher/tao_quiz.py", label=ASSIGN_LABELS[lang]["btn_go_to_create"], icon="🤖")

else:
    with st.container(border=True):
        st.subheader(ASSIGN_LABELS[lang]["sub_assign"])
        
        quiz_dict = {q['title']: q.get('id') for q in my_quizzes}
        danh_sach_de = list(quiz_dict.keys())
        
        default_index = 0
        if "selected_quiz_to_assign" in st.session_state:
            if st.session_state.selected_quiz_to_assign in danh_sach_de:
                default_index = danh_sach_de.index(st.session_state.selected_quiz_to_assign)
        
        selected_quiz_title = st.selectbox(ASSIGN_LABELS[lang]["select_quiz"], options=danh_sach_de, index=default_index)
        selected_classes = st.multiselect(ASSIGN_LABELS[lang]["select_class"], ["Lớp Tiếng Anh T6", "Lớp Toán Tư Duy T7", "Lớp Năng khiếu M1"])
        
        col1, col2 = st.columns(2)
        with col1:
            deadline_date = st.date_input(ASSIGN_LABELS[lang]["lbl_deadline"], datetime.now() + timedelta(days=3))
        with col2:
            deadline_time = st.time_input(ASSIGN_LABELS[lang]["lbl_time"], datetime.strptime("23:59", "%H:%M").time())
            
        note = st.text_area(ASSIGN_LABELS[lang]["lbl_note"], placeholder=ASSIGN_LABELS[lang]["note_placeholder"])

        if st.button(ASSIGN_LABELS[lang]["btn_submit"], type="primary", use_container_width=True):
            if not selected_classes:
                st.error(ASSIGN_LABELS[lang]["err_no_class"])
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
                        st.success(ASSIGN_LABELS[lang]["success_msg"].format(selected_quiz_title))
                        st.info(ASSIGN_LABELS[lang]["info_notif"])
                        st.balloons()
                        if "selected_quiz_to_assign" in st.session_state:
                            del st.session_state["selected_quiz_to_assign"]
                    else:
                        st.error(f"{ASSIGN_LABELS[lang]['err_backend']} {res.text}")
                except Exception as e:
                    st.error(f"{ASSIGN_LABELS[lang]['err_connection']} {e}")