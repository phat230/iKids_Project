import streamlit as st
import requests
import time
import copy

st.set_page_config(page_title="Kho Học Liệu AI", page_icon="📚", layout="wide")

# ================= KẾT NỐI API BACKEND =================
API_URL_VIDEOS = "http://127.0.0.1:8000/api/tv2/videos"
API_URL_QUIZZES = "http://127.0.0.1:8000/api/tv2/quizzes"

# Lấy thông tin user (ĐÃ CẬP NHẬT LẤY CHUẨN TÊN TỪ HỆ THỐNG)
def get_teacher_info():
    if "user_info" in st.session_state:
        info = st.session_state.user_info
        
        # Lấy email làm khóa bảo mật
        email = info.get("email", "khach@gmail.com")
        
        # Quét mọi key có thể chứa "Họ và tên" do TV1 thiết kế
        name = info.get("full_name", 
               info.get("name", 
               info.get("ho_ten", 
               info.get("ho_va_ten", 
               info.get("username", email.split('@')[0])))))
               
        # GÓC DEBUG: Nếu vẫn không ra tên, ông bỏ dấu # ở dòng dưới để xem hệ thống chứa key gì nhé
        # st.sidebar.write("Dữ liệu hệ thống đang có:", info)
        
        return email, name
    return "khach@gmail.com", "Khách"

teacher_email, teacher_name = get_teacher_info()

# Lấy dữ liệu
try:
    res_videos = requests.get(API_URL_VIDEOS)
    ai_videos = res_videos.json() if res_videos.status_code == 200 else []
except:
    ai_videos = []

try:
    res_quizzes = requests.get(API_URL_QUIZZES)
    saved_quizzes = res_quizzes.json() if res_quizzes.status_code == 200 else []
except:
    saved_quizzes = []

if "selected_quiz" not in st.session_state:
    st.session_state.selected_quiz = None
if "is_editing" not in st.session_state:
    st.session_state.is_editing = False

# ================= CSS TÙY CHỈNH =================
st.markdown("""
    <style>
    .repo-card { background-color: white; padding: 15px; border-radius: 8px; border-left: 4px solid #4F46E5; box-shadow: 0 2px 4px rgba(0,0,0,0.05); margin-bottom: 10px; cursor: pointer;}
    .repo-card:hover { background-color: #f8fafc; }
    .video-card { background-color: white; padding: 20px; border-radius: 12px; border: 1px solid #e2e8f0; margin-bottom: 20px; }
    .tag-badge { background-color: #E0E7FF; color: #4338CA; padding: 4px 8px; border-radius: 6px; font-size: 0.85rem; font-weight: 600; margin-right: 5px; }
    .edit-box { background-color: #f8fafc; padding: 20px; border-radius: 8px; border: 1px solid #e2e8f0; margin-bottom: 15px; }
    </style>
""", unsafe_allow_html=True)

st.title("📚 Kho Học Liệu & AI-Video Hub")
st.write(f"Đang đăng nhập: **{teacher_name}** ({teacher_email})")
st.write("Quản lý bài tập của bạn và duyệt các tài nguyên video do bộ phận AI nội bộ trung tâm sản xuất.")

tab_quiz, tab_video = st.tabs(["📝 Bộ Đề Quiz", "🎬 AI-Video Hub"])

