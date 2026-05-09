import streamlit as st
import time

st.set_page_config(page_title="Kho Học Liệu AI", page_icon="📚", layout="wide")

# ================= XÓA TRIỆT ĐỂ BÓNG MA DỮ LIỆU ẢO TỪ CACHE CŨ =================
if "ai_videos" in st.session_state:
    # Nếu phát hiện video ảo (có link dQw4w9WgXcQ) còn kẹt trong bộ nhớ, lập tức xóa sạch!
    for vid in st.session_state.ai_videos:
        if "dQw4w9WgXcQ" in vid.get("url", ""):
            st.session_state.ai_videos = []
            break

# ================= KHỞI TẠO BỘ NHỚ TRỐNG 100% =================
if "saved_quizzes" not in st.session_state:
    st.session_state.saved_quizzes = []

if "ai_videos" not in st.session_state:
    st.session_state.ai_videos = []

# ================= CSS TÙY CHỈNH =================
st.markdown("""
    <style>
    .repo-card { background-color: white; padding: 20px; border-radius: 12px; border-left: 5px solid #4F46E5; box-shadow: 0 4px 6px rgba(0,0,0,0.05); margin-bottom: 20px; }
    .video-card { background-color: white; padding: 20px; border-radius: 12px; border: 1px solid #e2e8f0; margin-bottom: 20px; }
    .tag-badge { background-color: #E0E7FF; color: #4338CA; padding: 4px 8px; border-radius: 6px; font-size: 0.85rem; font-weight: 600; margin-right: 5px; }
    </style>
""", unsafe_allow_html=True)

st.title("📚 Kho Học Liệu & AI-Video Hub")
st.write("Quản lý bài tập của bạn và duyệt các tài nguyên video do bộ phận AI nội bộ trung tâm sản xuất.")

tab_quiz, tab_video = st.tabs(["📝 Bộ Đề Quiz (Của Bạn)", "🎬 AI-Video Hub (Duyệt Video)"])

# ----------------- TAB 1: QUẢN LÝ BỘ ĐỀ QUIZ -----------------
with tab_quiz:
    st.subheader("Danh sách bộ đề hiện có")
    if not st.session_state.saved_quizzes:
        st.info("💡 Kho đề của bạn đang trống. Hãy sang trang 'Tạo Bài Tập AI' để thiết kế bộ đề mới nhé!")
    else:
        for i, q in enumerate(st.session_state.saved_quizzes):
            with st.container():
                st.markdown(f"""
                <div class="repo-card">
                    <h3 style="margin-top:0;">{q['title']}</h3>
                    <p style="margin-bottom:0;">🔢 Số câu: {len(q['questions'])} | 📅 Ngày tạo: {q.get('created_at', 'Hôm nay')}</p>
                </div>
                """, unsafe_allow_html=True)
                
                c1, c2, c3 = st.columns([1, 1, 4])
                with c1:
                    if st.button("📤 Giao Đề Này", key=f"assign_{i}", type="primary"):
                        st.session_state.selected_quiz_to_assign = q['title']
                        st.switch_page("pages/teacher/giao_bai.py")
                with c2:
                    if st.button("🗑️ Xóa", key=f"del_q_{i}"):
                        st.session_state.saved_quizzes.pop(i)
                        st.rerun()
                st.write("---")

