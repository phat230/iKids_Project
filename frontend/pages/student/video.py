import streamlit as st
import requests
import time
import re
import html
import urllib.parse  # Thư viện mã hóa tên để gọi API không bị lỗi
import os

# ================= CRITICAL: CẤU HÌNH TRANG LUÔN ĐỂ ĐẦU FILE =================
st.set_page_config(page_title="Rạp Chiếu Video AI", page_icon="🎬", layout="wide")

# ================= HÀM ĐỌC FILE CSS (SỬA LỖI ĐƯỜNG DẪN) =================
def load_css(file_name):
    """
    Tự động tìm file CSS trong thư mục frontend/CSS/
    file_name: tên file kèm thư mục con, ví dụ 'student/video.css'
    """
    current_dir = os.path.dirname(os.path.abspath(__file__))  # Đang ở frontend/pages/student
    css_root = os.path.abspath(os.path.join(current_dir, "../../CSS"))
    full_path = os.path.join(css_root, file_name)

    if os.path.exists(full_path):
        with open(full_path, "r", encoding="utf-8") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    else:
        st.warning(f"⚠️ Không tìm thấy file CSS tại: {full_path}")

# Tải file CSS
load_css("student/student_global.css")
BACKEND_URL = st.session_state.get("api_url", "http://localhost:8000")
API_URL = BACKEND_URL
lang = st.session_state.get("lang", "vi")

# ==========================================
# BỘ TỪ ĐIỂN SONG NGỮ CHI TIẾT CHO STUDENT VIDEO PLAYER
# ==========================================
VIDEO_LABELS = {
    "vi": {
        "title": "🎬 Rạp Chiếu Video Bài Giảng",
        "search_placeholder": "🔍 Tìm Kiếm Bài Học...",
        "search_hint": "Nhập tên video...",
        "info_empty": "Chưa có video nào phù hợp.",
        "lbl_completed": "✅ Đã xem",
        "lbl_reward_hint": "⭐ +30 EXP",
        "btn_watch": "Xem ngay",
        "btn_back_dashboard": "Leave ⬅ Quay lại Bảng Điều Khiển",
        
        # Màn hình Player chi tiết
        "btn_back_list": "⬅ Quay lại danh sách Video",
        "btn_back_hub": "🏠 Về Góc Học Tập",
        "err_invalid_link": "❌ Link video không hợp lệ hoặc bị lỗi đường truyền!",
        "lbl_topic": "Chủ đề:",
        "lbl_level": "Trình độ:",
        "lbl_reward": "🎁 Phần thưởng:",
        "btn_like_done": "❤️ Đã Thích ({})",
        "btn_like": "👍 Thích ({})",
        "btn_complete_lesson": "✅ Hoàn thành bài học",
        "btn_completed_lesson": "🔒 Đã hoàn thành",
        "toast_api_err": "⚠️ Lỗi kết nối API máy chủ!",
        "toast_save_err": "⚠️ Có lỗi khi lưu dữ liệu lên server.",
        "toast_success_exp": "🎉 Xuất sắc! Nhận +30 EXP",
        
        # Bình luận
        "lbl_comments_count": "Bình luận",
        "cmt_placeholder": "Viết bình luận của bạn (Nhấn Enter để gửi)...",
        "author_anonymous": "Ẩn danh",
        "author_guest": "Khách",
        
        # Playlist bên cạnh
        "playlist_title": "📂 Danh Sách Bài Học",
        "btn_sidebar_play": "▶ Xem bài này",
        "default_topic": "Khác"
    },
    "en": {
        "title": "🎬 AI Animated Video Theater",
        "search_placeholder": "🔍 Search Video Lessons...",
        "search_hint": "Enter video title here...",
        "info_empty": "No matching video lessons found.",
        "lbl_completed": "✅ Watched",
        "lbl_reward_hint": "⭐ +30 EXP",
        "btn_watch": "Watch Now",
        "btn_back_dashboard": "⬅ Back to Dashboard",
        
        # Detailed Player Screen
        "btn_back_list": "⬅ Back to Video Directory",
        "btn_back_hub": "🏠 Back to Study Hub",
        "err_invalid_link": "❌ Invalid video URL or network stream error!",
        "lbl_topic": "Topic:",
        "lbl_level": "Level:",
        "lbl_reward": "🎁 Rewards:",
        "btn_like_done": "❤️ Liked ({})",
        "btn_like": "👍 Like ({})",
        "btn_complete_lesson": "✅ Complete Quest",
        "btn_completed_lesson": "🔒 Completed",
        "toast_api_err": "⚠️ Server API connection failure!",
        "toast_save_err": "⚠️ Error occurred while storing metadata metrics.",
        "toast_success_exp": "🎉 Quest Complete! Earned +30 EXP",
        
        # Comments
        "lbl_comments_count": "Comments",
        "cmt_placeholder": "Add a public comment (Press Enter to post)...",
        "author_anonymous": "Anonymous",
        "author_guest": "Guest",
        
        # Sidebar Playlist
        "playlist_title": "📂 Course Playlist",
        "btn_sidebar_play": "▶ Play Lesson",
        "default_topic": "General"
    }
}

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
        return st.session_state.user_info.get("full_name", st.session_state.user_info.get("name", "Student" if lang=='en' else "Học sinh"))
    return "Student" if lang=='en' else "Học sinh"

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

