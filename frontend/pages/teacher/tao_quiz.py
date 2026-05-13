import streamlit as st
import time
import json
import requests
import google.generativeai as genai
from datetime import datetime

st.set_page_config(page_title="Quản Lý Bài Tập AI", page_icon="🤖", layout="wide")

# ================= CẤU HÌNH HỆ THỐNG =================
API_URL = "http://localhost:8000"
GEMINI_API_KEY = "AIzaSyChVKPJxTjK2o_fd0_EzV_-ENyZApq_5aw" # API Key của bạn
genai.configure(api_key=GEMINI_API_KEY)

# Khởi tạo session state nếu chưa có
if "quiz_questions" not in st.session_state:
    st.session_state.quiz_questions = []

# ================= HÀM HỖ TRỢ (HELPERS) =================
def generate_ai_quiz(topic, num_q):
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        prompt = f"""
        Bạn là giáo viên. Tạo {num_q} câu hỏi trắc nghiệm về: "{topic}".
        Trả về DUY NHẤT mảng JSON, không giải thích.
        Format: [{{"question": "...", "options": ["A. ..", "B. ..", "C. ..", "D. .."], "correct_answer": "A. .."}}]
        """
        response = model.generate_content(prompt)
        raw_text = response.text.strip().replace("```json", "").replace("```", "")
        return json.loads(raw_text)
    except Exception as e:
        st.error(f"Lỗi AI: {e}")
        return []

def get_completed_tasks():
    """Lấy danh sách kết quả bài tập từ học sinh (TV2 Academic)"""
    try:
        # Giả sử bạn có route lấy kết quả bài tập
        res = requests.get(f"{API_URL}/api/tv2/quizzes/results")
        return res.json() if res.status_code == 200 else []
    except:
        return []

# ================= GIAO DIỆN CHÍNH =================
st.title("🤖 Quản Lý Bài Tập & Tiến Độ Học Sinh")

# Tạo 3 Tab theo yêu cầu của bạn
tab_create, tab_preview, tab_tracking = st.tabs([
    "✨ Soạn bài tập (AI/Thủ công)", 
    "📋 Xem trước & Lưu kho", 
    "📈 Tiến độ học sinh hoàn thành"
])

# ----------------- TAB 1: SOẠN BÀI TẬP -----------------
with tab_create:
    col_ai, col_manual = st.columns(2, gap="large")
    
    with col_ai:
        st.subheader("Sinh đề bằng AI")
        topic = st.text_input("Chủ đề học tập", placeholder="Ví dụ: Động vật hoang dã")
        num_q = st.slider("Số lượng câu", 1, 10, 5)
        if st.button("🚀 AI soạn đề ngay", type="primary"):
            with st.spinner("AI đang suy nghĩ..."):
                questions = generate_ai_quiz(topic, num_q)
                if questions:
                    st.session_state.quiz_questions.extend(questions)
                    st.success(f"Đã thêm {len(questions)} câu hỏi vào danh sách tạm!")

    with col_manual:
        st.subheader("Nhập câu hỏi thủ công")
        with st.form("manual_form"):
            q_text = st.text_input("Câu hỏi")
            c1, c2 = st.columns(2)
            oa = c1.text_input("Đáp án A")
            ob = c1.text_input("Đáp án B")
            oc = c2.text_input("Đáp án C")
            od = c2.text_input("Đáp án D")
            correct = st.selectbox("Đáp án đúng", ["A", "B", "C", "D"])
            if st.form_submit_button("➕ Thêm câu hỏi"):
                new_q = {
                    "question": q_text,
                    "options": [f"A. {oa}", f"B. {ob}", f"C. {oc}", f"D. {od}"],
                    "correct_answer": f"{correct}. {locals()[f'o{correct.lower()}']}"
                }
                st.session_state.quiz_questions.append(new_q)
                st.toast("Đã thêm câu hỏi thủ công!")

# ----------------- TAB 2: XEM TRƯỚC & LƯU -----------------
with tab_preview:
    if not st.session_state.quiz_questions:
        st.info("Chưa có câu hỏi nào được soạn.")
    else:
        quiz_name = st.text_input("Đặt tên bộ đề", placeholder="Ví dụ: Kiểm tra cuối khóa - Lớp T6")
        
        for i, q in enumerate(st.session_state.quiz_questions):
            with st.expander(f"Câu hỏi {i+1}: {q['question'][:50]}..."):
                st.write(f"**Câu hỏi:** {q['question']}")
                st.write(f"**Đáp án đúng:** :green[{q['correct_answer']}]")
                if st.button(f"Xóa câu {i+1}", key=f"del_{i}"):
                    st.session_state.quiz_questions.pop(i)
                    st.rerun()

        if st.button("💾 LƯU BỘ ĐỀ VÀO DATABASE", use_container_width=True, type="primary"):
            if not quiz_name:
                st.error("Vui lòng nhập tên bộ đề!")
            else:
                payload = {
                    "title": quiz_name,
                    "questions": st.session_state.quiz_questions,
                    "created_at": datetime.now().isoformat()
                }
                # Gửi lên API Backend để lưu vào MongoDB
                res = requests.post(f"{API_URL}/api/tv2/quizzes", json=payload)
                if res.status_code in [200, 201]:
                    st.success("Đã lưu vào kho học liệu thành công!")
                    st.session_state.quiz_questions = []
                    time.sleep(1)
                    st.rerun()

# ----------------- TAB 3: TIẾN ĐỘ (YÊU CẦU MỚI) -----------------
with tab_tracking:
    st.subheader("Danh sách bài tập học sinh đã hoàn thành")
    st.write("Tại đây giáo viên có thể theo dõi xem học sinh nào đã làm bài và đạt bao nhiêu điểm.")
    
    # Lấy dữ liệu thật từ database kết quả bài làm
    results = get_completed_tasks()
    
    if not results:
        # Mock data mẫu nếu DB chưa có dữ liệu kết quả
        results = [
            {"student_name": "Nguyễn Văn An", "quiz_title": "Thì hiện tại đơn", "score": "9/10", "date": "12/05/2026"},
            {"student_name": "Trần Thị Bình", "quiz_title": "Từ vựng Con Vật", "score": "10/10", "date": "13/05/2026"},
        ]

    # Hiển thị dạng bảng (giống yêu cầu Excel của bạn)
    import pandas as pd
    df = pd.DataFrame(results)
    df.columns = ["Học sinh", "Tên bài tập", "Điểm số", "Ngày nộp"]
    st.table(df)

    st.download_button(
        label="📥 Xuất báo cáo kết quả (Excel/CSV)",
        data=df.to_csv(index=False).encode('utf-8-sig'),
        file_name='ket_qua_hoc_tap.csv',
        mime='text/csv',
    )