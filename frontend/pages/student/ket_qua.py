import streamlit as st
import pandas as pd
import requests
import os
from utils.role_guard import require_role

# 1. Lính gác: Chỉ cho phép tài khoản học sinh truy cập trang này
require_role(["student"])

BACKEND_URL = st.session_state.get("api_url", "http://localhost:8000")

# ================= HÀM ĐỌC FILE CSS =================
def load_css(file_name):
    """
    Tự động tìm file CSS trong thư mục frontend/CSS/
    file_name: tên file kèm thư mục con, ví dụ 'student/ket_qua.css'
    """
    current_dir = os.path.dirname(os.path.abspath(__file__)) 
    css_root = os.path.abspath(os.path.join(current_dir, "../../CSS"))
    full_path = os.path.join(css_root, file_name)

    if os.path.exists(full_path):
        with open(full_path, "r", encoding="utf-8") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    else:
        st.warning(f"⚠️ Không tìm thấy file CSS tại: {full_path}")

# Tải CSS làm đẹp cho bảng điểm
load_css("student/student_global.css")
# Lấy cấu hình ngôn ngữ hiện hành từ session_state toàn cục (Mặc định là "vi")
lang = st.session_state.get("lang", "vi")

# ==========================================
# BỘ TỪ ĐIỂN SONG NGỮ CHI TIẾT CHO STUDENT KET_QUA
# ==========================================
STUDENT_REPORT_LABELS = {
    "vi": {
        "title": "📊 Bảng Điểm Cá Nhân",
        "subtitle": "Theo dõi sự tiến bộ của bạn qua từng bài kiểm tra và các kỳ thi nhé!",
        "sub_ai": "🤖 Phân Tích Từ Hệ Thống AI",
        "no_grades": "Hiện tại bạn chưa có điểm tổng kết nào được ghi nhận. Hãy cố gắng học tập nhé!",
        
        # Tiêu đề cột DataFrame đồng bộ với DB
        "col_subject": "Môn Học",
        "col_attend": "Chuyên Cần",
        "col_test": "TB Kiểm Tra",
        "col_midterm": "Giữa Kỳ",
        "col_final": "Cuối Kỳ",
        "col_total": "Tổng Kết",
        "col_rank": "Xếp Loại"
    },
    "en": {
        "title": "📊 My Report Card",
        "subtitle": "Track your academic growth and exam grades throughout the semester!",
        "sub_ai": "🤖 AI Insights & Recommendations",
        "no_grades": "No grades have been recorded for you yet. Keep up the good work!",
        
        # DataFrame Table Header Config
        "col_subject": "Subject",
        "col_attend": "Attendance",
        "col_test": "Avg Test",
        "col_midterm": "Midterm",
        "col_final": "Final",
        "col_total": "Final Grade",
        "col_rank": "Rank"
    }
}

# ================= LẤY THÔNG TIN ĐĂNG NHẬP =================
student_id = st.session_state.get("user_id")
token = st.session_state.get("access_token") or st.session_state.get("token")

if not student_id or not token:
    st.error("Vui lòng đăng nhập để xem điểm.")
    st.stop()

headers = {"Authorization": f"Bearer {token}"}

# ================= GỌI API LẤY ĐIỂM THẬT =================
@st.cache_data(ttl=30)
def get_my_real_grades(sid):
    try:
        res = requests.get(f"{API_URL}/api/tv2/grades/{sid}", headers=headers, timeout=5)
        if res.status_code == 200:
            return res.json()
    except Exception as e:
        st.error(f"Lỗi kết nối máy chủ: {e}")
    return []

real_grades = get_my_real_grades(student_id)

# ================= GIAO DIỆN CHÍNH =================
st.title(STUDENT_REPORT_LABELS[lang]["title"])
st.write(STUDENT_REPORT_LABELS[lang]["subtitle"])
st.divider()

if not real_grades:
    st.info(STUDENT_REPORT_LABELS[lang]["no_grades"])
else:
    # 1. Đóng gói dữ liệu thật vào DataFrame
    formatted_grades = []
    for g in real_grades:
        formatted_grades.append({
            STUDENT_REPORT_LABELS[lang]["col_subject"]: g.get("subject", "N/A"),
            STUDENT_REPORT_LABELS[lang]["col_attend"]: g.get("chuyen_can", 0),
            STUDENT_REPORT_LABELS[lang]["col_test"]: g.get("tb_kiem_tra", 0),
            STUDENT_REPORT_LABELS[lang]["col_midterm"]: g.get("giua_ky", 0),
            STUDENT_REPORT_LABELS[lang]["col_final"]: g.get("cuoi_ky", 0),
            STUDENT_REPORT_LABELS[lang]["col_total"]: g.get("tong_ket", 0),
            STUDENT_REPORT_LABELS[lang]["col_rank"]: g.get("xep_loai", "N/A")
        })
    
    df = pd.DataFrame(formatted_grades)
    
    # Dịch "Xếp loại" nếu ở chế độ tiếng Anh
    if lang == "en":
        rank_map = {"Giỏi": "Excellent", "Khá": "Good", "TB": "Average", "Yếu": "Poor"}
        df[STUDENT_REPORT_LABELS[lang]["col_rank"]] = df[STUDENT_REPORT_LABELS[lang]["col_rank"]].map(lambda x: rank_map.get(x, x))
    
    # Hiển thị bảng điểm
    st.dataframe(df, use_container_width=True, hide_index=True)
    st.divider()

    # 2. Phân tích AI linh động dựa trên dữ liệu thật
    st.subheader(STUDENT_REPORT_LABELS[lang]["sub_ai"])
    
    # Tìm môn cao điểm nhất và thấp điểm nhất
    best_subject = max(real_grades, key=lambda x: x.get("tong_ket", 0))
    weakest_subject = min(real_grades, key=lambda x: x.get("tong_ket", 10))
    
    if lang == "vi":
        ai_comment = (
            f"💡 **AI Nhận xét:** Xin chúc mừng, bạn đang học rất xuất sắc môn **{best_subject.get('subject')}** "
            f"với số điểm tổng kết là **{best_subject.get('tong_ket')}**! 🎉\n\n"
            f"Tuy nhiên, môn **{weakest_subject.get('subject')}** của bạn đang cần chú ý hơn một chút "
            f"(Điểm hiện tại: {weakest_subject.get('tong_ket')}). Hãy vào mục **Bài Tập AI** để ôn luyện thêm phần này, "
            f"vừa cải thiện điểm số vừa nhận thêm thật nhiều iKids Xu nhé! 🪙"
        )
    else:
        ai_comment = (
            f"💡 **AI Feedback:** Congratulations, you are performing excellently in **{best_subject.get('subject')}** "
            f"with a final grade of **{best_subject.get('tong_ket')}**! 🎉\n\n"
            f"However, your **{weakest_subject.get('subject')}** score requires a bit more attention "
            f"(Current score: {weakest_subject.get('tong_ket')}). Head over to the **AI Quizzes** section to practice more, "
            f"level up your scores, and earn lots of iKids Coins! 🪙"
        )
        
    st.info(ai_comment)