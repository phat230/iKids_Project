import streamlit as st
import time
from datetime import date

st.set_page_config(page_title="Nhật Ký & Điểm Danh", page_icon="📓", layout="wide")

st.title("📓 Nhật Ký Giảng Dạy & Điểm Danh")
st.write("Ghi nhận điểm danh, đánh giá học sinh và lưu trữ nhật ký bài giảng ngay sau ca dạy.")

# ================= MOCK DATA (GIẢ LẬP DỮ LIỆU TỪ TV1) =================
mock_classes = ["Tiếng Anh Giao Tiếp - Lớp T6", "Toán Tư Duy - Lớp T7", "Lớp Năng khiếu M1"]

mock_students = {
    "Tiếng Anh Giao Tiếp - Lớp T6": ["Nguyễn Văn An", "Trần Thị Bình", "Lê Văn Cường", "Phạm Hoàng Dung"],
    "Toán Tư Duy - Lớp T7": ["Hoàng Gia Bảo", "Vũ Thiên Kim", "Đinh Tuấn Kiệt"],
    "Lớp Năng khiếu M1": ["Trương Tiểu My", "Lý Hải Ngọc"]
}

# ================= LẤY DỮ LIỆU TỪ KHO HỌC LIỆU CỦA ÔNG =================
if "ai_videos" not in st.session_state:
    st.session_state.ai_videos = []

if "saved_quizzes" not in st.session_state:
    st.session_state.saved_quizzes = []

# ================= GIAO DIỆN CHÍNH =================
st.subheader("1. Lựa chọn ca dạy")
col_date, col_class = st.columns([1, 3])
with col_date:
    selected_date = st.date_input("Ngày dạy:", date.today())
with col_class:
    selected_class = st.selectbox("Chọn lớp học:", mock_classes)

st.divider()

# Chia Layout: 6 phần cho Điểm danh, 4 phần cho Nhật ký
col_left, col_right = st.columns([6, 4], gap="large")

# ----------------- CỘT TRÁI: ĐIỂM DANH & ĐÁNH GIÁ -----------------
with col_left:
    st.markdown(f"### 👥 Điểm danh & Đánh giá: `{selected_class}`")
    st.caption("Ghi chú: Phụ huynh sẽ nhận được thông báo ngay khi bạn lưu dữ liệu này.")
    
    students = mock_students[selected_class]
    attendance_data = []
    
    # Header của bảng điểm danh
    h1, h2, h3, h4 = st.columns([2.5, 2, 2, 3])
    h1.write("**Họ và tên**")
    h2.write("**Trạng thái**")
    h3.write("**Thái độ học**")
    h4.write("**Nhận xét nhanh**")
    
    for student in students:
        with st.container(border=True):
            c_name, c_att, c_emo, c_cmt = st.columns([2.5, 2, 2, 3])
            
            with c_name:
                st.markdown(f"<div style='margin-top: 8px; font-weight: 500;'>{student}</div>", unsafe_allow_html=True)
            
            with c_att:
                att = st.selectbox("Trạng thái", ["✅ Có mặt", "❌ Vắng", "⏳ Đi trễ"], key=f"att_{student}", label_visibility="collapsed")
            
            with c_emo:
                is_disabled = True if att == "❌ Vắng" else False
                emo = st.selectbox("Thái độ", ["⭐ Xuất sắc", "👍 Tốt", "👌 Bình thường", "👎 Thiếu tập trung"], key=f"emo_{student}", label_visibility="collapsed", disabled=is_disabled)
            
            with c_cmt:
                cmt = st.text_input("Nhận xét", placeholder="Nhập nhận xét...", key=f"cmt_{student}", label_visibility="collapsed", disabled=is_disabled)
            
            attendance_data.append({"Tên": student, "Trạng thái": att, "Thái độ": emo, "Nhận xét": cmt})

# ----------------- CỘT PHẢI: NHẬT KÝ BÀI GIẢNG -----------------
with col_right:
    st.markdown("### 📝 Nhật ký bài học")
    
    with st.container(border=True):
        lesson_topic = st.text_input("🎯 Nội dung / Chủ đề bài học:", placeholder="Ví dụ: Unit 3 - Wild Animals")
        
        # CHỌN VIDEO AI (TỪ KHO)
        available_videos = [vid["title"] for vid in st.session_state.ai_videos]
        if not available_videos:
            used_videos = st.multiselect("🎬 Video AI đã sử dụng trên lớp:", ["(Không có video trong kho)"], disabled=True)
        else:
            used_videos = st.multiselect("🎬 Video AI đã sử dụng trên lớp:", available_videos)
            
        # CHỌN BÀI TẬP VỀ NHÀ (TỪ KHO QUIZ) - TÍNH NĂNG MỚI THEO Ý ÔNG
        available_quizzes = [q["title"] for q in st.session_state.saved_quizzes]
        if not available_quizzes:
            st.warning("💡 Kho bài tập hiện đang trống. Hãy qua trang 'Tạo Bài Tập AI' để soạn đề trước nhé!")
            assigned_quizzes = st.multiselect("📝 Bài tập (Quiz) giao về nhà:", ["(Không có đề nào)"], disabled=True)
        else:
            assigned_quizzes = st.multiselect("📝 Bài tập (Quiz) giao về nhà:", available_quizzes)
        
        general_note = st.text_area("💬 Ghi chú chung cho ca dạy (Nội bộ):", placeholder="Ví dụ: Lớp học sôi nổi, các con nắm bài tốt...")
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        if st.button("💾 LƯU NHẬT KÝ & ĐIỂM DANH", type="primary", use_container_width=True):
            if not lesson_topic:
                st.error("⚠️ Vui lòng nhập nội dung/chủ đề bài học!")
            else:
                with st.spinner("Đang đồng bộ dữ liệu hệ thống..."):
                    time.sleep(1.5)
                    st.success(f"✅ Đã lưu nhật ký cho lớp {selected_class} thành công!")
                    
                    # Hiện thông báo báo cáo các hành động đã làm
                    if assigned_quizzes:
                        st.info(f"🔔 Đã tự động giao {len(assigned_quizzes)} bài tập về nhà cho lớp. Thông báo đã gửi tới Học sinh/Phụ huynh (TV3).")
                    else:
                        st.info("🔔 Dữ liệu điểm danh & nhận xét đã được đẩy sang App Phụ Huynh (TV3).")
                        
                    st.balloons()