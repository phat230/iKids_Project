import streamlit as st
import requests
import time
import urllib.parse
import os
import pandas as pd

# ================= CRITICAL: CẤU HÌNH TRANG LUÔN ĐỂ ĐẦU FILE =================
st.set_page_config(page_title="Trạm Quiz AI", page_icon="📝", layout="wide")

# ================= HÀM ĐỌC FILE CSS =================
def load_css(file_name):
    current_dir = os.path.dirname(os.path.abspath(__file__)) 
    css_root = os.path.abspath(os.path.join(current_dir, "../../CSS"))
    full_path = os.path.join(css_root, file_name)

    if os.path.exists(full_path):
        with open(full_path, "r", encoding="utf-8") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

load_css("student/student_global.css")
lang = st.session_state.get("lang", "vi")

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
        "btn_sync": "🔄 Làm mới dữ liệu",
        "btn_back_dashboard": "⬅️ Quay lại Bảng Điều Khiển",
        "btn_back_list": "⬅ Trở về danh sách bộ đề",
        "lbl_quiz_title": "Đề Bài:",
        "info_quiz_hint": "💡 Hãy đọc kỹ câu hỏi và chọn đáp án chính xác nhất. Cần tích đủ tất cả các câu mới có thể nộp bài.",
        "lbl_question_prefix": "Câu",
        "select_option_lbl": "Chọn đáp án:",
        "btn_submit_quiz": "🏆 Nộp Bài & Nhận Thưởng",
        "err_unanswered": "⚠️ Bạn chưa chọn đáp án cho tất cả các câu. Vui lòng kéo lên kiểm tra!",
        "err_duplicate": "⛔ Bạn đã hoàn thành bài tập này rồi! Không thể nhận điểm hai lần.",
        "err_save_toast": "⚠️ Có lỗi khi lưu dữ liệu lên server:",
        "success_grading": "🎉 Chấm xong! Bạn làm đúng {}/{} câu. **Điểm: {}/10**",
        "info_exp_reward": "🚀 Chúc mừng! Bạn nhận được +{} EXP!",
        "err_connection": "⚠️ Mất kết nối đến Backend Database.",
        "chart_title": "📊 Biểu Đồ Kết Quả Làm Bài",
        "btn_finish_review": "Hoàn Tất & Quay Lại",
        "stat_progress": "📈 Tiến Độ Hoàn Thành Bài Tập"
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
        "btn_sync": "🔄 Refresh Data",
        "btn_back_dashboard": "⬅️ Back to Dashboard",
        "btn_back_list": "⬅ Back to Quiz List",
        "lbl_quiz_title": "Quiz Title:",
        "info_quiz_hint": "💡 Please read question carefully.",
        "lbl_question_prefix": "Question",
        "select_option_lbl": "Select an answer:",
        "btn_submit_quiz": "🏆 Submit",
        "err_unanswered": "⚠️ You haven't answered all the questions yet!",
        "err_duplicate": "⛔ You have already completed this quiz!",
        "err_save_toast": "⚠️ Error occurred:",
        "success_grading": "🎉 Grading completed! You got {}/{} correct. **Score: {}/10**",
        "info_exp_reward": "🚀 Congratulations! You earned +{} EXP!",
        "err_connection": "⚠️ Unable to establish a connection.",
        "chart_title": "📊 Quiz Result Analysis",
        "btn_finish_review": "Finish & Return",
        "stat_progress": "📈 Task Completion Progress"
    }
}

# ================= HÀM LẤY ĐỊNH DANH (ÉP DÙNG ID ĐỘC NHẤT) =================
def get_current_username():
    if "user_id" in st.session_state and st.session_state.user_id:
        return str(st.session_state.user_id)
        
    if "user_info" in st.session_state and isinstance(st.session_state.user_info, dict):
        return str(st.session_state.user_info.get("id", st.session_state.user_info.get("email", "Student")))
    
    if "email" in st.session_state and st.session_state.email: return st.session_state.email
    return "Student"

real_name = get_current_username()
encoded_name = urllib.parse.quote(real_name)

# ================= HÀM ĐỒNG BỘ MẠNH =================
def fetch_latest_data():
    try:
        prof_res = requests.get(f"http://127.0.0.1:8000/api/tv2/student/{encoded_name}/profile", timeout=5)
        if prof_res.status_code == 200:
            st.session_state.student_profile = prof_res.json()
        else:
            st.session_state.student_profile = {"username": real_name, "exp": 0, "completed_tasks": []}
    except:
        st.session_state.student_profile = {"username": real_name, "exp": 0, "completed_tasks": []}

    try:
        quiz_res = requests.get("http://127.0.0.1:8000/api/tv2/quizzes", timeout=5)
        if quiz_res.status_code == 200:
            quizzes = quiz_res.json()
            for i, q in enumerate(quizzes):
                if 'id' not in q or not q['id']:
                    q['id'] = f"quiz_backup_id_{i}"
            st.session_state.all_quizzes = quizzes
        else:
            st.session_state.all_quizzes = []
    except:
        st.session_state.all_quizzes = []

if "last_logged_in_user" not in st.session_state or st.session_state.last_logged_in_user != encoded_name:
    fetch_latest_data()
    st.session_state.last_logged_in_user = encoded_name 
