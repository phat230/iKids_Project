import streamlit as st
import time
import json
import requests
import google.generativeai as genai
from datetime import datetime

st.set_page_config(page_title="Quản Lý Bài Tập AI", page_icon="🤖", layout="wide")

<<<<<<< HEAD
# ================= KHỞI TẠO KHO LƯU TRỮ CHUNG =================
if "saved_quizzes" not in st.session_state:
    st.session_state.saved_quizzes = []

# LẤY CẢ EMAIL VÀ TÊN THẬT TỪ HỆ THỐNG ĐỂ LƯU VÀO DB
def get_teacher_info():
    if "user_info" in st.session_state:
        info = st.session_state.user_info
        
        email = info.get("email", "khach@gmail.com")
        
        # Quét tên thật từ DB của TV1
        name = info.get("full_name", 
               info.get("name", 
               info.get("ho_ten", 
               info.get("ho_va_ten", 
               info.get("username", email.split('@')[0])))))
               
        return email, name
    return "khach@gmail.com", "Khách"

teacher_email, teacher_name = get_teacher_info()

# ================= KẾT NỐI API BACKEND =================
API_URL_QUIZZES = "http://127.0.0.1:8000/api/tv2/quizzes"

# ================= CẤU HÌNH AI =================
GEMINI_API_KEY = "AIzaSyBgREbTgan_MGy14hcNsr8B3hmuBfVvnGA" 
genai.configure(api_key=GEMINI_API_KEY)

def generate_real_ai_quiz(topic, num_q):
    """Hàm gọi API Gemini để sinh câu hỏi trắc nghiệm thật"""
    try:
        model = genai.GenerativeModel('gemini-2.5-flash')
        prompt = f"""
        Bạn là một giáo viên. Hãy tạo {num_q} câu hỏi trắc nghiệm về chủ đề: "{topic}".
        Trả về KẾT QUẢ DUY NHẤT LÀ MỘT MẢNG JSON, không giải thích.
        Cấu trúc JSON bắt buộc:
        [
          {{
            "question": "Nội dung câu hỏi",
            "options": ["Đáp án 1", "Đáp án 2", "Đáp án 3", "Đáp án 4"],
            "correct_answer": "Đáp án đúng (phải giống hệt 1 trong 4 đáp án trên)"
          }}
        ]
        """
        response = model.generate_content(prompt)
        raw_text = response.text.strip()
        
        if raw_text.startswith("```json"):
            raw_text = raw_text[7:-3]
        elif raw_text.startswith("```"):
            raw_text = raw_text[3:-3]
            
        data = json.loads(raw_text)
        
        prefixes = ["A", "B", "C", "D"]
        for q in data:
            formatted_options = []
            correct_idx = 0
            
            for idx, opt in enumerate(q["options"]):
                clean_opt = opt.replace("A. ", "").replace("B. ", "").replace("C. ", "").replace("D. ", "").strip()
                clean_correct = str(q.get("correct_answer", "")).replace("A. ", "").replace("B. ", "").replace("C. ", "").replace("D. ", "").strip()
                
                if clean_opt == clean_correct:
                    correct_idx = idx
                
                formatted_options.append(f"{prefixes[idx]}. {clean_opt}")
            
            q["options"] = formatted_options
            q["correct_answer"] = formatted_options[correct_idx]

        return data
    except Exception as e:
        st.error(f"Lỗi gọi AI: {e}")
        return []

# ==============================================

st.title("🤖 Tạo Bài Tập Trắc Nghiệm (Quiz)")
st.write("Sử dụng AI để tự động tạo bộ câu hỏi nhanh chóng hoặc tự thiết kế câu hỏi thủ công cho lớp học của bạn.")

=======
# ================= CẤU HÌNH HỆ THỐNG =================
API_URL = "http://localhost:8000"
GEMINI_API_KEY = "AIzaSyChVKPJxTjK2o_fd0_EzV_-ENyZApq_5aw" # API Key của bạn
genai.configure(api_key=GEMINI_API_KEY)

# Khởi tạo session state nếu chưa có
>>>>>>> b867fa3eeaab06e3a13728884e413c388f05024f
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
    
<<<<<<< HEAD
    if st.button("🚀 AI Bắt đầu soạn đề", type="primary"):
        if not topic:
            st.warning("⚠️ Vui lòng nhập chủ đề trước khi gọi AI!")
        else:
            with st.spinner(f"AI đang phân tích chủ đề '{topic}' và soạn {num_q} câu hỏi..."):
                real_questions = generate_real_ai_quiz(topic, num_q)
                if real_questions:
                    st.session_state.quiz_questions.extend(real_questions)
                    st.success("✅ AI đã soạn xong! Hãy kiểm tra lại ở phần bên dưới.")
