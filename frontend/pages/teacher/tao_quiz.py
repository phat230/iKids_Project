import streamlit as st
from datetime import datetime

def render_ai_quiz_page():
    st.set_page_config(layout="wide")
    st.title("🤖 Kho Học Liệu AI & Giao Bài")
    st.markdown("Khám phá các video bài giảng sinh động do AI tạo ra. Tương tác và giao bài tập Quiz trực tiếp cho học sinh.")

    # --- 1. DỮ LIỆU MÔ PHỎNG TỪ NHÓM AI (TV2) ---
    ai_videos = [
        {
            "id": "vid_01",
            "title": "Toán Tư Duy: Khám phá vương quốc Phép Cộng",
            "tags": ["Toán học", "Lớp 1", "Hoạt hình AI"],
            "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ", # Link video mẫu
            "likes": 128,
            "comments": 24,
            "quiz": [
                "Câu 1: 5 quả táo thêm 3 quả táo bằng mấy quả? (A: 7, B: 8, C: 9)",
                "Câu 2: Dấu nào dùng để cộng? (A: +, B: -, C: =)"
            ]
        },
        {
            "id": "vid_02",
            "title": "Scratch Cơ Bản: Lập trình chú Mèo chạy đua",
            "tags": ["Lập trình", "Scratch", "Thực hành"],
            "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
            "likes": 85,
            "comments": 12,
            "quiz": [
                "Câu 1: Khối lệnh nào để bắt đầu chương trình? (A: Lá cờ xanh, B: Hình vuông đỏ)",
                "Câu 2: Lệnh 'Move 10 steps' có tác dụng gì? (A: Xoay tròn, B: Tiến tới)"
            ]
        },
        {
            "id": "vid_03",
            "title": "Tiếng Anh: Chuyến phiêu lưu cùng các loài Động Vật",
            "tags": ["Tiếng Anh", "Từ vựng", "Kids"],
            "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
            "likes": 210,
            "comments": 45,
            "quiz": [
                "Câu 1: Con chó trong tiếng Anh là gì? (A: Cat, B: Dog, C: Bird)",
                "Câu 2: 'Elephant' nghĩa là con gì? (A: Voi, B: Hổ, C: Khỉ)"
            ]
        }
    ]

    # Danh sách lớp học hiện tại của giáo viên (Đồng bộ từ TV1)
    active_classes = [
        "Toán Tư Duy - 1A (Thứ 2)",
        "Lập trình Scratch (Thứ 3)",
        "Tiếng Anh Giao Tiếp (Hôm nay)"
    ]

    # --- 2. GIAO DIỆN LỌC TÌM KIẾM ---
    col_search, col_filter = st.columns([3, 1])
    with col_search:
        st.text_input("🔍 Tìm kiếm học liệu AI...", placeholder="Nhập tên môn học, chủ đề...")
    with col_filter:
        st.selectbox("Lọc theo môn", ["Tất cả", "Toán học", "Lập trình", "Tiếng Anh", "Khoa học"])

    st.markdown("---")
    st.subheader("🔥 Xu hướng học liệu hôm nay")

    # --- 3. HIỂN THỊ DANH SÁCH VIDEO (DẠNG GRID YOUTUBE) ---
    # Hiển thị 3 video trên 1 hàng ngang
    cols = st.columns(3)
    
    for index, video in enumerate(ai_videos):
        # Chia đều video vào các cột
        with cols[index % 3]:
            # Container để tạo viền cho thẻ Video
            with st.container(border=True):
                # 1. Trình phát Video
                st.video(video["url"])
                
                # 2. Thông tin Video
                st.markdown(f"**{video['title']}**")
                
                # Hiển thị Tags
                tags_html = "".join([f"<span style='background-color: #f1f5f9; color: #475569; padding: 3px 8px; border-radius: 12px; font-size: 12px; margin-right: 5px;'>#{tag}</span>" for tag in video['tags']])
                st.markdown(tags_html, unsafe_allow_html=True)
                
                st.write("") # Dòng trống
                
                # 3. Tương tác Mạng Xã Hội
                c1, c2 = st.columns(2)
                if c1.button(f"❤️ {video['likes']} Thích", key=f"like_{video['id']}", use_container_width=True):
                    st.toast("Đã thả tim cho video học liệu!")
                if c2.button(f"💬 {video['comments']} Góp ý", key=f"cmt_{video['id']}", use_container_width=True):
                    st.toast("Tính năng bình luận đang mở!")
                
                st.divider()
                
                # 4. Khu vực Xem trước Quiz và Giao Bài
                with st.expander("📝 Giao bài & Xem trước Quiz"):
                    st.caption("Bộ câu hỏi AI tự động sinh ra cho video này:")
                    for q in video['quiz']:
                        st.info(q)
                    
                    st.markdown("**Giao bài cho lớp:**")
                    selected_class = st.selectbox("Chọn lớp", active_classes, key=f"class_{video['id']}", label_visibility="collapsed")
                    
                    if st.button("🚀 Giao Bài Tập Về Nhà", type="primary", key=f"assign_{video['id']}", use_container_width=True):
                        st.success(f"✅ Đã giao {len(video['quiz'])} câu hỏi Quiz và Video này cho lớp {selected_class.split('(')[0].strip()}!")

if __name__ == "__main__":
    render_ai_quiz_page()