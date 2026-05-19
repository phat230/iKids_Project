import streamlit as st
import time
import requests
import os
from datetime import datetime
import pandas as pd
from deep_translator import GoogleTranslator

# ================= CRITICAL: CẤU HÌNH TRANG LUÔN ĐỂ ĐẦU FILE =================
st.set_page_config(page_title="Quản Lý Bài Tập AI", page_icon="🤖", layout="wide")

# ================= HÀM ĐỌC FILE CSS =================
def load_css(file_name):
    current_dir = os.path.dirname(os.path.abspath(__file__))
    css_root = os.path.abspath(os.path.join(current_dir, "../../CSS"))
    full_path = os.path.join(css_root, file_name)

    if os.path.exists(full_path):
        with open(full_path, "r", encoding="utf-8") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

load_css("teacher/tao_quiz.css")

# Lấy cấu hình ngôn ngữ hiện hành (Mặc định "vi")
lang = st.session_state.get("lang", "vi")

# ================= BỘ TỪ ĐIỂN SONG NGỮ =================
QUIZ_LABELS = {
    "vi": {
        "title": "🤖 Quản Lý Bài Tập AI",
        "tab_create": "Soạn bài tập (AI/Thủ công)",
        "tab_preview": "Xem trước & Lưu kho",
        "tab_tracking": "Tiến độ học sinh",
        "sub_ai": "Tạo Tập Bằng AI",
        "ai_mode": "Cách thức tạo đề:",
        "ai_mode_opts": ["Tự nhập chủ đề", "Tải tài liệu Word (.docx) lên"],
        "input_topic": "Chủ đề học tập",
        "topic_placeholder": "Ví dụ: Động vật hoang dã",
        "input_num": "Số lượng câu",
        "btn_ai_gen": "Soạn đề bằng AI",
        "warn_topic": "⚠️ Vui lòng nhập chủ đề!",
        "spinner_ai": "AI đang soạn {} câu về '{}'...",
        "success_ai": "✅ AI soạn xong! Hãy sang tab Xem trước.",
        "file_uploader": "Kéo thả hoặc chọn file Word (.docx)",
        "btn_ai_file": "AI bắt đầu soạn đề",
        "warn_file": "⚠️ Vui lòng tải file Word lên trước!",
        "spinner_file": "AI đang đọc tài liệu và phân tích câu hỏi...",
        "sub_manual": "Nhập câu hỏi thủ công",
        "input_q": "Câu hỏi",
        "input_opt": "Đáp án",
        "input_correct": "Đáp án đúng",
        "btn_add_manual": "Thêm câu hỏi",
        "success_add": "Đã thêm 1 câu!",
        "info_empty": "💡 Chưa có câu hỏi nào. Bạn hãy soạn đề ở Tab đầu tiên nhé!",
        "sub_preview": "Tổng hợp toàn bộ câu hỏi ({} câu)",
        "input_title": "Tên bộ Quiz",
        "title_placeholder": "Nhập tên để lưu (Ví dụ: Kiểm tra 15 phút)...",
        "btn_save": "LƯU BÀI TẬP VÀO KHO",
        "err_title": "⚠️ Hãy đặt tên bộ đề trước khi lưu!",
        "success_save": "🎉 Đã lưu bộ đề vào kho học liệu thành công!",
        "sub_tracking": "Tiến độ học sinh hoàn thành",
        "btn_export": "XUẤT BÁO CÁO"
    },
    "en": {
        "title": "🤖 AI Quiz Management",
        "tab_create": "Compose Quiz (AI/Manual)",
        "tab_preview": "Preview & Save to Library",
        "tab_tracking": "Student Progress",
        "sub_ai": "Generate Quiz with AI",
        "ai_mode": "Method:",
        "ai_mode_opts": ["Enter Topic", "Upload Word Document (.docx)"],
        "input_topic": "Learning Topic",
        "topic_placeholder": "e.g., Wildlife Ecosystems",
        "input_num": "Number of Questions",
        "btn_ai_gen": "Generate with AI",
        "warn_topic": "⚠️ Please enter a topic!",
        "spinner_ai": "AI is generating {} questions about '{}'...",
        "success_ai": "✅ Generation complete! Head to the Preview tab.",
        "file_uploader": "Drag & drop or upload Word file (.docx)",
        "btn_ai_file": "Start AI Analysis",
        "warn_file": "⚠️ Please upload a Word file first!",
        "spinner_file": "AI is parsing document and analyzing questions...",
        "sub_manual": "Add Questions Manually",
        "input_q": "Question",
        "input_opt": "Option",
        "input_correct": "Correct Answer",
        "btn_add_manual": "Add Question",
        "success_add": "Added 1 question!",
        "info_empty": "💡 No questions added yet. Start composing in the first tab!",
        "sub_preview": "Review Quiz Questions ({} total)",
        "input_title": "Quiz Title",
        "title_placeholder": "Enter title to save (e.g., 15-min Tech Quiz)...",
        "btn_save": "SAVE QUIZ TO LIBRARY",
        "err_title": "⚠️ Please name the quiz before saving!",
        "success_save": "🎉 Quiz successfully saved to library!",
        "sub_tracking": "Student Completion Progress",
        "btn_export": "EXPORT REPORT"
    }
}

