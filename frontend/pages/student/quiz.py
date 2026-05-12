import streamlit as st
import requests
import time
import urllib.parse

st.set_page_config(page_title="Trạm Quiz AI", page_icon="📝", layout="wide")

# CSS Trang trí cho thẻ Quiz đẹp mắt
st.markdown("""
    <style>
    .quiz-card {
        background: #ffffff; border-radius: 10px; padding: 15px 20px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05); margin-bottom: 15px;
        border-left: 5px solid #4F46E5; border-top: 1px solid #e2e8f0; border-right: 1px solid #e2e8f0; border-bottom: 1px solid #e2e8f0;
    }
    .quiz-title { font-size: 1.2rem; font-weight: bold; color: #1e293b; margin-bottom: 5px; }
    .quiz-meta { color: #64748b; font-size: 0.9rem; }
    </style>
""", unsafe_allow_html=True)

# ================= HÀM LẤY TÊN USER =================
def get_current_username():
    """Tự động tìm tên tài khoản thật từ hệ thống đăng nhập"""
    if "username" in st.session_state and st.session_state.username: return st.session_state.username
    if "full_name" in st.session_state and st.session_state.full_name: return st.session_state.full_name
    if "user_info" in st.session_state and isinstance(st.session_state.user_info, dict):
        return st.session_state.user_info.get("full_name", st.session_state.user_info.get("name", "Học sinh"))
    return "Học sinh"

real_name = get_current_username()
# MÃ HÓA TÊN AN TOÀN ĐỂ KHÔNG BỊ LỖI KHI GỌI API (Khắc phục lỗi khoảng trắng)
encoded_name = urllib.parse.quote(real_name)

# ================= ĐỒNG BỘ PROFILE TỪ DATABASE =================
try:
    prof_res = requests.get(f"http://127.0.0.1:8000/api/tv2/student/{encoded_name}/profile", timeout=5)
    if prof_res.status_code == 200:
        st.session_state.student_profile = prof_res.json()
    else:
        st.session_state.student_profile = {"username": real_name, "exp": 0, "completed_tasks": []}
except Exception as e:
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
    # ĐÂY LÀ DÒNG LỖI MỚI. NẾU WEB CỦA ÔNG CHƯA HIỆN DÒNG NÀY NGHĨA LÀ CHƯA SAVE CODE!
    st.error(f"⚠️ Mất kết nối đến Backend Database (Chi tiết lỗi: {e}). Hãy đảm bảo Uvicorn đang chạy!")
    saved_quizzes = []
# ============================================================================

if "selected_quiz" not in st.session_state:
    st.session_state.selected_quiz = None

# -------------------------------------------------------------------------
# MÀN HÌNH 1: DANH SÁCH BỘ ĐỀ
# -------------------------------------------------------------------------
if st.session_state.selected_quiz is None:
    st.title("📝 Trạm Quiz AI")
    st.write("Hoàn thành các bài tập dưới đây để tích lũy EXP thăng hạng nhé!")
    
    st.markdown(f"🌟 **Tổng EXP của bạn:** `{st.session_state.student_profile.get('exp', 0)} EXP`")

    if not saved_quizzes:
        st.info("🎉 Hiện tại giáo viên chưa có bài tập nào. Bạn có thể nghỉ ngơi!")
    else:
        for i, q in enumerate(saved_quizzes):
            quiz_id = q.get('id', f"quiz_backup_id_{i}")
            is_completed = quiz_id in st.session_state.student_profile.get('completed_tasks', [])
            
            with st.container():
                col_info, col_btn = st.columns([4, 1])
                with col_info:
                    st.markdown(f"""
                    <div class="quiz-card">
                        <div class="quiz-title">📜 {q.get('title', 'Bài tập chưa có tên')}</div>
                        <div class="quiz-meta">Số câu: {len(q.get('questions', []))} | Phần thưởng: +50 EXP</div>
                    </div>
                    """, unsafe_allow_html=True)
                
                with col_btn:
                    st.write("") 
                    if is_completed:
                        st.button("✅ Đã hoàn thành", key=f"done_{quiz_id}", disabled=True, use_container_width=True)
                    else:
                        if st.button("▶ Bắt đầu làm", key=f"start_{quiz_id}", type="primary", use_container_width=True):
                            st.session_state.selected_quiz = q
                            st.rerun()

    st.divider()
    if st.button("⬅️ Quay lại Bảng Điều Khiển"):
        st.switch_page("pages/student/dashboard.py")

# -------------------------------------------------------------------------
# MÀN HÌNH 2: GIAO DIỆN LÀM BÀI FULL MÀN HÌNH
# -------------------------------------------------------------------------
else:
    q = st.session_state.selected_quiz
    quiz_id = q.get('id', 'temp_id')
    questions = q.get('questions', [])
    num_questions = len(questions)

    if st.button("⬅️ Trở về danh sách bộ đề"):
        st.session_state.selected_quiz = None
        st.rerun()

    st.markdown(f"## 📝 Đề thi: {q.get('title')}")
    st.info("Hãy đọc kỹ câu hỏi và chọn đáp án chính xác nhất. Cần tích đủ tất cả các câu mới có thể nộp bài.")

    with st.form(key=f"full_quiz_form_{quiz_id}"):
        user_answers = {}
        for idx, question in enumerate(questions):
            st.markdown(f"**Câu {idx + 1}: {question['question']}**")
            
            user_answers[idx] = st.radio(
                label="Chọn đáp án:", 
                options=question['options'], 
                key=f"ans_{quiz_id}_{idx}", 
                index=None,
                label_visibility="collapsed"
            )
            st.write("---")
        
        submit_btn = st.form_submit_button("🚀 Nộp Bài & Nhận Thưởng", type="primary", use_container_width=True)
        
        if submit_btn:
            if None in user_answers.values():
                st.error("⚠️ Bạn chưa chọn đáp án cho tất cả các câu. Vui lòng kéo lên kiểm tra và điền đầy đủ trước khi nộp!")
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
                    st.toast(f"⚠️ Có lỗi khi lưu dữ liệu lên server: {e}")

                st.session_state.student_profile['exp'] += earned_exp
                st.session_state.student_profile['completed_tasks'].append(quiz_id)
                
                st.success(f"🎉 Chấm xong! Bạn làm đúng {correct_count}/{num_questions} câu. **Điểm: {score}/10**")
                st.balloons()
                st.info(f"✨ Chúc mừng! Bạn nhận được +{earned_exp} EXP! Đang quay lại trang chủ...")
                
                time.sleep(3)
                st.session_state.selected_quiz = None
                st.rerun()