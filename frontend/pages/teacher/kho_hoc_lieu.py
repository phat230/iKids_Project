import streamlit as st
import requests
import time
import copy
import os

st.set_page_config(page_title="Kho Học Liệu AI", page_icon="📚", layout="wide")

# ================= HÀM ĐỌC FILE CSS (SỬA LỖI ĐƯỜNG DẪN) =================
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
load_css("teacher/kho_hoc_lieu.css")

# ================= KẾT NỐI API BACKEND =================
API_URL_VIDEOS = "http://127.0.0.1:8000/api/tv2/videos"
API_URL_QUIZZES = "http://127.0.0.1:8000/api/tv2/quizzes"

def get_teacher_info():
    if "user_info" in st.session_state:
        info = st.session_state.user_info
        email = info.get("email", "khach@gmail.com")
        name = info.get("full_name", info.get("name", info.get("username", email.split('@')[0])))
        return email, name
    return "khach@gmail.com", "Khách"

teacher_email, teacher_name = get_teacher_info()

# Lấy dữ liệu từ DB
@st.cache_data(ttl=10)
def fetch_data(url):
    try:
        res = requests.get(url, timeout=5)
        return res.json() if res.status_code == 200 else []
    except: return []

ai_videos = fetch_data(API_URL_VIDEOS)
saved_quizzes = fetch_data(API_URL_QUIZZES)

if "selected_quiz" not in st.session_state: st.session_state.selected_quiz = None
if "is_editing" not in st.session_state: st.session_state.is_editing = False

st.title("Kho Bài Tập và Video")
st.write(f"Đang đăng nhập: **{teacher_name}** ({teacher_email})")

tab_quiz, tab_video = st.tabs(["Danh Sách Bộ Đề", "Thêm Video Bài Tập"])

# ----------------- TAB 1: QUẢN LÝ BỘ ĐỀ QUIZ -----------------
with tab_quiz:
    if not saved_quizzes:
        st.info("💡 Kho đề đang trống. Hãy sang trang 'Tạo Bài Tập AI' để thiết kế bộ đề mới!")
    else:
        col_list, col_detail = st.columns([1, 2])
        
        with col_list:
            st.subheader("Danh Sách Đề")
            for i, q in enumerate(saved_quizzes):
                qid = q.get('id', str(i))
                author_name = q.get("author", q.get("author_email", "Hệ thống"))
                with st.container(border=True):
                    st.markdown(f"**{q.get('title', 'Chưa có tên')}**")
                    st.caption(f"👤 Tác giả: {author_name} | Số câu hỏi: {len(q.get('questions', []))}")
                    if st.button("Xem chi tiết", key=f"view_{qid}", use_container_width=True):
                        st.session_state.selected_quiz, st.session_state.is_editing = q, False
                        st.rerun()

        with col_detail:
            if st.session_state.selected_quiz is None:
                st.info(" Vui lòng chọn một bộ đề ở danh sách bên trái để xem chi tiết.")
            else:
                qd = st.session_state.selected_quiz
                qid = qd.get('id')
                is_owner = (qd.get("author_email") == teacher_email)

                with st.container(border=True):
                    if not st.session_state.is_editing:
                        st.markdown(f"###  {qd.get('title')}")
                        st.caption(f"👤 Người soạn đề: **{qd.get('author')}** | Ngày tạo: {qd.get('created_at', 'N/A')}")
                        
                        c1, c2, c3 = st.columns(3)
                        with c1:
                            if st.button(" Giao Bài Tập Này", type="primary", use_container_width=True):
                                st.session_state.selected_quiz_to_assign = qd.get('title')
                                st.switch_page("pages/teacher/giao_bai.py")
                        with c2:
                            if st.button(" Chỉnh Sửa", disabled=not is_owner, use_container_width=True):
                                st.session_state.is_editing = True
                                st.rerun()
                        with c3:
                            if st.button(" Xóa Bài Tập ", disabled=not is_owner, use_container_width=True):
                                if requests.delete(f"{API_URL_QUIZZES}/{qid}?author={teacher_email}").status_code == 200:
                                    st.success("Đã xóa!"); st.session_state.selected_quiz = None
                                    time.sleep(1); st.rerun()
                        
                        st.divider()
                        for idx, item in enumerate(qd.get("questions", [])):
                            st.markdown(f"**Câu {idx + 1}: {item.get('question')}**")
                            for opt in item.get('options', []):
                                if opt.startswith(item.get('correct_answer', '')): st.success(f"✅ {opt}")
                                else: st.write(opt)
                            st.write("---")
                    else:
                        st.markdown("###  Chỉnh Sửa Bài Tập")
                        new_title = st.text_input("Tên bộ đề", value=qd.get('title'))
                        new_qs = copy.deepcopy(qd.get("questions", []))
                        
                        for idx, item in enumerate(new_qs):
                            st.markdown(f"<div class='edit-box'>**Câu {idx + 1}:**", unsafe_allow_html=True)
                            item["question"] = st.text_input("Nội dung", value=item.get('question'), key=f"eq_{idx}", label_visibility="collapsed")
                            opts = item.get('options', ["", "", "", ""])
                            while len(opts) < 4: opts.append("") 
                            
                            o_cols = st.columns(2)
                            o0 = o_cols[0].text_input("A", value=opts[0], key=f"o_{idx}_0")
                            o1 = o_cols[0].text_input("B", value=opts[1], key=f"o_{idx}_1")
                            o2 = o_cols[1].text_input("C", value=opts[2], key=f"o_{idx}_2")
                            o3 = o_cols[1].text_input("D", value=opts[3], key=f"o_{idx}_3")
                            item["options"] = [o0, o1, o2, o3]
                            
                            cur_correct = item.get('correct_answer', "")
                            def_idx = opts.index(cur_correct) if cur_correct in opts else 0
                            item["correct_answer"] = st.selectbox("Đáp án đúng:", options=item["options"], index=def_idx, key=f"cor_{idx}")
                            st.markdown("</div>", unsafe_allow_html=True)
                        
                        cs, cc = st.columns(2)
                        if cs.button(" LƯU THAY ĐỔI", type="primary", use_container_width=True):
                            if requests.put(f"{API_URL_QUIZZES}/{qid}?author={teacher_email}", json={"title": new_title, "questions": new_qs}).status_code == 200:
                                st.success("Lưu thành công!"); st.session_state.is_editing = False
                                time.sleep(1); st.rerun()
                        if cc.button("HỦY BỎ", use_container_width=True):
                            st.session_state.is_editing = False; st.rerun()