# ================= KHỞI TẠO STATE =================
if "quiz_questions" not in st.session_state: st.session_state.quiz_questions = []

def get_teacher_info():
    if "user_info" in st.session_state:
        info = st.session_state.user_info
        email = info.get("email", "khach@gmail.com")
        name = info.get("full_name", info.get("name", email.split('@')[0]))
        return email, name
    return "khach@gmail.com", "Guest"

teacher_email, teacher_name = get_teacher_info()

# ================= API ENDPOINTS =================
API_URL = "http://127.0.0.1:8000"
API_URL_QUIZZES = f"{API_URL}/api/tv2/quizzes"
API_GENERATE_QUIZ = f"{API_URL}/api/tv2/generate-quiz"
API_GENERATE_QUIZ_FILE = f"{API_URL}/api/tv2/generate-quiz-from-file"

# ================= HÀM HỖ TRỢ DỊCH & FORMAT =================
def format_ai_questions(raw_questions):
    prefixes = ["A", "B", "C", "D"]
    for q in raw_questions:
        formatted_options = []
        correct_idx = 0
        clean_correct = str(q.get("correct_answer", "")).replace("A. ", "").replace("B. ", "").replace("C. ", "").replace("D. ", "").strip()
        for idx, opt in enumerate(q.get("options", [])):
            clean_opt = str(opt).replace("A. ", "").replace("B. ", "").replace("C. ", "").replace("D. ", "").strip()
            if clean_opt == clean_correct: correct_idx = idx
            formatted_options.append(f"{prefixes[idx]}. {clean_opt}")
        q["options"] = formatted_options
        q["correct_answer"] = formatted_options[correct_idx]
    return raw_questions

def generate_real_ai_quiz(topic, num_q):
    try:
        response = requests.post(API_GENERATE_QUIZ, json={"topic": topic, "num_questions": num_q}, timeout=60)
        return format_ai_questions(response.json().get("questions", [])) if response.status_code == 200 else []
    except: return []

# ================= GIAO DIỆN CHÍNH =================
tab_create, tab_preview, tab_tracking = st.tabs([QUIZ_LABELS[lang]["tab_create"], QUIZ_LABELS[lang]["tab_preview"], QUIZ_LABELS[lang]["tab_tracking"]])

