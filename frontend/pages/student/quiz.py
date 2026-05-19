import streamlit as st
import requests
import time
import urllib.parse
import os

# ================= CRITICAL: CẤU HÌNH TRANG LUÔN ĐỂ ĐẦU FILE =================
st.set_page_config(page_title="Trạm Quiz AI", page_icon="📝", layout="wide")

# ================= HÀM ĐỌC FILE CSS (SỬA LỖI ĐƯỜNG DẪN) =================
def load_css(file_name):
    """
    Tự động tìm file CSS trong thư mục frontend/CSS/
    file_name: tên file kèm thư mục con, ví dụ 'student/quiz.css'
    """
    current_dir = os.path.dirname(os.path.abspath(__file__)) # frontend/pages/student
    css_root = os.path.abspath(os.path.join(current_dir, "../../CSS"))
    full_path = os.path.join(css_root, file_name)

    if os.path.exists(full_path):
        with open(full_path, "r", encoding="utf-8") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    else:
        st.warning(f"⚠️ Không tìm thấy file CSS tại: {full_path}")

# Tải CSS làm đẹp cho trang Quiz
load_css("student/quiz.css")

# Lấy cấu hình ngôn ngữ hiện hành từ session_state toàn cục (Mặc định là "vi")
lang = st.session_state.get("lang", "vi")

# ==========================================
# BỘ TỪ ĐIỂN SONG NGỮ CHI TIẾT CHO STUDENT QUIZ
# ==========================================
QUIZ_LABELS = {
    "vi": {
        "title": "📝 Trạm Quiz AI",
        "subtitle": "Hoàn thành các bài tập dưới đây để tích lũy EXP thăng hạng nhé!",
        "lbl_total_exp": "Tổng EXP của bạn:",
        "info_empty_quizzes": "✨ Hiện tại giáo viên chưa có bài tập nào. Bạn có thể nghỉ ngơi!",
        "lbl_questions_count": "Số câu:",
        "lbl_reward": "Phần thưởng:",
        "btn_completed": "✅ Đã hoàn thành",
        "btn_start": "▶ Bắt đầu làm",
        "btn_back_dashboard": "⬅️ Quay lại Bảng Điều Khiển",
        
        # Màn hình làm bài
        "btn_back_list": "⬅ Trở về danh sách bộ đề",
        "lbl_quiz_title": "Đề Bài:",
        "info_quiz_hint": "💡 Hãy đọc kỹ câu hỏi và chọn đáp án chính xác nhất. Cần tích đủ tất cả các câu mới có thể nộp bài.",
        "lbl_question_prefix": "Câu",
        "select_option_lbl": "Chọn đáp án:",
        "btn_submit_quiz": "🏆 Nộp Bài & Nhận Thưởng",
        
        # Thông báo phản hồi kết quả
        "err_unanswered": "⚠️ Bạn chưa chọn đáp án cho tất cả các câu. Vui lòng kéo lên kiểm tra và điền đầy đủ trước khi nộp!",
        "err_save_toast": "⚠️ Có lỗi khi lưu dữ liệu lên server:",
        "success_grading": "🎉 Chấm xong! Bạn làm đúng {}/{} câu. **Điểm: {}/10**",
        "info_exp_reward": "🚀 Chúc mừng! Bạn nhận được +{} EXP! Đang quay lại trang chủ...",
        "err_connection": "⚠️ Mất kết nối đến Backend Database. Hãy đảm bảo Uvicorn đang chạy! Chi tiết lỗi:"
    },
    "en": {
        "title": "📝 AI Quiz Station",
        "subtitle": "Complete the practice quizzes below to accumulate EXP and level up your rank! 🏆",
        "lbl_total_exp": "Your Current EXP:",
        "info_empty_quizzes": "✨ There are currently no active homework quizzes assigned. You can take a break!",
        "lbl_questions_count": "Questions:",
        "lbl_reward": "Reward Value:",
        "btn_completed": "✅ Completed",
        "btn_start": "▶ Start Quiz",
        "btn_back_dashboard": "⬅️ Back to Dashboard",
        
        # In-quiz screen
        "btn_back_list": "⬅ Back to Quiz List",
        "lbl_quiz_title": "Quiz Title:",
        "info_quiz_hint": "💡 Please read each question carefully and select the most accurate option. All questions must be answered to submit.",
        "lbl_question_prefix": "Question",
        "select_option_lbl": "Select an answer:",
        "btn_submit_quiz": "🏆 Submit & Claim Rewards",
        
        # Response feedbacks
        "err_unanswered": "⚠️ You haven't answered all the questions yet. Please scroll up to verify and complete all fields before submitting!",
        "err_save_toast": "⚠️ Error occurred while synchronizing metrics to server data:",
        "success_grading": "🎉 Grading completed! You got {}/{} correct. **Score: {}/10**",
        "info_exp_reward": "🚀 Congratulations! You earned +{} EXP! Navigating back to main deck...",
        "err_connection": "⚠️ Unable to establish a connection to Backend Database. Please verify that Uvicorn is active! Error details:"
    }
}

# ================= HÀM LẤY TÊN USER =================
def get_current_username():
    """Tự động tìm tên tài khoản thật từ hệ thống đăng nhập"""
    if "username" in st.session_state and st.session_state.username: return st.session_state.username
    if "full_name" in st.session_state and st.session_state.full_name: return st.session_state.full_name
    if "user_info" in st.session_state and isinstance(st.session_state.user_info, dict):
        return st.session_state.user_info.get("full_name", st.session_state.user_info.get("name", "Student"))
    return "Student"

real_name = get_current_username()
encoded_name = urllib.parse.quote(real_name)

