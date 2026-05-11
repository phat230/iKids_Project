import streamlit as st
import requests
import time
import re
import html

st.set_page_config(page_title="Rạp Chiếu Video AI", page_icon="📺", layout="wide")

# ================= HÀM UTILS =================
def get_yt_thumbnail(url):
    pattern = r"(?:v=|\/)([0-9A-Za-z_-]{11}).*"
    match = re.search(pattern, str(url))
    if match:
        return f"https://img.youtube.com/vi/{match.group(1)}/hqdefault.jpg"
    return "https://via.placeholder.com/320x180.png?text=Video"

# ================= CSS NÂNG CẤP GIAO DIỆN =================
st.markdown("""
    <style>
    /* Tổng thể Player */
    .main-player-header {
        background: #ffffff; padding: 15px; border-radius: 12px;
        border-bottom: 3px solid #4F46E5; margin-bottom: 20px;
    }
    /* Danh sách video liên quan bên phải */
    .playlist-container {
        background: #f8fafc; padding: 15px; border-radius: 12px;
        border: 1px solid #e2e8f0; max-height: 400px; overflow-y: auto;
    }
    .playlist-item {
        display: flex; gap: 10px; padding: 10px; border-radius: 8px;
        background: white; margin-bottom: 10px; border: 1px solid #f1f5f9;
        cursor: pointer; transition: 0.3s;
    }
    .playlist-item:hover { background: #eef2ff; border-color: #4F46E5; }
    
    /* Bình luận */
    .comment-section {
        background: #ffffff; padding: 15px; border-radius: 12px;
        border: 1px solid #e2e8f0; margin-top: 20px;
    }
    .comment-box {
        background-color: #f1f5f9; padding: 10px 15px; border-radius: 8px;
        margin-bottom: 8px; font-size: 0.9rem;
    }
    </style>
""", unsafe_allow_html=True)

if "student_profile" not in st.session_state:
    st.session_state.student_profile = {"name": "Học sinh", "exp": 0, "completed_tasks": []}
if "selected_video" not in st.session_state:
    st.session_state.selected_video = None

# Gọi API lấy dữ liệu
API_URL = "http://127.0.0.1:8000/api/tv2/videos"
try:
    response = requests.get(API_URL)
    ai_videos = response.json() if response.status_code == 200 else []
except:
    ai_videos = []

# -------------------------------------------------------------------------
# VIEW 1: GRID DANH SÁCH (TRANG CHỦ RẠP)
# -------------------------------------------------------------------------
if st.session_state.selected_video is None:
    st.title("📺 Rạp Chiếu Video AI")
    search_term = st.text_input("🔍 Tìm kiếm bài học...", placeholder="Nhập tên video...")
    filtered = [v for v in ai_videos if search_term.lower() in v.get('title','').lower()]

    if not filtered:
        st.info("Chưa có video nào.")
    else:
        rows = (len(filtered) + 3) // 4
        for i in range(rows):
            cols = st.columns(4)
            for j in range(4):
                idx = i * 4 + j
                if idx < len(filtered):
                    v = filtered[idx]
                    with cols[j]:
                        st.image(get_yt_thumbnail(v['url']), use_container_width=True)
                        st.write(f"**{v['title']}**")
                        if st.button("Xem ngay", key=f"btn_{v['id']}", use_container_width=True):
                            st.session_state.selected_video = v
                            st.rerun()
# -------------------------------------------------------------------------
# VIEW 2: CHI TIẾT PLAYER (XỬ LÝ CÁI KHUNG TRẮNG)
# -------------------------------------------------------------------------
else:
    current_v = st.session_state.selected_video
    vid_id = current_v['id']
    
    if st.button("⬅️ Trở về danh sách"):
        st.session_state.selected_video = None
        st.rerun()

    # Layout chính: Trái (Player) - Phải (Playlist & Chat)
    col_left, col_right = st.columns([7, 3], gap="medium")

    with col_left:
        # 1. Header video hiện tại
        st.markdown(f"""
        <div class="main-player-header">
            <h2 style='margin:0;'>{html.escape(current_v['title'])}</h2>
            <p style='color:gray; margin:0;'>📚 {current_v.get('topic','')} | 🎓 {current_v.get('level','')}</p>
        </div>
        """, unsafe_allow_html=True)
        
        # 2. Player
        st.video(current_v['url'])
        
        # 3. Nút hành động
        c1, c2 = st.columns(2)
        with c1:
            if st.button("❤️ Thích Video", key=f"lk_{vid_id}", use_container_width=True):
                st.toast("Đã thêm vào yêu thích!")
        with c2:
            is_done = vid_id in st.session_state.student_profile['completed_tasks']
            if not is_done:
                if st.button("✅ Hoàn thành bài học", key=f"dn_{vid_id}", type="primary", use_container_width=True):
                    st.session_state.student_profile['completed_tasks'].append(vid_id)
                    st.session_state.student_profile['exp'] += 30
                    st.rerun()
            else:
                st.success("Bạn đã hoàn thành bài học này! ✨")

    with col_right:
        # 4. DANH SÁCH VIDEO LIÊN QUAN (Lấp đầy khung trắng)
        st.markdown("### 📽️ Video khác")
        with st.container():
            for v in ai_videos:
                if v['id'] == vid_id: continue # Bỏ qua video đang xem
                
                # Tạo item playlist thủ công bằng button để có thể click
                with st.expander(f"▶️ {v['title'][:30]}...", expanded=False):
                    st.image(get_yt_thumbnail(v['url']), use_container_width=True)
                    if st.button("Chuyển bài", key=f"switch_{v['id']}", use_container_width=True):
                        st.session_state.selected_video = v
                        st.rerun()

        # 5. THẢO LUẬN
        st.markdown("### 💬 Thảo luận")
        if f"comments_{vid_id}" not in st.session_state:
            st.session_state[f"comments_{vid_id}"] = current_v.get('comments', [])
            
        with st.container():
            for c in st.session_state[f"comments_{vid_id}"]:
                st.markdown(f"<div class='comment-box'><b>Học sinh:</b> {html.escape(c)}</div>", unsafe_allow_html=True)
        
        with st.form(f"f_{vid_id}", clear_on_submit=True):
            msg = st.text_input("Góp ý...", placeholder="Nhập bình luận...")
            if st.form_submit_button("Gửi"):
                if msg:
                    st.session_state[f"comments_{vid_id}"].append(msg)
                    st.rerun()