# GỌI API LẤY DATA VIDEO
API_URL = "http://127.0.0.1:8000/api/tv2/videos"
try:
    response = requests.get(API_URL)
    ai_videos = response.json() if response.status_code == 200 else []
except:
    ai_videos = []

# -------------------------------------------------------------------------
# VIEW 1: TRANG CHỦ DANH SÁCH VIDEO (GRID 4 CỘT)
# -------------------------------------------------------------------------
if st.session_state.selected_video is None:
    st.title(VIDEO_LABELS[lang]["title"])
    search_term = st.text_input(VIDEO_LABELS[lang]["search_placeholder"], placeholder=VIDEO_LABELS[lang]["search_hint"])
    filtered = [v for v in ai_videos if search_term.lower() in v.get('title','').lower()]

    if not filtered:
        st.info(VIDEO_LABELS[lang]["info_empty"])
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
                        
                        # Hiển thị trạng thái đã hoàn thành hay chưa
                        topic_display = v.get('topic', VIDEO_LABELS[lang]['default_topic'])
                        if lang == "en" and topic_display == "Khác": topic_display = "General"
                        
                        if v['id'] in st.session_state.student_profile['completed_tasks']:
                            st.markdown(f"<div class='grid-info'>{VIDEO_LABELS[lang]['lbl_completed']} | 📌 {html.escape(topic_display)}</div>", unsafe_allow_html=True)
                        else:
                            st.markdown(f"<div class='grid-info'>{VIDEO_LABELS[lang]['lbl_reward_hint']} | 📌 {html.escape(topic_display)}</div>", unsafe_allow_html=True)
                        
                        if st.button(VIDEO_LABELS[lang]["btn_watch"], key=f"home_{v['id']}", use_container_width=True):
                            st.session_state.selected_video = v
                            st.rerun()
    st.divider()
    if st.button(VIDEO_LABELS[lang]["btn_back_dashboard"]):
        st.switch_page("pages/student/dashboard.py")

