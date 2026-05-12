import streamlit as st
import requests
import time
import re
import html
import urllib.parse # Thư viện mã hóa tên để gọi API không bị lỗi

st.set_page_config(page_title="Rạp Chiếu Video AI", page_icon="📺", layout="wide")

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
        
        # BẮN API XUỐNG BACKEND LƯU MONGODB
        try:
            requests.post(f"http://127.0.0.1:8000/api/tv2/videos/{vid_id}/comments", json=new_comment)
            time.sleep(0.2) # Đợi DB update 1 xíu
        except:
            pass # Bỏ qua nếu lỗi mạng
            
    st.session_state[f"input_cmt_{vid_id}"] = ""

# ================= CSS CHUẨN EDTECH & YOUTUBE =================
st.markdown("""
    <style>
    .block-container { padding-top: 2rem; padding-bottom: 2rem; }
    .grid-title { font-size: 1rem; font-weight: bold; color: #0f0f0f; margin-top: 8px; margin-bottom: 4px; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; line-height: 1.3;}
    .grid-info { font-size: 0.8rem; color: #606060; margin-bottom: 10px; }
    .yt-title { font-size: 1.4rem; font-weight: bold; color: #0f0f0f; margin-top: 15px; margin-bottom: 5px;}
    .yt-stats { font-size: 0.9rem; color: #606060; margin-bottom: 15px; font-weight: 500;}
    .playlist-scrollable { max-height: 650px; overflow-y: auto; overflow-x: hidden; padding-right: 8px; }
    .playlist-scrollable::-webkit-scrollbar { width: 6px; }
    .playlist-scrollable::-webkit-scrollbar-track { background: #f1f5f9; border-radius: 8px; }
    .playlist-scrollable::-webkit-scrollbar-thumb { background: #cbd5e1; border-radius: 8px; }
    .playlist-scrollable::-webkit-scrollbar-thumb:hover { background: #94a3b8; }
    .yt-sidebar-title { font-size: 0.85rem; font-weight: bold; color: #0f0f0f; line-height: 1.3; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; margin-bottom: 2px;}
    .yt-sidebar-author { font-size: 0.75rem; color: #606060;}
    .cmt-list-container { margin-top: 25px; }
    .cmt-container { display: flex; gap: 15px; margin-bottom: 20px; }
    .cmt-avatar { width: 40px; height: 40px; border-radius: 50%; background-color: #4F46E5; color: white; display: flex; align-items: center; justify-content: center; font-weight: bold; font-size: 1.2rem;}
    .cmt-content { flex: 1; }
    .cmt-name { font-size: 0.9rem; font-weight: bold; color: #0f0f0f; margin-bottom: 3px;}
    .cmt-text { font-size: 0.95rem; color: #0f0f0f;}
    </style>
""", unsafe_allow_html=True)

if "student_profile" not in st.session_state:
    st.session_state.student_profile = {"name": "Học sinh", "exp": 0, "completed_tasks": []}
if "selected_video" not in st.session_state:
    st.session_state.selected_video = None