# ----------------- TAB 2: KHO VIDEO AI (CHUẨN TÀI LIỆU) -----------------
with tab_video:
    st.markdown("### 🎬 Hệ thống Video do AI nội bộ sản xuất")
    st.caption("Theo quy trình: Nhân viên AI sẽ tải video lên. Giáo viên chỉ xem xét, đánh giá chuyên môn và giao cho lớp.")
    
    # FORM MÔ PHỎNG NHÂN VIÊN AI (CHỈ DÙNG ĐỂ ÔNG CÓ CÔNG CỤ NHẬP DATA THẬT ĐỂ TEST)
    with st.expander("🛠️ [Góc Mô Phỏng] Cổng Upload Video của Nhân viên AI"):
        st.warning("⚠️ Khu vực này thực tế thuộc về module của Admin/Nhân viên AI. Đặt tạm ở đây để bạn có chỗ nhập Video test.")
        with st.form("upload_video_form"):
            v_title = st.text_input("Tên video AI:")
            v_url = st.text_input("Đường dẫn (URL Youtube THẬT):", placeholder="Ví dụ: https://www.youtube.com/watch?v=...")
            c1, c2 = st.columns(2)
            with c1:
                v_topic = st.selectbox("Chủ đề:", ["Tiếng Anh", "Toán", "Khoa học", "Khác"])
            with c2:
                v_level = st.selectbox("Trình độ:", ["Mẫu giáo", "Lớp 1", "Lớp 2", "Lớp 3", "Lớp 4", "Lớp 5"])
            
            if st.form_submit_button("Tải Video Lên Hệ Thống"):
                if v_title and v_url:
                    st.session_state.ai_videos.append({
                        "id": f"vid_{int(time.time())}", "title": v_title, "url": v_url,
                        "topic": v_topic, "level": v_level, "likes": 0, "comments": []
                    })
                    st.success("Nhân viên AI đã tải video thành công!")
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error("Vui lòng điền đủ Tên và URL video.")

    st.divider()

    # KHU VỰC HIỂN THỊ CỦA GIÁO VIÊN
    if not st.session_state.ai_videos:
        st.info("Chưa có video AI nào trên hệ thống. (Hãy mở phần mô phỏng ở trên để tải lên 1 video thật nhé!)")
    else:
        with st.container(border=True):
            col_f1, col_f2 = st.columns(2)
            with col_f1: filter_topic = st.selectbox("Lọc theo Chủ đề:", ["Tất cả", "Tiếng Anh", "Toán", "Khoa học", "Khác"])
            with col_f2: filter_level = st.selectbox("Lọc theo Trình độ:", ["Tất cả", "Mẫu giáo", "Lớp 1", "Lớp 2", "Lớp 3", "Lớp 4", "Lớp 5"])

        for i, vid in enumerate(st.session_state.ai_videos):
            if filter_topic != "Tất cả" and vid['topic'] != filter_topic: continue
            if filter_level != "Tất cả" and vid['level'] != filter_level: continue
            
            with st.container():
                st.markdown(f"""
                <div class="video-card">
                    <h4 style="margin-top:0;">{vid['title']}</h4>
                    <span class="tag-badge">📚 {vid['topic']}</span>
                    <span class="tag-badge">🎓 {vid['level']}</span>
                </div>
                """, unsafe_allow_html=True)
                
                v_col1, v_col2 = st.columns([3, 2])
                with v_col1:
                    try: st.video(vid['url'])
                    except: st.error("Link video không hợp lệ")
                
                with v_col2:
                    st.markdown(f"**❤️ {vid['likes']} Lượt thích từ Giáo viên**")
                    if st.button(f"👍 Thích Video Này", key=f"like_{vid['id']}", use_container_width=True):
                        vid['likes'] += 1
                        st.rerun()
                    if st.button("📤 Gán video này vào lớp học", key=f"assign_v_{vid['id']}", type="primary", use_container_width=True):
                        st.success("✅ Đã gán video vào bài giảng! Học sinh xem sẽ được cộng EXP.")
                    
                    st.write("---")
                    st.write("**💬 Bình luận chuyên môn:**")
                    if not vid['comments']:
                        st.caption("Chưa có bình luận nào.")
                    for cmt in vid['comments']: st.caption(f"- {cmt}")
                    
                    with st.form(key=f"cmt_form_{vid['id']}"):
                        new_cmt = st.text_input("Góp ý chuyên môn của bạn:")
                        if st.form_submit_button("Gửi bình luận"):
                            if new_cmt:
                                vid['comments'].append(new_cmt)
                                st.rerun()
                st.write("---")