# ----------------- TAB 1: QUẢN LÝ BỘ ĐỀ QUIZ -----------------
with tab_quiz:
    if not saved_quizzes:
        st.info("💡 Kho đề đang trống. Hãy sang trang 'Tạo Bài Tập AI' để thiết kế bộ đề mới nhé!")
    else:
        col_list, col_detail = st.columns([1, 2])
        
        # --- CỘT TRÁI: DANH SÁCH ĐỀ ---
        with col_list:
            st.subheader("Danh sách bộ đề")
            for i, q in enumerate(saved_quizzes):
                quiz_id = q.get('id', str(i))
                # HIỂN THỊ TÊN ĐẸP THAY VÌ EMAIL
                author_email_db = q.get("author_email", "Hệ thống")
                author_name_db = q.get("author", author_email_db) 
                title = q.get('title', 'Chưa có tên')
                
                with st.container(border=True):
                    st.markdown(f"**{title}**")
                    st.caption(f"👤 Tác giả: {author_name_db} | 🔢 Số câu: {len(q.get('questions', []))}")
                    if st.button("👉 Xem chi tiết", key=f"btn_view_{quiz_id}", use_container_width=True):
                        st.session_state.selected_quiz = q
                        st.session_state.is_editing = False
                        st.rerun()

        # --- CỘT PHẢI: CHI TIẾT ĐỀ HOẶC FORM SỬA ---
        with col_detail:
            if st.session_state.selected_quiz is None:
                st.info("👈 Vui lòng chọn một bộ đề ở danh sách bên trái để xem chi tiết.")
            else:
                q_detail = st.session_state.selected_quiz
                quiz_id = q_detail.get('id')
                author_email_db = q_detail.get("author_email", "Hệ thống")
                author_name_db = q_detail.get("author", author_email_db)
                
                # CHỐT QUYỀN: So sánh email của người đang đăng nhập với email trong DB
                is_owner = (author_email_db == teacher_email)

                with st.container(border=True):
                    # --- CHẾ ĐỘ XEM CHI TIẾT ---
                    if not st.session_state.is_editing:
                        st.markdown(f"### 📖 {q_detail.get('title')}")
                        st.caption(f"👤 Người ra đề: **{author_name_db}** | 📅 Tạo ngày: {q_detail.get('created_at', 'N/A')}")
                        
                        c1, c2, c3 = st.columns([2, 2, 2])
                        with c1:
                            if st.button("🚀 Giao Đề Này", type="primary", use_container_width=True):
                                st.session_state.selected_quiz_to_assign = q_detail.get('title')
                                st.switch_page("pages/teacher/giao_bai.py")
                        with c2:
                            if st.button("📝 Sửa Đề", disabled=not is_owner, use_container_width=True):
                                st.session_state.is_editing = True
                                st.rerun()
                        with c3:
                            if st.button("🗑️ Xóa", disabled=not is_owner, use_container_width=True):
                                res = requests.delete(f"{API_URL_QUIZZES}/{quiz_id}?author={teacher_email}")
                                if res.status_code == 200:
                                    st.success("Đã xóa bộ đề!")
                                    st.session_state.selected_quiz = None
                                    time.sleep(1)
                                    st.rerun()
                                else:
                                    st.error("Lỗi xóa đề!")
                        
                        st.divider()
                        for idx, q_item in enumerate(q_detail.get("questions", [])):
                            st.markdown(f"**Câu {idx + 1}: {q_item.get('question')}**")
                            for opt in q_item.get('options', []):
                                if opt.startswith(q_item.get('correct_answer', '')):
                                    st.success(f"✅ {opt}")
                                else:
                                    st.write(opt)
                            st.write("---")

                    # --- CHẾ ĐỘ SỬA ĐỀ TOÀN DIỆN ---
                    else:
                        st.markdown("### 🛠️ Chỉnh Sửa Bộ Đề")
                        new_title = st.text_input("Tên bộ đề", value=q_detail.get('title'))
                        
                        new_questions = copy.deepcopy(q_detail.get("questions", []))
                        
                        for idx, q_item in enumerate(new_questions):
                            st.markdown(f"<div class='edit-box'>", unsafe_allow_html=True)
                            st.markdown(f"**Câu {idx + 1}:**")
                            
                            # 1. Sửa nội dung câu hỏi
                            q_item["question"] = st.text_input("Nội dung", value=q_item.get('question'), key=f"edit_q_{idx}", label_visibility="collapsed")
                            
                            # 2. Sửa 4 đáp án
                            opts = q_item.get('options', ["", "", "", ""])
                            # Đảm bảo mảng luôn có 4 phần tử để tránh lỗi
                            while len(opts) < 4: opts.append("") 
                            
                            col_o1, col_o2 = st.columns(2)
                            with col_o1:
                                o0 = st.text_input("Đáp án A", value=opts[0], key=f"opt_{idx}_0")
                                o1 = st.text_input("Đáp án B", value=opts[1], key=f"opt_{idx}_1")
                            with col_o2:
                                o2 = st.text_input("Đáp án C", value=opts[2], key=f"opt_{idx}_2")
                                o3 = st.text_input("Đáp án D", value=opts[3], key=f"opt_{idx}_3")
                            
                            q_item["options"] = [o0, o1, o2, o3]
                            
                            # 3. Chọn lại đáp án đúng
                            old_correct = q_item.get('correct_answer', "")
                            try:
                                default_idx = opts.index(old_correct) if old_correct in opts else 0
                            except:
                                default_idx = 0
                                
                            q_item["correct_answer"] = st.selectbox("Chọn đáp án đúng:", options=q_item["options"], index=default_idx, key=f"corr_{idx}")
                            
                            st.markdown("</div>", unsafe_allow_html=True)
                        
                        c_save, c_cancel = st.columns([2, 2])
                        with c_save:
                            if st.button("💾 Lưu Thay Đổi", type="primary", use_container_width=True):
                                payload = {"title": new_title, "questions": new_questions}
                                res = requests.put(f"{API_URL_QUIZZES}/{quiz_id}?author={teacher_email}", json=payload)
                                if res.status_code == 200:
                                    st.success("Lưu thành công!")
                                    st.session_state.selected_quiz["title"] = new_title
                                    st.session_state.selected_quiz["questions"] = new_questions
                                    st.session_state.is_editing = False
                                    time.sleep(1)
                                    st.rerun()
                                else:
                                    st.error("Lỗi cập nhật DB!")
                        with c_cancel:
                            if st.button("❌ Hủy Bỏ", use_container_width=True):
                                st.session_state.is_editing = False
                                st.rerun()

