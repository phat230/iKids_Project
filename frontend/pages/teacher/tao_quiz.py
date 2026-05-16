import streamlit as st
import time
import requests
import os
from datetime import datetime
import pandas as pd

st.set_page_config(page_title="Quản Lý Bài Tập AI", page_icon="🤖", layout="wide")

# ================= HÀM ĐỌC FILE CSS (ĐƯỜNG DẪN TUYỆT ĐỐI) =================
def load_css(file_name):
    """Tự động tìm file CSS trong thư mục frontend/CSS/"""
    current_dir = os.path.dirname(os.path.abspath(__file__)) # pages/teacher
    css_root = os.path.abspath(os.path.join(current_dir, "../../CSS"))
    full_path = os.path.join(css_root, file_name)

    if os.path.exists(full_path):
        with open(full_path, "r", encoding="utf-8") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    else:
        st.warning(f"⚠️ Không tìm thấy file CSS tại: {full_path}")

# Tải CSS (Truyền folder con teacher/)
load_css("teacher/tao_quiz.css")

# ================= KHỞI TẠO KHO LƯU TRỮ CHUNG =================
if "quiz_questions" not in st.session_state:
    st.session_state.quiz_questions = []

def get_teacher_info():
    if "user_info" in st.session_state:
        info = st.session_state.user_info
        email = info.get("email", "khach@gmail.com")
        name = info.get("full_name", info.get("name", email.split('@')[0]))
        return email, name
    return "khach@gmail.com", "Khách"

teacher_email, teacher_name = get_teacher_info()

# ================= KẾT NỐI API BACKEND =================
API_URL = "http://127.0.0.1:8000"
API_URL_QUIZZES = f"{API_URL}/api/tv2/quizzes"
API_GENERATE_QUIZ = f"{API_URL}/api/tv2/generate-quiz"
API_GENERATE_QUIZ_FILE = f"{API_URL}/api/tv2/generate-quiz-from-file"

# Hàm format lại định dạng A, B, C, D cho câu trả lời từ AI
def format_ai_questions(raw_questions):
    prefixes = ["A", "B", "C", "D"]
    for q in raw_questions:
        formatted_options = []
        correct_idx = 0
        for idx, opt in enumerate(q.get("options", [])):
            clean_opt = str(opt).replace("A. ", "").replace("B. ", "").replace("C. ", "").replace("D. ", "").strip()
            clean_correct = str(q.get("correct_answer", "")).replace("A. ", "").replace("B. ", "").replace("C. ", "").replace("D. ", "").strip()
            if clean_opt == clean_correct:
                correct_idx = idx
            formatted_options.append(f"{prefixes[idx]}. {clean_opt}")
        q["options"] = formatted_options
        if formatted_options and correct_idx < len(formatted_options):
            q["correct_answer"] = formatted_options[correct_idx]
    return raw_questions

def generate_real_ai_quiz(topic, num_q):
    try:
        payload = {"topic": topic, "num_questions": num_q}
        response = requests.post(API_GENERATE_QUIZ, json=payload, timeout=60)
        
        if response.status_code == 200:
            data = response.json()
            raw_questions = data.get("questions", [])
            return format_ai_questions(raw_questions)
        return []
    except Exception as e:
        st.error(f"🔥 Lỗi hệ thống: {e}")
        return []

def get_completed_tasks():
    try:
        res = requests.get(f"{API_URL}/api/tv2/quizzes/results")
        return res.json() if res.status_code == 200 else []
    except: return []

# ================= GIAO DIỆN CHÍNH =================
st.title("🤖 Quản Lý Bài Tập & Tiến Độ Học Sinh")

tab_create, tab_preview, tab_tracking = st.tabs([
    "✨ Soạn bài tập (AI/Thủ công)", 
    "📋 Xem trước & Lưu kho", 
    "📈 Tiến độ học sinh"
])