=======
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
>>>>>>> b867fa3eeaab06e3a13728884e413c388f05024f

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
        
<<<<<<< HEAD
        if st.button("➕ Thêm vào bộ Quiz"):
            if manual_q and opt_a and opt_b and opt_c and opt_d:
                fmt_a = opt_a if opt_a.upper().startswith("A. ") else f"A. {opt_a}"
                fmt_b = opt_b if opt_b.upper().startswith("B. ") else f"B. {opt_b}"
                fmt_c = opt_c if opt_c.upper().startswith("C. ") else f"C. {opt_c}"
                fmt_d = opt_d if opt_d.upper().startswith("D. ") else f"D. {opt_d}"
                
                opts_list = [fmt_a, fmt_b, fmt_c, fmt_d]
                correct_idx = ["Đáp án A", "Đáp án B", "Đáp án C", "Đáp án D"].index(correct_opt)
                
                st.session_state.quiz_questions.append({
                    "question": manual_q,
                    "options": opts_list,
                    "correct_answer": opts_list[correct_idx]
                })
                st.success("Đã thêm 1 câu hỏi thủ công!")
            else:
                st.error("Vui lòng điền đầy đủ câu hỏi và 4 đáp án.")

st.divider()

if st.session_state.quiz_questions:
    st.markdown(f"### 📋 Tổng hợp bộ Quiz ({len(st.session_state.quiz_questions)} câu hỏi)")
    
    quiz_title = st.text_input("Tên bộ Quiz (để lưu vào kho)", placeholder="Nhập tên để dễ quản lý sau này...")
    
    for i, q in enumerate(st.session_state.quiz_questions):
        with st.container(border=True):
            col_q, col_btn = st.columns([9, 1])
            with col_q:
                st.markdown(f"**Câu {i+1}: {q['question']}**")
                correct_index = q['options'].index(q['correct_answer']) if q['correct_answer'] in q['options'] else 0
                st.radio("Các lựa chọn:", options=q['options'], index=correct_index, key=f"preview_q_{i}", disabled=True)
            with col_btn:
                st.markdown("<br>", unsafe_allow_html=True)
                if st.button("🗑️ Xóa", key=f"del_{i}"):
=======
        for i, q in enumerate(st.session_state.quiz_questions):
            with st.expander(f"Câu hỏi {i+1}: {q['question'][:50]}..."):
                st.write(f"**Câu hỏi:** {q['question']}")
                st.write(f"**Đáp án đúng:** :green[{q['correct_answer']}]")
                if st.button(f"Xóa câu {i+1}", key=f"del_{i}"):
>>>>>>> b867fa3eeaab06e3a13728884e413c388f05024f
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
    
<<<<<<< HEAD
    if st.button("💾 LƯU BỘ ĐỀ VÀO KHO HỌC LIỆU", type="primary", use_container_width=True):
        if not quiz_title:
            st.error("⚠️ Vui lòng đặt tên cho bộ Quiz trước khi lưu.")
        else:
            new_quiz = {
                "title": quiz_title,
                "questions": st.session_state.quiz_questions,
                "created_at": datetime.now().strftime("%d/%m/%Y %H:%M"),
                "author_email": teacher_email, # Khóa bảo mật
                "author": teacher_name         # Tên hiển thị đẹp đúng lấy từ DB
            }
            
            try:
                response = requests.post(API_URL_QUIZZES, json=new_quiz)
                if response.status_code in [200, 201]:
                    st.success(f"🎉 Đã lưu thành công bộ đề '{quiz_title}' vào Database thật! Đang chuyển sang Kho Học Liệu...")
                    st.session_state.quiz_questions = [] 
                    time.sleep(1.5)
                    st.switch_page("pages/teacher/kho_hoc_lieu.py")
                else:
                    st.error("⚠️ Lỗi khi lưu vào Database. Vui lòng thử lại!")
            except Exception as e:
                st.error(f"⚠️ Mất kết nối đến Backend Database: {e}")
else:
    st.info("💡 Chưa có câu hỏi nào. Hãy sử dụng AI hoặc tự nhập câu hỏi ở phía trên để bắt đầu.")
=======
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
>>>>>>> b867fa3eeaab06e3a13728884e413c388f05024f