# ----------------- TAB 2: KHO VIDEO AI -----------------
with tab_video:
    st.markdown("### Thêm Videp BÀi Tập Thủ Công")
    with st.expander(" Cổng Upload Video"):
        with st.form("up_vid"):
            vt, vu = st.text_input("Tên video:"), st.text_input("Youtube URL:")
            c1, c2 = st.columns(2)
            v_top = c1.selectbox("Chủ đề:", ["Tiếng Anh", "Toán", "Khoa học", "Khác"])
            v_lev = c2.selectbox("Trình độ:", ["Mẫu giáo", "Lớp 1", "Lớp 2", "Lớp 3", "Lớp 4", "Lớp 5"])
            if st.form_submit_button("Tải Video Lên"):
                if vt and vu:
                    if requests.post(API_URL_VIDEOS, json={"title": vt, "url": vu, "topic": v_top, "level": v_lev, "likes": 0, "comments": []}).status_code in [200, 201]:
                        st.success("Thành công!"); time.sleep(1); st.rerun()

    if ai_videos:
        with st.container(border=True):
            f1, f2 = st.columns(2)
            ft = f1.selectbox("Chủ đề:", ["Tất cả", "Tiếng Anh", "Toán", "Khoa học", "Khác"])
            fl = f2.selectbox("Trình độ:", ["Tất cả", "Mẫu giáo", "Lớp 1", "Lớp 2", "Lớp 3", "Lớp 4", "Lớp 5"])

        for i, vid in enumerate(ai_videos):
            if ft != "Tất cả" and vid.get('topic') != ft: continue
            if fl != "Tất cả" and vid.get('level') != fl: continue
            
            st.markdown(f'<div class="video-card"><h4>{vid.get("title")}</h4><span class="tag-badge">📚 {vid.get("topic")}</span><span class="tag-badge">🎓 {vid.get("level")}</span></div>', unsafe_allow_html=True)
            v_c1, v_c2 = st.columns([3, 2])
            with v_c1:
                try: st.video(vid.get('url'))
                except: st.error("Link lỗi")
            with v_c2:
                st.write(f"**❤️ {vid.get('likes', 0)} Lượt thích**")
                if st.button("👍 Thích Video Này", key=f"lk_{i}", use_container_width=True): st.info("API Like đang bảo trì")
                if st.button("Gán Vào Lớp Học", key=f"as_{i}", type="primary", use_container_width=True): st.success("Đã gán!")
                st.write("---")
                st.write("**💬 Bình luận:**")
                for c in vid.get('comments', []): st.caption(f"- {c}")
                with st.form(f"cm_{i}"):
                    if st.form_submit_button("Gửi bình luận"): st.info("Tính năng đang phát triển")
            st.write("---")