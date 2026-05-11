import streamlit as st
import requests
import time

st.set_page_config(page_title="Trạm Quiz AI", page_icon="📝", layout="wide")

# (Giả lập Profile học sinh nếu chưa kết nối API TV3 đầy đủ)
if "student_profile" not in st.session_state:
    st.session_state.student_profile = {"name": "Học sinh", "exp": 0, "completed_tasks": []}

st.title("📝 Trạm Quiz AI")
st.write("Hoàn thành các bài tập dưới đây để tích lũy EXP thăng hạng nhé!")

# ================= GỌI API BACKEND ĐỂ LẤY DANH SÁCH BÀI TẬP =================
API_URL = "http://127.0.0.1:8000/api/tv2/quizzes"

try:
    response = requests.get(API_URL)
    if response.status_code == 200:
        saved_quizzes = response.json()
    else:
        saved_quizzes = []
except Exception as e:
    st.error("⚠️ Không thể kết nối đến Backend Database. Vui lòng kiểm tra Uvicorn!")
    saved_quizzes = []
# ============================================================================

if not saved_quizzes:
    st.info("🎉 Hiện tại giáo viên chưa giao bài tập nào. Bạn có thể nghỉ ngơi!")
else:
    for q in saved_quizzes:
        # Lấy ID của bộ đề
        quiz_id = q.get('id')
        is_completed = quiz_id in st.session_state.student_profile.get('completed_tasks', [])
        
        with st.container(border=True):
            col1, col2 = st.columns([3, 1])
            with col1:
                st.markdown(f"### 📜 {q.get('title', 'Bài tập chưa có tên')}")
                st.caption(f"Số câu: {len(q.get('questions', []))} | Phần thưởng: +50 EXP")
            
            with col2:
                if is_completed:
                    st.success("✅ Đã hoàn thành")
                else:
                    with st.popover("🚀 Bắt đầu làm bài", use_container_width=True):
                        st.write(f"**Đề thi:** {q.get('title')}")
                        with st.form(key=f"quiz_form_{quiz_id}"):
                            user_answers = {}
                            for idx, question in enumerate(q.get('questions', [])):
                                st.write(f"**Câu {idx + 1}: {question['question']}**")
                                user_answers[idx] = st.radio("Chọn đáp án:", question['options'], key=f"ans_{quiz_id}_{idx}")
                                st.write("---")
                            
                            if st.form_submit_button("Nộp Bài & Nhận Thưởng", type="primary"):
                                # Chấm điểm tự động
                                correct_count = sum(1 for idx, question in enumerate(q['questions']) if user_answers[idx] == question['correct_answer'])
                                score = round((correct_count / len(q['questions'])) * 10, 1)
                                st.success(f"Bạn làm đúng {correct_count}/{len(q['questions'])} câu. Điểm: {score}/10")
                                
                                # Tính toán EXP và cập nhật
                                earned_exp = 50 + (correct_count * 10)
                                st.session_state.student_profile['exp'] += earned_exp
                                st.session_state.student_profile['completed_tasks'].append(quiz_id)
                                
                                st.info(f"✨ Chúc mừng! Bạn nhận được +{earned_exp} EXP!")
                                time.sleep(2)
                                st.rerun()

st.divider()
if st.button("⬅️ Quay lại Bảng Điều Khiển"):
    st.switch_page("pages/student/dashboard.py")