# ================= ĐỒNG BỘ PROFILE TỪ DATABASE =================
try:
    prof_res = requests.get(f"http://127.0.0.1:8000/api/tv2/student/{encoded_name}/profile", timeout=5)
    if prof_res.status_code == 200:
        st.session_state.student_profile = prof_res.json()
    else:
        st.session_state.student_profile = {"username": real_name, "exp": 0, "completed_tasks": []}
except Exception:
    if "student_profile" not in st.session_state:
        st.session_state.student_profile = {"username": real_name, "exp": 0, "completed_tasks": []}

# ================= GỌI API BACKEND ĐỂ LẤY DANH SÁCH BÀI TẬP =================
try:
    response = requests.get("http://127.0.0.1:8000/api/tv2/quizzes", timeout=5)
    if response.status_code == 200:
        saved_quizzes = response.json()
    else:
        saved_quizzes = []
except Exception as e:
    st.error(f"{QUIZ_LABELS[lang]['err_connection']} {e}")
    saved_quizzes = []

if "selected_quiz" not in st.session_state:
    st.session_state.selected_quiz = None

# -------------------------------------------------------------------------
# MÀN HÌNH 1: DANH SÁCH BỘ ĐỀ
# -------------------------------------------------------------------------
if st.session_state.selected_quiz is None:
    st.title(QUIZ_LABELS[lang]["title"])
    st.write(QUIZ_LABELS[lang]["subtitle"])
    
    st.markdown(f"🏅 **{QUIZ_LABELS[lang]['lbl_total_exp']}** `{st.session_state.student_profile.get('exp', 0)} EXP`")

    if not saved_quizzes:
        st.info(QUIZ_LABELS[lang]["info_empty_quizzes"])
    else:
        for i, q in enumerate(saved_quizzes):
            quiz_id = q.get('id', f"quiz_backup_id_{i}")
            is_completed = quiz_id in st.session_state.student_profile.get('completed_tasks', [])
            
            with st.container():
                col_info, col_btn = st.columns([4, 1])
                with col_info:
                    st.markdown(f"""
                    <div class="quiz-card">
                        <div class="quiz-title"> {q.get('title', 'Bài tập chưa có tên' if lang == 'vi' else 'Untitled Quiz')}</div>
                        <div class="quiz-meta">{QUIZ_LABELS[lang]['lbl_questions_count']} {len(q.get('questions', []))} | {QUIZ_LABELS[lang]['lbl_reward']} +50 EXP</div>
                    </div>
                    """, unsafe_allow_html=True)
                
                with col_btn:
                    st.write("") 
                    if is_completed:
                        st.button(QUIZ_LABELS[lang]["btn_completed"], key=f"done_{quiz_id}", disabled=True, use_container_width=True)
                    else:
                        if st.button(QUIZ_LABELS[lang]["btn_start"], key=f"start_{quiz_id}", type="primary", use_container_width=True):
                            st.session_state.selected_quiz = q
                            st.rerun()

    st.divider()
    if st.button(QUIZ_LABELS[lang]["btn_back_dashboard"]):
        st.switch_page("pages/student/dashboard.py")

# -------------------------------------------------------------------------
# MÀN HÌNH 2: GIAO DIỆN LÀM BÀI FULL MÀN HÌNH
# -------------------------------------------------------------------------
else:
    q = st.session_state.selected_quiz
    quiz_id = q.get('id', 'temp_id')
    questions = q.get('questions', [])
    num_questions = len(questions)

    if st.button(QUIZ_LABELS[lang]["btn_back_list"]):
        st.session_state.selected_quiz = None
        st.rerun()

    st.markdown(f"## 📝 {QUIZ_LABELS[lang]['lbl_quiz_title']} {q.get('title')}")
    st.info(QUIZ_LABELS[lang]["info_quiz_hint"])

    with st.form(key=f"full_quiz_form_{quiz_id}"):
        user_answers = {}
        for idx, question in enumerate(questions):
            st.markdown(f"**{QUIZ_LABELS[lang]['lbl_question_prefix']} {idx + 1}: {question['question']}**")
            
            user_answers[idx] = st.radio(
                label=QUIZ_LABELS[lang]["select_option_lbl"], 
                options=question['options'], 
                key=f"ans_{quiz_id}_{idx}", 
                index=None,
                label_visibility="collapsed"
            )
            st.write("---")
        
        submit_btn = st.form_submit_button(QUIZ_LABELS[lang]["btn_submit_quiz"], type="primary", use_container_width=True)
        
        if submit_btn:
            if None in user_answers.values():
                st.error(QUIZ_LABELS[lang]["err_unanswered"])
            else:
                correct_count = sum(1 for idx, question in enumerate(questions) if user_answers[idx] == question['correct_answer'])
                score = round((correct_count / num_questions) * 10, 1) if num_questions > 0 else 0
                earned_exp = 50 + (correct_count * 10)
                
                # BẮN API XUỐNG DATABASE ĐỂ LƯU KẾT QUẢ VĨNH VIỄN
                submit_payload = {
                    "quiz_id": quiz_id,
                    "exp_earned": earned_exp,
                    "score": score
                }
                try:
                    requests.post(f"http://127.0.0.1:8000/api/tv2/student/{encoded_name}/submit-quiz", json=submit_payload, timeout=5)
                except Exception as e:
                    st.toast(f"{QUIZ_LABELS[lang]['err_save_toast']} {e}")

                st.session_state.student_profile['exp'] += earned_exp
                st.session_state.student_profile['completed_tasks'].append(quiz_id)
                
                st.success(QUIZ_LABELS[lang]["success_grading"].format(correct_count, num_questions, score))
                st.balloons()
                st.info(QUIZ_LABELS[lang]["info_exp_reward"].format(earned_exp))
                
                time.sleep(3)
                st.session_state.selected_quiz = None
                st.rerun()