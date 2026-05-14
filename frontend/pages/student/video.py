import streamlit as st
import requests
import time
import re
import html
import urllib.parse # Thư viện mã hóa tên để gọi API không bị lỗi
import os

st.set_page_config(page_title="Rạp Chiếu Video AI", page_icon="🎬", layout="wide")

# ================= HÀM ĐỌC FILE CSS (SỬA LỖI ĐƯỜNG DẪN) =================
def load_css(file_name):
    """
    Tự động tìm file CSS trong thư mục frontend/CSS/
    file_name: tên file kèm thư mục con, ví dụ 'student/video.css'
    """
    # Lấy đường dẫn tuyệt đối đến thư mục chứa file video.py hiện tại
    current_dir = os.path.dirname(os.path.abspath(__file__)) # Đang ở frontend/pages/student
    
    # Tìm đường dẫn đến thư mục CSS (lùi 2 cấp từ pages/student/ rồi vào CSS/)
    css_root = os.path.abspath(os.path.join(current_dir, "../../CSS"))
    full_path = os.path.join(css_root, file_name)

    if os.path.exists(full_path):
        with open(full_path, "r", encoding="utf-8") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    else:
        st.warning(f"⚠️ Không tìm thấy file CSS tại: {full_path}")

# Tải file CSS (Chỉ cần truyền phần sau thư mục CSS/)
load_css("student/video.css")


# ================= HÀM LẤY THUMBNAIL YOUTUBE =================
def get_yt_thumbnail(url):
    pattern = r"(?:v=|\/)([0-9A-Za-z_-]{11}).*"
    match = re.search(pattern, str(url))
    if match:
        return f"https://img.youtube.com/vi/{match.group(1)}/hqdefault.jpg"
    return "https://via.placeholder.com/320x180.png?text=Video"

# ================= HÀM LẤY TÊN USER =================
def get_current_username():
    """Lấy tên tài khoản thật từ hệ thống"""
    if "username" in st.session_state and st.session_state.username: return st.session_state.username
    if "full_name" in st.session_state and st.session_state.full_name: return st.session_state.full_name
    if "user_info" in st.session_state and isinstance(st.session_state.user_info, dict):
        return st.session_state.user_info.get("full_name", st.session_state.user_info.get("name", "Học sinh"))
    return "Học sinh"

# ================= HÀM BẮN API LƯU BÌNH LUẬN =================
def submit_comment(vid_id):
    cmt_text = st.session_state.get(f"input_cmt_{vid_id}", "")
    if cmt_text.strip():
        real_name = get_current_username()
        new_comment = {"author": real_name, "text": cmt_text.strip()}
        
        try:
            requests.post(f"http://127.0.0.1:8000/api/tv2/videos/{vid_id}/comments", json=new_comment)
            time.sleep(0.2) 
        except:
            pass 
            
    st.session_state[f"input_cmt_{vid_id}"] = ""

if "student_profile" not in st.session_state:
    st.session_state.student_profile = {"name": "Học sinh", "exp": 0, "completed_tasks": []}
if "selected_video" not in st.session_state:
    st.session_state.selected_video = None

# GỌI API LẤY DATA
API_URL = "http://127.0.0.1:8000/api/tv2/videos"
try:
    response = requests.get(API_URL)
    ai_videos = response.json() if response.status_code == 200 else []
except:
    ai_videos = []

# -------------------------------------------------------------------------
# VIEW 1: TRANG CHỦ (GRID 4 CỘT)
# -------------------------------------------------------------------------
if st.session_state.selected_video is None:
    st.title("🍿 Rạp Chiếu Video Bài Giảng")
    search_term = st.text_input("🔍 Tìm kiếm bài học...", placeholder="Nhập tên video...")
    filtered = [v for v in ai_videos if search_term.lower() in v.get('title','').lower()]

    if not filtered:
        st.info("Chưa có video nào phù hợp.")
    else:
        cols_per_row = 4
        for i in range(0, len(filtered), cols_per_row):
            cols = st.columns(cols_per_row, gap="medium")
            for j in range(cols_per_row):
                idx = i + j
                if idx < len(filtered):
                    v = filtered[idx]
                    with cols[j]:
                        st.image(get_yt_thumbnail(v['url']), use_container_width=True)
                        st.markdown(f"<div class='grid-title' title='{html.escape(v['title'])}'>{html.escape(v['title'])}</div>", unsafe_allow_html=True)
                        if v['id'] in st.session_state.student_profile['completed_tasks']:
                            st.markdown("<div class='grid-info'>✅ Đã xem | 📌 " + html.escape(v.get('topic', 'Khác')) + "</div>", unsafe_allow_html=True)
                        else:
                            st.markdown("<div class='grid-info'>⭐ +30 EXP | 📌 " + html.escape(v.get('topic', 'Khác')) + "</div>", unsafe_allow_html=True)
                        
                        if st.button("Xem ngay", key=f"home_{v['id']}", use_container_width=True):
                            st.session_state.selected_video = v
                            st.rerun()
    st.divider()
    if st.button("⬅️ Quay lại Bảng Điều Khiển"):
        st.switch_page("pages/student/dashboard.py")

