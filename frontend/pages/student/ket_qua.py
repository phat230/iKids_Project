import streamlit as st
import pandas as pd
import os
from utils.role_guard import require_role

# 1. Lính gác: Chỉ cho phép tài khoản học sinh truy cập trang này
require_role(["student"])

# ================= HÀM ĐỌC FILE CSS (SỬA LỖI ĐƯỜNG DẪN) =================
def load_css(file_name):
    """
    Tự động tìm file CSS trong thư mục frontend/CSS/
    file_name: tên file kèm thư mục con, ví dụ 'student/ket_qua.css'
    """
    # Lấy đường dẫn tuyệt đối đến thư mục chứa file ket_qua.py hiện tại
    current_dir = os.path.dirname(os.path.abspath(__file__)) # frontend/pages/student
    
    # Tìm đường dẫn đến thư mục CSS (lùi 2 cấp rồi vào CSS/)
    css_root = os.path.abspath(os.path.join(current_dir, "../../CSS"))
    full_path = os.path.join(css_root, file_name)

    if os.path.exists(full_path):
        with open(full_path, "r", encoding="utf-8") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    else:
        st.warning(f"⚠️ Không tìm thấy file CSS tại: {full_path}")

# Tải CSS làm đẹp cho bảng điểm
load_css("student/ket_qua.css")

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
        "ai_comment": "💡 **AI Nhận xét:** Bạn đang làm rất tốt môn Kỹ Năng Sống và Anh Văn! Tuy nhiên, điểm môn Khoa Học đang hơi thấp. Hãy vào mục **Bài Tập AI** để ôn luyện thêm phần này, vừa cải thiện điểm số vừa nhận thêm thật nhiều iKids Xu nhé!",
        
        # Tiêu đề cột DataFrame
        "col_subject": "Môn học",
        "col_midterm": "Điểm Giữa Kỳ",
        "col_final": "Điểm Cuối Kỳ",
        "col_grade": "Đánh giá",
        
        # Dữ liệu nội mảng động
        "sub_math": "Toán Tư Duy",
        "sub_english": "Anh Văn",
        "sub_science": "Khoa Học",
        "sub_skills": "Kỹ Năng Sống",
        "not_available": "Chưa có",
        "grade_good": "Khá",
        "grade_excellent": "Tốt",
        "grade_needs_improvement": "Cần cố gắng",
        "grade_outstanding": "Xuất sắc"
    },
    "en": {
        "title": "📊 My Report Card",
        "subtitle": "Track your academic growth and exam grades throughout the semester!",
        "sub_ai": "🤖 AI Insights & Recommendations",
        "ai_comment": "💡 **AI Feedback:** You are performing excellently in Life Skills and English! However, your Science score has room for improvement. Head over to the **AI Quizzes** section to practice more, level up your scores, and earn lots of iKids Coins! 🪙",
        
        # DataFrame Table Header Config
        "col_subject": "Course Subject",
        "col_midterm": "Midterm Grade",
        "col_final": "Final Exam Grade",
        "col_grade": "Performance Evaluation",
        
        # Inner array cell items data mapped
        "sub_math": "Critical Thinking Math",
        "sub_english": "English Language",
        "sub_science": "Science Experiments",
        "sub_skills": "Essential Life Skills",
        "not_available": "N/A",
        "grade_good": "Good",
        "grade_excellent": "Very Good",
        "grade_needs_improvement": "Needs Improvement",
        "grade_outstanding": "Outstanding"
    }
}

# ================= GIAO DIỆN CHÍNH =================
st.title(STUDENT_REPORT_LABELS[lang]["title"])
st.write(STUDENT_REPORT_LABELS[lang]["subtitle"])
st.divider()

# 2. Dữ liệu mảng học thuật thích ứng linh hoạt theo ngôn ngữ hiển thị
data = {
    STUDENT_REPORT_LABELS[lang]["col_subject"]: [
        STUDENT_REPORT_LABELS[lang]["sub_math"], 
        STUDENT_REPORT_LABELS[lang]["sub_english"], 
        STUDENT_REPORT_LABELS[lang]["sub_science"], 
        STUDENT_REPORT_LABELS[lang]["sub_skills"]
    ],
    STUDENT_REPORT_LABELS[lang]["col_midterm"]: [8.5, 9.0, 7.5, 10.0],
    STUDENT_REPORT_LABELS[lang]["col_final"]: [
        STUDENT_REPORT_LABELS[lang]["not_available"], 
        STUDENT_REPORT_LABELS[lang]["not_available"], 
        STUDENT_REPORT_LABELS[lang]["not_available"], 
        STUDENT_REPORT_LABELS[lang]["not_available"]
    ],
    STUDENT_REPORT_LABELS[lang]["col_grade"]: [
        STUDENT_REPORT_LABELS[lang]["grade_good"], 
        STUDENT_REPORT_LABELS[lang]["grade_excellent"], 
        STUDENT_REPORT_LABELS[lang]["grade_needs_improvement"], 
        STUDENT_REPORT_LABELS[lang]["grade_outstanding"]
    ]
}

# 3. Hiển thị bảng dữ liệu đẹp mắt (Tự động thích ứng đầu cột dynamic)
df = pd.DataFrame(data)
st.dataframe(df, use_container_width=True, hide_index=True)

st.divider()

# 4. Góc phân tích thông minh của AI (Smart Recommendation)
st.subheader(STUDENT_REPORT_LABELS[lang]["sub_ai"])
st.info(STUDENT_REPORT_LABELS[lang]["ai_comment"])