# --- TAB 1: SOẠN BÀI TẬP ---
with tab_create:
    col_ai, col_manual = st.columns(2, gap="large")
    
    with col_ai:
        st.subheader("Sinh đề bằng AI")
        
        # Công tắc chọn cách thức tạo đề
        ai_mode = st.radio("Cách thức tạo đề:", ["Tự nhập chủ đề", "Tải tài liệu Word (.docx) lên"], horizontal=True)

        if ai_mode == "Tự nhập chủ đề":
            topic = st.text_input("Chủ đề học tập", placeholder="Ví dụ: Động vật hoang dã")
            num_q = st.slider("Số lượng câu", 1, 20, 5)
            
            if st.button("🚀 AI Bắt đầu soạn đề", type="primary", use_container_width=True):
                if not topic: 
                    st.warning("⚠️ Vui lòng nhập chủ đề!")
                else:
                    with st.spinner(f"AI đang soạn {num_q} câu về '{topic}'..."):
                        qs = generate_real_ai_quiz(topic, num_q)
                        if qs:
                            st.session_state.quiz_questions.extend(qs)
                            st.success("✅ AI soạn xong! Hãy sang tab Xem trước.")
                            
        else: # Chế độ tải file Word
            uploaded_file = st.file_uploader("Kéo thả hoặc chọn file Word (.docx)", type=["docx"])
            num_q_file = st.slider("Số lượng câu cần trích xuất", 1, 20, 5, key="file_slider")

            if st.button("🚀 AI Đọc File & Soạn Đề", type="primary", use_container_width=True):
                if uploaded_file is None:
                    st.warning("⚠️ Vui lòng tải file Word lên trước!")
                else:
                    with st.spinner("AI đang đọc tài liệu và phân tích câu hỏi..."):
                        try:
                            # Đóng gói file gửi qua API Backend
                            files = {
                                "file": (uploaded_file.name, uploaded_file.getvalue(), "application/vnd.openxmlformats-officedocument.wordprocessingml.document")
                            }
                            data = {"num_questions": num_q_file}
                            
                            res = requests.post(API_GENERATE_QUIZ_FILE, files=files, data=data)
                            if res.status_code == 200:
                                raw_questions = res.json().get("questions", [])
                                # Tái sử dụng hàm format đáp án A, B, C, D
                                formatted_qs = format_ai_questions(raw_questions)
                                
                                st.session_state.quiz_questions.extend(formatted_qs)
                                st.success("✅ AI đã trích xuất xong! Hãy sang tab Xem trước.")
                            else:
                                st.error(f"❌ Lỗi: {res.json().get('detail', res.text)}")
                        except Exception as e:
                            st.error(f"❌ Lỗi kết nối API: {e}")

    with col_manual:
        st.subheader("Nhập câu hỏi thủ công")
        with st.form("manual_form"):
            manual_q = st.text_input("Câu hỏi")
            c1, c2 = st.columns(2)
            o_a, o_b = c1.text_input("Đáp án A"), c1.text_input("Đáp án B")
            o_c, o_d = c2.text_input("Đáp án C"), c2.text_input("Đáp án D")
            correct = st.selectbox("Đáp án đúng", ["A", "B", "C", "D"])
            if st.form_submit_button("➕ Thêm câu hỏi", use_container_width=True):
                if all([manual_q, o_a, o_b, o_c, o_d]):
                    opts = [f"A. {o_a}", f"B. {o_b}", f"C. {o_c}", f"D. {o_d}"]
                    idx = ["A", "B", "C", "D"].index(correct)
                    st.session_state.quiz_questions.append({"question": manual_q, "options": opts, "correct_answer": opts[idx]})
                    st.success("Đã thêm 1 câu!")

# --- TAB 2: XEM TRƯỚC ---
with tab_preview:
    if not st.session_state.quiz_questions:
        st.info("💡 Chưa có câu hỏi nào. Bạn hãy soạn đề ở Tab đầu tiên nhé!")
    else:
        st.markdown(f"### 📋 Tổng hợp bộ Quiz ({len(st.session_state.quiz_questions)} câu)")
        quiz_title = st.text_input("Tên bộ Quiz", placeholder="Nhập tên để lưu (Ví dụ: Kiểm tra 15 phút bài Word)...")
        
        for i, q in enumerate(st.session_state.quiz_questions):
            with st.container(border=True):
                cq, cb = st.columns([9, 1])
                cq.markdown(f"**Câu {i+1}: {q['question']}**")
                ans_idx = q['options'].index(q['correct_answer']) if q['correct_answer'] in q['options'] else 0
                cq.radio("Lựa chọn:", q['options'], index=ans_idx, key=f"preview_{i}", disabled=True)
                if cb.button("🗑️", key=f"del_{i}"):
                    st.session_state.quiz_questions.pop(i); st.rerun()
        
        if st.button("💾 LƯU BỘ ĐỀ VÀO KHO", type="primary", use_container_width=True):
            if not quiz_title: 
                st.error("⚠️ Hãy đặt tên bộ đề trước khi lưu!")
            else:
                payload = {
                    "title": quiz_title, "questions": st.session_state.quiz_questions,
                    "author_email": teacher_email, "author": teacher_name
                }
                if requests.post(API_URL_QUIZZES, json=payload).status_code in [200, 201]:
                    st.success("🎉 Đã lưu bộ đề vào kho học liệu thành công!")
                    st.session_state.quiz_questions = []
                    time.sleep(1)
                    st.switch_page("pages/teacher/kho_hoc_lieu.py")

# --- TAB 3: TIẾN ĐỘ ---
with tab_tracking:
    st.subheader("Tiến độ học sinh hoàn thành")
    results = get_completed_tasks()
    if not results:
        results = [{"Học sinh": "An", "Bài tập": "Toán", "Điểm": "9/10", "Ngày": "12/05/2026"}]
    df = pd.DataFrame(results)
    st.table(df)
    st.download_button("📥 Xuất báo cáo CSV", data=df.to_csv(index=False).encode('utf-8-sig'), file_name='ket_qua_lam_bai.csv', mime='text/csv')