# -------------------------------------------------------------------------
# VIEW 2: CHI TIẾT PLAYER
# -------------------------------------------------------------------------
else:
    current_v = next((vid for vid in ai_videos if vid["id"] == st.session_state.selected_video["id"]), st.session_state.selected_video)
    st.session_state.selected_video = current_v 
    
    vid_id = current_v['id']
    is_completed = vid_id in st.session_state.student_profile['completed_tasks']
    real_name = get_current_username()
    encoded_name = urllib.parse.quote(real_name)

    nav_c1, nav_c2, _ = st.columns([2, 2, 6])
    with nav_c1:
        if st.button("⬅️ Danh sách Video", use_container_width=True):
            st.session_state.selected_video = None
            st.rerun()
    with nav_c2:
        if st.button("🏠 Về Góc Học Tập", use_container_width=True):
            st.switch_page("pages/student/dashboard.py")

    col_video, col_playlist = st.columns([7, 3], gap="large")

    with col_video:
        try: st.video(current_v['url'])
        except: st.error("Link video không hợp lệ!")
        
        safe_title = html.escape(current_v.get('title', ''))
        st.markdown(f"<div class='yt-title'>{safe_title}</div>", unsafe_allow_html=True)
        st.markdown(f"<div class='yt-stats'>📌 Chủ đề: {html.escape(current_v.get('topic',''))} • 📊 Trình độ: {html.escape(current_v.get('level',''))} • 🎁 Phần thưởng: +30 EXP</div>", unsafe_allow_html=True)
        
        liked_by_list = current_v.get("liked_by", [])
        total_likes = current_v.get("likes", 0)
        has_liked = real_name in liked_by_list

        btn_c1, btn_c2, _ = st.columns([2.5, 3, 4.5]) 
        with btn_c1:
            like_icon = f"❤️ Đã Thích ({total_likes})" if has_liked else f"👍 Thích ({total_likes})"
            if st.button(like_icon, key=f"like_{vid_id}", use_container_width=True):
                try:
                    requests.post(f"http://127.0.0.1:8000/api/tv2/videos/{vid_id}/like", json={"username": real_name})
                    time.sleep(0.2)
                    st.rerun()
                except:
                    st.toast("⚠️ Lỗi kết nối API!")
                    
        with btn_c2:
            if not is_completed:
                if st.button("✅ Hoàn thành bài học", type="primary", use_container_width=True):
                    submit_payload = {"video_id": vid_id, "exp_earned": 30}
                    try:
                        requests.post(f"http://127.0.0.1:8000/api/tv2/student/{encoded_name}/complete-video", json=submit_payload, timeout=5)
                    except Exception as e:
                        st.toast("⚠️ Có lỗi khi lưu dữ liệu lên server.")

                    st.session_state.student_profile['completed_tasks'].append(vid_id)
                    st.session_state.student_profile['exp'] += 30
                    st.toast("🎉 Đã hoàn thành! Nhận +30 EXP")
                    time.sleep(0.5)
                    st.rerun()
            else:
                st.button("✨ Đã hoàn thành", disabled=True, use_container_width=True)
                
        st.divider()

        db_comments = current_v.get("comments", [])
        db_comments.reverse() 
        
        st.markdown(f"<h4>{len(db_comments)} Bình luận</h4>", unsafe_allow_html=True)
        
        st.text_input(
            "Thêm bình luận (Nhấn Enter để gửi)...", 
            key=f"input_cmt_{vid_id}", 
            label_visibility="collapsed",
            placeholder="Viết bình luận của bạn...",
            on_change=submit_comment,
            args=(vid_id,)
        )

        st.markdown('<div class="cmt-list-container">', unsafe_allow_html=True)
        for cmt in db_comments:
            if isinstance(cmt, dict):
                author = cmt.get("author", "Ẩn danh")
                text = cmt.get("text", "")
            else:
                author = "Khách" 
                text = str(cmt)

            safe_author = html.escape(author)
            safe_text = html.escape(text)
            display_handle = safe_author.replace(" ", "")
            avatar_char = safe_author[0].upper() if safe_author else "U"

            st.markdown(f"""
            <div class="cmt-container">
                <div class="cmt-avatar">{avatar_char}</div>
                <div class="cmt-content">
                    <div class="cmt-name">@{display_handle}</div>
                    <div class="cmt-text">{safe_text}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    with col_playlist:
        st.markdown("#### 🎞️ Danh sách bài học")
        with st.container(height=650, border=False):
            for v in ai_videos:
                if v['id'] == vid_id: continue 
                
                with st.container(border=True):
                    st.markdown(f"""
                    <div style="display: flex; align-items: flex-start; gap: 10px; margin-bottom: 8px;">
                        <img src="{get_yt_thumbnail(v['url'])}" style="width: 45%; border-radius: 6px; object-fit: cover; aspect-ratio: 16/9;">
                        <div style="width: 55%;">
                            <div class="yt-sidebar-title" title="{html.escape(v['title'])}">{html.escape(v['title'])}</div>
                            <div class="yt-sidebar-author">iKids Education</div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    if st.button("▶ Xem bài này", key=f"play_{v['id']}", use_container_width=True):
                        st.session_state.selected_video = v
                        st.rerun()