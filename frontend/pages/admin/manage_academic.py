import streamlit as st
from api_clients.tv2_client import get_all_quizzes, get_all_videos

def main():
    st.title("Quản lý Học thuật & Tương tác")
    
    tab1, tab2 = st.tabs(["Kho học liệu (Quiz)", "Kho Video AI"])

    with tab1:
        st.subheader("Danh sách bộ đề từ Giáo viên")
        quizzes = get_all_quizzes() # Gọi API từ module TV2
        for q in quizzes:
            col1, col2, col3 = st.columns([3, 2, 1])
            col1.write(f"**{q['title']}**")
            col2.write(f"GV: {q['teacher_name']}")
            if col3.button("Xem chi tiết", key=f"quiz_{q['id']}"):
                st.session_state.selected_quiz = q['id']
                st.rerun() # Hoặc chuyển sang sub-page chi tiết

    with tab2:
        st.subheader("Danh sách Video đã upload")
        videos = get_all_videos()
        for v in videos:
            col1, col2, col3 = st.columns([3, 2, 1])
            col1.write(f"🎥 {v['video_name']}")
            col2.write(f"Ngày: {v['upload_date']}")
            if col3.button("Xem chi tiết", key=f"vid_{v['id']}"):
                st.session_state.selected_video = v['id']
                st.rerun()