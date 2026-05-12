import streamlit as st
import time
import json
from datetime import datetime
import requests
import google.generativeai as genai

st.set_page_config(page_title="Tạo Bài Tập AI", page_icon="🤖", layout="wide")

# ================= KHỞI TẠO KHO LƯU TRỮ CHUNG =================
if "saved_quizzes" not in st.session_state:
    st.session_state.saved_quizzes = []

# ================= KẾT NỐI API BACKEND =================
API_URL_QUIZZES = "http://127.0.0.1:8000/api/tv2/quizzes"

# ================= CẤU HÌNH AI =================
# TODO: Thay API Key của ông vào đây
GEMINI_API_KEY = "AIzaSyChVKPJxTjK2o_fd0_EzV_-ENyZApq_5aw" 
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
        
        # Làm sạch JSON
        if raw_text.startswith("```json"):
            raw_text = raw_text[7:-3]
        elif raw_text.startswith("```"):
            raw_text = raw_text[3:-3]
            
        data = json.loads(raw_text)
        
        # ================= SỬA LỖI Ở ĐÂY: XỬ LÝ HẬU KỲ BẰNG PYTHON =================
        # Bất chấp AI trả về thế nào, Python sẽ ép format A, B, C, D
        prefixes = ["A", "B", "C", "D"]
        for q in data:
            formatted_options = []
            correct_idx = 0
            
            # Tìm vị trí của câu trả lời đúng trước
            for idx, opt in enumerate(q["options"]):
                # Lọc bỏ A. B. C. D. nếu AI có lỡ tự sinh ra để so sánh cho chuẩn
                clean_opt = opt.replace("A. ", "").replace("B. ", "").replace("C. ", "").replace("D. ", "").strip()
                clean_correct = str(q.get("correct_answer", "")).replace("A. ", "").replace("B. ", "").replace("C. ", "").replace("D. ", "").strip()
                
                if clean_opt == clean_correct:
                    correct_idx = idx
                
                # Ép tiền tố A. B. C. D. vào mảng
                formatted_options.append(f"{prefixes[idx]}. {clean_opt}")
            
            # Gán lại mảng đã format cho câu hỏi
            q["options"] = formatted_options
            q["correct_answer"] = formatted_options[correct_idx]
        # =========================================================================

        return data
    except Exception as e:
        st.error(f"Lỗi gọi AI: {e}")
        return []

# ==============================================

st.title("🤖 Tạo Bài Tập Trắc Nghiệm (Quiz)")
st.write("Sử dụng AI để tự động tạo bộ câu hỏi nhanh chóng hoặc tự thiết kế câu hỏi thủ công cho lớp học của bạn.")

if "quiz_questions" not in st.session_state:
    st.session_state.quiz_questions = []

tab_ai, tab_manual = st.tabs(["✨ Sinh câu hỏi bằng AI", "✍️ Thêm câu hỏi thủ công"])

with tab_ai:
    st.markdown("### Thiết lập AI")
    col1, col2 = st.columns([3, 1])
    with col1:
        topic = st.text_input("Chủ đề bài kiểm tra", placeholder="VD: Thì hiện tại đơn, Con vật bằng tiếng Anh...")
    with col2:
        num_q = st.number_input("Số lượng câu hỏi", min_value=1, max_value=10, value=5)
    
    if st.button("🚀 AI Bắt đầu soạn đề", type="primary"):
        if not topic:
            st.warning("⚠️ Vui lòng nhập chủ đề trước khi gọi AI!")
        elif GEMINI_API_KEY == "YOUR_GEMINI_API_KEY":
            st.error("⚠️ Ông chưa thay GEMINI_API_KEY kìa! Đăng ký API Key rồi dán vào code đi.")
        else:
            with st.spinner(f"AI đang phân tích chủ đề '{topic}' và soạn {num_q} câu hỏi..."):
                real_questions = generate_real_ai_quiz(topic, num_q)
                if real_questions:
                    st.session_state.quiz_questions.extend(real_questions)
                    st.success("✅ AI đã soạn xong! Hãy kiểm tra lại ở phần bên dưới.")

with tab_manual:
    st.markdown("### Tự thiết kế câu hỏi")
    with st.container(border=True):
        manual_q = st.text_input("Nội dung câu hỏi")
        c1, c2 = st.columns(2)
        with c1:
            opt_a = st.text_input("Đáp án 1", key="opt_a")
            opt_b = st.text_input("Đáp án 2", key="opt_b")
        with c2:
            opt_c = st.text_input("Đáp án 3", key="opt_c")
            opt_d = st.text_input("Đáp án 4", key="opt_d")
            
        correct_opt = st.selectbox("Đâu là đáp án đúng?", ["Đáp án A", "Đáp án B", "Đáp án C", "Đáp án D"])
        
        if st.button("➕ Thêm vào bộ Quiz"):
            if manual_q and opt_a and opt_b and opt_c and opt_d:
                # Ép tiền tố A, B, C, D cho nhập thủ công
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

# ================= PHẦN HIỂN THỊ & LƯU TRỮ VÀO DATABASE =================
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
                    st.session_state.quiz_questions.pop(i)
                    st.rerun()
        
    st.markdown("<br>", unsafe_allow_html=True)
    
    if st.button("💾 LƯU BỘ ĐỀ VÀO KHO HỌC LIỆU", type="primary", use_container_width=True):
        if not quiz_title:
            st.error("⚠️ Vui lòng đặt tên cho bộ Quiz trước khi lưu.")
        else:
            new_quiz = {
                "title": quiz_title,
                "questions": st.session_state.quiz_questions,
                "created_at": datetime.now().strftime("%d/%m/%Y %H:%M")
            }
            
            # BẮN API LƯU XUỐNG MONGODB
            try:
                response = requests.post(API_URL_QUIZZES, json=new_quiz)
                if response.status_code in [200, 201]:
                    st.success(f"🎉 Đã lưu thành công bộ đề '{quiz_title}' vào Database thật! Đang chuyển sang Kho Học Liệu...")
                    st.session_state.quiz_questions = [] # Xóa sạch bộ nhớ tạm sau khi lưu thành công
                    time.sleep(1.5)
                    st.switch_page("pages/teacher/kho_hoc_lieu.py")
                else:
                    st.error("⚠️ Lỗi khi lưu vào Database. Vui lòng thử lại!")
            except Exception as e:
                st.error(f"⚠️ Mất kết nối đến Backend Database: {e}")
else:
    st.info("💡 Chưa có câu hỏi nào. Hãy sử dụng AI hoặc tự nhập câu hỏi ở phía trên để bắt đầu.")