# GỌI API LẤY DATA (LUÔN LÀ DATA MỚI NHẤT TỪ DB)
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
    st.title("📺 Rạp Chiếu Video Bài Giảng")
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
                            st.markdown("<div class='grid-info'>✅ Đã xem | 📚 " + html.escape(v.get('topic', 'Khác')) + "</div>", unsafe_allow_html=True)
                        else:
                            st.markdown("<div class='grid-info'>🎁 +30 EXP | 📚 " + html.escape(v.get('topic', 'Khác')) + "</div>", unsafe_allow_html=True)
                        
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
    # Cập nhật lại current_v từ ai_videos mới nhất (tránh data bị cũ khi vừa Like xong)
    current_v = next((vid for vid in ai_videos if vid["id"] == st.session_state.selected_video["id"]), st.session_state.selected_video)
    st.session_state.selected_video = current_v 
    
    vid_id = current_v['id']
    is_completed = vid_id in st.session_state.student_profile['completed_tasks']
    real_name = get_current_username()
    encoded_name = urllib.parse.quote(real_name) # Mã hóa để API không bị lỗi

    # THAY THẾ BẰNG 2 NÚT ĐIỀU HƯỚNG MỚI ĐỂ TRÁNH LÚ
    nav_c1, nav_c2, _ = st.columns([2, 2, 6])
    with nav_c1:
        if st.button("⬅️ Danh sách Video", use_container_width=True):
            st.session_state.selected_video = None
            st.rerun()
    with nav_c2:
        if st.button("🏠 Về Góc Học Tập", use_container_width=True):
            st.switch_page("pages/student/dashboard.py")

    col_video, col_playlist = st.columns([7, 3], gap="large")

    # ================== CỘT TRÁI ==================
    with col_video:
        try: st.video(current_v['url'])
        except: st.error("Link video không hợp lệ!")
        
        safe_title = html.escape(current_v.get('title', ''))
        st.markdown(f"<div class='yt-title'>{safe_title}</div>", unsafe_allow_html=True)
        st.markdown(f"<div class='yt-stats'>📚 Chủ đề: {html.escape(current_v.get('topic',''))} • 🎓 Trình độ: {html.escape(current_v.get('level',''))} • 🎁 Phần thưởng: +30 EXP</div>", unsafe_allow_html=True)
        
        # LOGIC LIKE DATABASE: Kiểm tra tên user có trong danh sách liked_by không
        liked_by_list = current_v.get("liked_by", [])
        total_likes = current_v.get("likes", 0)
        has_liked = real_name in liked_by_list

        btn_c1, btn_c2, _ = st.columns([2.5, 3, 4.5]) 
        with btn_c1:
            like_icon = f"❤️ Đã Thích ({total_likes})" if has_liked else f"👍 Thích ({total_likes})"
            if st.button(like_icon, key=f"like_{vid_id}", use_container_width=True):
                # GỌI API TOGGLE LIKE XUỐNG DB
                try:
                    requests.post(f"http://127.0.0.1:8000/api/tv2/videos/{vid_id}/like", json={"username": real_name})
                    time.sleep(0.2)
                    st.rerun()
                except:
                    st.toast("⚠️ Lỗi kết nối API!")
                    
        with btn_c2:
            if not is_completed:
                if st.button("✅ Hoàn thành bài học", type="primary", use_container_width=True):
                    # BẮN API LƯU ĐIỂM XUỐNG DATABASE GIỐNG TRẠM QUIZ
                    submit_payload = {"video_id": vid_id, "exp_earned": 30}
                    try:
                        requests.post(f"http://127.0.0.1:8000/api/tv2/student/{encoded_name}/complete-video", json=submit_payload, timeout=5)
                    except Exception as e:
                        st.toast("⚠️ Có lỗi khi lưu dữ liệu lên server, nhưng kết quả tạm thời vẫn được ghi nhận.")

                    # Cập nhật Giao diện ngay lập tức
                    st.session_state.student_profile['completed_tasks'].append(vid_id)
                    st.session_state.student_profile['exp'] += 30
                    st.toast("🎉 Đã hoàn thành! Nhận +30 EXP")
                    time.sleep(0.5)
                    st.rerun()
            else:
                st.button("✨ Đã hoàn thành", disabled=True, use_container_width=True)
                
        st.divider()

        # DANH SÁCH BÌNH LUẬN (LẤY TRỰC TIẾP TỪ DB, KHÔNG XÀI SESSION_STATE NỮA)
        db_comments = current_v.get("comments", [])
        # Đảo ngược danh sách để comment mới nhất lên đầu
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

    # ================== CỘT PHẢI ==================
    with col_playlist:
        st.markdown("#### 📽️ Danh sách bài học")
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