# ----------------- TAB 2: KHO VIDEO AI (GIỮ NGUYÊN) -----------------
with tab_video:
    st.markdown("### 🎬 Hệ thống Video do AI nội bộ sản xuất")
    st.caption("Theo quy trình: Nhân viên AI sẽ tải video lên. Giáo viên chỉ xem xét, đánh giá chuyên môn và giao cho lớp.")
    
    with st.expander("🛠️ [Góc Mô Phỏng] Cổng Upload Video của Nhân viên AI"):
        st.warning("⚠️ Khu vực này thực tế thuộc về module của Admin/Nhân viên AI.")
        with st.form("upload_video_form"):
            v_title = st.text_input("Tên video AI:")
            v_url = st.text_input("Đường dẫn (URL Youtube THẬT):")
            c1, c2 = st.columns(2)
            with c1:
                v_topic = st.selectbox("Chủ đề:", ["Tiếng Anh", "Toán", "Khoa học", "Khác"])
            with c2:
                v_level = st.selectbox("Trình độ:", ["Mẫu giáo", "Lớp 1", "Lớp 2", "Lớp 3", "Lớp 4", "Lớp 5"])
            
            if st.form_submit_button("Tải Video Lên Hệ Thống"):
                if v_title and v_url:
                    payload = {"title": v_title, "url": v_url, "topic": v_topic, "level": v_level, "likes": 0, "comments": []}
                    response = requests.post(API_URL_VIDEOS, json=payload)
                    if response.status_code in [200, 201]:
                        st.success("Tải video thành công!")
                        time.sleep(1)
                        st.rerun()
                else:
                    st.error("Vui lòng điền đủ Tên và URL video.")

    st.divider()

    if not ai_videos:
        st.info("Chưa có video AI nào trên hệ thống Database.")
    else:
        with st.container(border=True):
            col_f1, col_f2 = st.columns(2)
            with col_f1: filter_topic = st.selectbox("Lọc theo Chủ đề:", ["Tất cả", "Tiếng Anh", "Toán", "Khoa học", "Khác"])
            with col_f2: filter_level = st.selectbox("Lọc theo Trình độ:", ["Tất cả", "Mẫu giáo", "Lớp 1", "Lớp 2", "Lớp 3", "Lớp 4", "Lớp 5"])

        for i, vid in enumerate(ai_videos):
            if filter_topic != "Tất cả" and vid.get('topic') != filter_topic: continue
            if filter_level != "Tất cả" and vid.get('level') != filter_level: continue
            
            with st.container():
                st.markdown(f"""
                <div class="video-card">
                    <h4 style="margin-top:0;">{vid.get('title')}</h4>
                    <span class="tag-badge">📚 {vid.get('topic')}</span>
                    <span class="tag-badge">🎓 {vid.get('level')}</span>
                </div>
                """, unsafe_allow_html=True)
                
                v_col1, v_col2 = st.columns([3, 2])
                with v_col1:
                    try: st.video(vid.get('url'))
                    except: st.error("Link video không hợp lệ")
                
                with v_col2:
                    st.markdown(f"**❤️ {vid.get('likes', 0)} Lượt thích từ Giáo viên**")
                    if st.button(f"👍 Thích Video Này", key=f"like_{vid.get('id', i)}", use_container_width=True):
                        st.success("Tính năng Like đang cập nhật API!")
                        
                    if st.button("📤 Gán video này vào lớp học", key=f"assign_v_{vid.get('id', i)}", type="primary", use_container_width=True):
                        st.success("✅ Đã gán video vào bài giảng!")
                    
                    st.write("---")
                    st.write("**💬 Bình luận chuyên môn:**")
                    if not vid.get('comments'): st.caption("Chưa có bình luận nào.")
                    for cmt in vid.get('comments', []): st.caption(f"- {cmt}")
                    
                    with st.form(key=f"cmt_form_{vid.get('id', i)}"):
                        new_cmt = st.text_input("Góp ý của bạn:")
                        if st.form_submit_button("Gửi bình luận"):
                            st.success("Chức năng bình luận đang cập nhật!")
                st.write("---")