elif "student_profile" not in st.session_state or "all_quizzes" not in st.session_state:
    fetch_latest_data()

if "selected_quiz" not in st.session_state:
    st.session_state.selected_quiz = None

if "quiz_result_view" not in st.session_state:
    st.session_state.quiz_result_view = None

# -------------------------------------------------------------------------
# MÀN HÌNH 1: DANH SÁCH BỘ ĐỀ & TIẾN ĐỘ
# -------------------------------------------------------------------------
if st.session_state.selected_quiz is None and st.session_state.quiz_result_view is None:
    st.title(QUIZ_LABELS[lang]["title"])
    st.write(QUIZ_LABELS[lang]["subtitle"])
    
    col_exp, col_sync = st.columns([5, 1])
    with col_exp:
        st.markdown(f"🏅 **{QUIZ_LABELS[lang]['lbl_total_exp']}** `{st.session_state.student_profile.get('exp', 0)} EXP`")
    with col_sync:
        if st.button(QUIZ_LABELS[lang]["btn_sync"], use_container_width=True, type="secondary"):
            fetch_latest_data() 
            st.rerun()

    saved_quizzes = st.session_state.get('all_quizzes', [])
    completed_list = st.session_state.student_profile.get('completed_tasks', [])
    
    # Biểu đồ Tiến độ hoàn thành
    if saved_quizzes:
        st.write("---")
        st.subheader(QUIZ_LABELS[lang]["stat_progress"])
        total_q = len(saved_quizzes)
        done_q = len([q for q in saved_quizzes if q['id'] in completed_list])
        progress_pct = int((done_q / total_q) * 100) if total_q > 0 else 0
        
        st.progress(progress_pct / 100, text=f"{progress_pct}% ({done_q}/{total_q})")
        st.write("---")

    if not saved_quizzes:
        st.info(QUIZ_LABELS[lang]["info_empty_quizzes"])
    else:
        for q in saved_quizzes:
            quiz_id = q['id']
            is_completed = quiz_id in completed_list
            
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
# MÀN HÌNH 2: GIAO DIỆN XEM KẾT QUẢ BÀI TẬP BẰNG SƠ ĐỒ TRỰC QUAN
# -------------------------------------------------------------------------
elif st.session_state.quiz_result_view is not None:
    result_data = st.session_state.quiz_result_view
    
    st.title(QUIZ_LABELS[lang]["chart_title"])
    st.success(QUIZ_LABELS[lang]["success_grading"].format(result_data['correct'], result_data['total'], result_data['score']))
    st.info(QUIZ_LABELS[lang]["info_exp_reward"].format(result_data['exp']))
    st.balloons()
    
    st.divider()
    
    # Sơ đồ cột thể hiện tỷ lệ Đúng/Sai
    chart_df = pd.DataFrame({
        "Kết quả": ["Câu Đúng" if lang == "vi" else "Correct", "Câu Sai" if lang == "vi" else "Incorrect"],
        "Số lượng": [result_data['correct'], result_data['total'] - result_data['correct']]
    })
    
    c1, c2 = st.columns([1, 2])
    with c1:
        st.metric("Điểm Số", f"{result_data['score']}/10")
        st.metric("Số câu đúng", f"{result_data['correct']}/{result_data['total']}")
        st.metric("EXP nhận được", f"+{result_data['exp']} ⭐")
    with c2:
        st.bar_chart(chart_df.set_index("Kết quả"), color=["#4CAF50"])

    st.divider()
    if st.button(QUIZ_LABELS[lang]["btn_finish_review"], type="primary", use_container_width=True):
        st.session_state.quiz_result_view = None
        fetch_latest_data() 
        st.rerun()

# -------------------------------------------------------------------------
# MÀN HÌNH 3: GIAO DIỆN LÀM BÀI FULL MÀN HÌNH
# -------------------------------------------------------------------------
else:
    q = st.session_state.selected_quiz
    quiz_id = q.get('id', 'temp_id')
    questions = q.get('questions', [])
    num_questions = len(questions)

    if st.button(QUIZ_LABELS[lang]["btn_back_list"]):
        st.session_state.selected_quiz = None
        fetch_latest_data() 
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
                
                submit_payload = {
                    "quiz_id": quiz_id,
                    "exp_earned": earned_exp,
                    "score": score
                }
                
                try:
                    res = requests.post(f"http://127.0.0.1:8000/api/tv2/student/{encoded_name}/submit-quiz", json=submit_payload, timeout=5)
                    
                    if res.status_code == 200 or res.status_code == 201:
                        # Điều hướng sang màn hình Xem sơ đồ kết quả (Màn hình 2)
                        st.session_state.selected_quiz = None
                        st.session_state.quiz_result_view = {
                            "correct": correct_count,
                            "total": num_questions,
                            "score": score,
                            "exp": earned_exp
                        }
                        st.rerun()
                        
                    elif res.status_code == 400:
                        st.error(QUIZ_LABELS[lang]["err_duplicate"])
                        time.sleep(3)
                        st.session_state.selected_quiz = None
                        fetch_latest_data() 
                        st.rerun()
                    else:
                        st.error(f"Lỗi Server: {res.text}")
                except Exception as e:
                    st.toast(f"{QUIZ_LABELS[lang]['err_save_toast']} {e}")