# -------------------------------------------------------------------------
# VIEW 2: MÀN HÌNH CHI TIẾT PLAYER XEM VIDEO
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
        if st.button(VIDEO_LABELS[lang]["btn_back_list"], use_container_width=True):
            st.session_state.selected_video = None
            st.rerun()
    with nav_c2:
        if st.button(VIDEO_LABELS[lang]["btn_back_hub"], use_container_width=True):
            st.switch_page("pages/student/dashboard.py")

    col_video, col_playlist = st.columns([7, 3], gap="large")

    with col_video:
        try: st.video(current_v['url'])
        except: st.error(VIDEO_LABELS[lang]["err_invalid_link"])
        
        safe_title = html.escape(current_v.get('title', ''))
        st.markdown(f"<div class='yt-title'>{safe_title}</div>", unsafe_allow_html=True)
        
        topic_display = current_v.get('topic', VIDEO_LABELS[lang]['default_topic'])
        if lang == "en" and topic_display == "Khác": topic_display = "General"
        
        st.markdown(f"<div class='yt-stats'> {VIDEO_LABELS[lang]['lbl_topic']} {html.escape(topic_display)} • {VIDEO_LABELS[lang]['lbl_level']} {html.escape(current_v.get('level',''))} • {VIDEO_LABELS[lang]['lbl_reward']} +30 EXP</div>", unsafe_allow_html=True)
        
        liked_by_list = current_v.get("liked_by", [])
        total_likes = current_v.get("likes", 0)
        has_liked = real_name in liked_by_list

        btn_c1, btn_c2, _ = st.columns([2.5, 3, 4.5]) 
        with btn_c1:
            like_icon = VIDEO_LABELS[lang]["btn_like_done"].format(total_likes) if has_liked else VIDEO_LABELS[lang]["btn_like"].format(total_likes)
            if st.button(like_icon, key=f"like_{vid_id}", use_container_width=True):
                try:
                    requests.post(f"http://127.0.0.1:8000/api/tv2/videos/{vid_id}/like", json={"username": real_name})
                    time.sleep(0.2)
                    st.rerun()
                except:
                    st.toast(VIDEO_LABELS[lang]["toast_api_err"])
                    
        with btn_c2:
            if not is_completed:
                if st.button(VIDEO_LABELS[lang]["btn_complete_lesson"], type="primary", use_container_width=True):
                    submit_payload = {"video_id": vid_id, "exp_earned": 30}
                    try:
                        requests.post(f"http://127.0.0.1:8000/api/tv2/student/{encoded_name}/complete-video", json=submit_payload, timeout=5)
                    except Exception:
                        st.toast(VIDEO_LABELS[lang]["toast_save_err"])

                    st.session_state.student_profile['completed_tasks'].append(vid_id)
                    st.session_state.student_profile['exp'] += 30
                    st.toast(VIDEO_LABELS[lang]["toast_success_exp"])
                    time.sleep(0.5)
                    st.rerun()
            else:
                st.button(VIDEO_LABELS[lang]["btn_completed_lesson"], disabled=True, use_container_width=True)
                
        st.divider()

        db_comments = current_v.get("comments", [])
        db_comments.reverse() 
        
        st.markdown(f"<h4>{len(db_comments)} {VIDEO_LABELS[lang]['lbl_comments_count']}</h4>", unsafe_allow_html=True)
        
        st.text_input(
            "Thêm bình luận...", 
            key=f"input_cmt_{vid_id}", 
            label_visibility="collapsed",
            placeholder=VIDEO_LABELS[lang]["cmt_placeholder"],
            on_change=submit_comment,
            args=(vid_id,)
        )

        st.markdown('<div class="cmt-list-container">', unsafe_allow_html=True)
        for cmt in db_comments:
            if isinstance(cmt, dict):
                author = cmt.get("author", VIDEO_LABELS[lang]["author_anonymous"])
                text = cmt.get("text", "")
            else:
                author = VIDEO_LABELS[lang]["author_guest"]
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
        st.markdown(f"#### {VIDEO_LABELS[lang]['playlist_title']}")
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
                    
                    if st.button(VIDEO_LABELS[lang]["btn_sidebar_play"], key=f"play_{v['id']}", use_container_width=True):
                        st.session_state.selected_video = v
                        st.rerun()