with tab_create:
    col_ai, col_manual = st.columns(2, gap="large")
    with col_ai:
        st.subheader(QUIZ_LABELS[lang]["sub_ai"])
        ai_mode = st.radio(QUIZ_LABELS[lang]["ai_mode"], QUIZ_LABELS[lang]["ai_mode_opts"], horizontal=True)
        
        if ai_mode == QUIZ_LABELS[lang]["ai_mode_opts"][0]:
            topic = st.text_input(QUIZ_LABELS[lang]["input_topic"], placeholder=QUIZ_LABELS[lang]["topic_placeholder"])
            num_q = st.slider(QUIZ_LABELS[lang]["input_num"], 1, 20, 5)
            if st.button(QUIZ_LABELS[lang]["btn_ai_gen"], type="primary", use_container_width=True):
                if not topic: st.warning(QUIZ_LABELS[lang]["warn_topic"])
                else:
                    with st.spinner(QUIZ_LABELS[lang]["spinner_ai"].format(num_q, topic)):
                        qs = generate_real_ai_quiz(topic, num_q)
                        if qs: st.session_state.quiz_questions.extend(qs); st.success(QUIZ_LABELS[lang]["success_ai"])
        else:
            uploaded_file = st.file_uploader(QUIZ_LABELS[lang]["file_uploader"], type=["docx"])
            num_q_file = st.slider(QUIZ_LABELS[lang]["input_num"], 1, 20, 5, key="file_slider")
            if st.button(QUIZ_LABELS[lang]["btn_ai_file"], type="primary", use_container_width=True):
                if not uploaded_file: st.warning(QUIZ_LABELS[lang]["warn_file"])
                else:
                    with st.spinner(QUIZ_LABELS[lang]["spinner_file"]):
                        files = {"file": (uploaded_file.name, uploaded_file.getvalue(), "application/vnd.openxmlformats-officedocument.wordprocessingml.document")}
                        res = requests.post(API_GENERATE_QUIZ_FILE, files=files, data={"num_questions": num_q_file})
                        if res.status_code == 200:
                            st.session_state.quiz_questions.extend(format_ai_questions(res.json().get("questions", [])))
                            st.success(QUIZ_LABELS[lang]["success_ai"])

    with col_manual:
        st.subheader(QUIZ_LABELS[lang]["sub_manual"])
        with st.form("manual_form"):
            manual_q = st.text_input(QUIZ_LABELS[lang]["input_q"])
            c1, c2 = st.columns(2)
            o_a, o_b = c1.text_input("A", key="ma"), c1.text_input("B", key="mb")
            o_c, o_d = c2.text_input("C", key="mc"), c2.text_input("D", key="md")
            correct = st.selectbox(QUIZ_LABELS[lang]["input_correct"], ["A", "B", "C", "D"])
            if st.form_submit_button(QUIZ_LABELS[lang]["btn_add_manual"], use_container_width=True):
                opts = [f"A. {o_a}", f"B. {o_b}", f"C. {o_c}", f"D. {o_d}"]
                st.session_state.quiz_questions.append({"question": manual_q, "options": opts, "correct_answer": opts[["A","B","C","D"].index(correct)]})
                st.success(QUIZ_LABELS[lang]["success_add"])

with tab_preview:
    if not st.session_state.quiz_questions: st.info(QUIZ_LABELS[lang]["info_empty"])
    else:
        st.markdown(f"### {QUIZ_LABELS[lang]['sub_preview'].format(len(st.session_state.quiz_questions))}")
        quiz_title = st.text_input(QUIZ_LABELS[lang]["input_title"], placeholder=QUIZ_LABELS[lang]["title_placeholder"])
        for i, q in enumerate(st.session_state.quiz_questions):
            with st.container(border=True):
                cq, cb = st.columns([9, 1])
                cq.markdown(f"**{i+1}. {q['question']}**")
                ans_idx = q['options'].index(q['correct_answer']) if q['correct_answer'] in q['options'] else 0
                cq.radio("...", q['options'], index=ans_idx, key=f"p_{i}", disabled=True, label_visibility="collapsed")
                if cb.button("❌", key=f"del_{i}"): st.session_state.quiz_questions.pop(i); st.rerun()
        
        if st.button(QUIZ_LABELS[lang]["btn_save"], type="primary", use_container_width=True):
            if not quiz_title: st.error(QUIZ_LABELS[lang]["err_title"])
            else:
                payload = {"title": quiz_title, "questions": st.session_state.quiz_questions, "author_email": teacher_email, "author": teacher_name}
                if requests.post(API_URL_QUIZZES, json=payload).status_code in [200, 201]:
                    st.success(QUIZ_LABELS[lang]["success_save"])
                    st.session_state.quiz_questions = []
                    time.sleep(1); st.rerun()

with tab_tracking:
    st.subheader(QUIZ_LABELS[lang]["sub_tracking"])
    # ... (giữ nguyên logic fetch API tracking)
    st.button(QUIZ_LABELS[lang]["btn_export"])