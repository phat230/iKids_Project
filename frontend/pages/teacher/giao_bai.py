import streamlit as st
from datetime import datetime, timedelta

st.set_page_config(page_title="Giao Bài Tập", page_icon="📤")

# Lấy kho dữ liệu từ Session State
if "saved_quizzes" not in st.session_state:
    st.session_state.saved_quizzes = []

st.title("📤 Giao Bài Tập Cho Lớp")

# NẾU CHƯA CÓ ĐỀ NÀO TRONG KHO
if len(st.session_state.saved_quizzes) == 0:
    st.warning("⚠️ Kho học liệu của bạn hiện chưa có bộ đề nào!")
    st.info("Hãy sử dụng AI để tạo bộ đề trước khi giao bài cho lớp nhé.")
    st.page_link("pages/teacher/tao_quiz.py", label="👉 Đi tới trang Tạo Bài Tập AI", icon="🤖")

# NẾU ĐÃ CÓ ĐỀ TRONG KHO THÌ HIỆN FORM
else:
    with st.container(border=True):
        st.subheader("⚙️ Cấu hình giao bài")
        
        # Trích xuất danh sách tên các bộ đề có THẬT
        danh_sach_de = [q['title'] for q in st.session_state.saved_quizzes]
        
        # Nếu được chuyển sang từ nút "Giao Bài Nhanh" bên trang Kho học liệu
        default_index = 0
        if "selected_quiz_to_assign" in st.session_state:
            if st.session_state.selected_quiz_to_assign in danh_sach_de:
                default_index = danh_sach_de.index(st.session_state.selected_quiz_to_assign)
        
        selected_quiz = st.selectbox("📝 Chọn bộ đề từ kho của bạn:", options=danh_sach_de, index=default_index)
        
        # Giả lập danh sách lớp của TV1 (Do TV1 chưa làm xong DB)
        selected_class = st.multiselect("👥 Chọn lớp nhận bài:", ["Lớp Tiếng Anh T6", "Lớp Toán Tư Duy T7", "Lớp Năng khiếu M1"])
        
        col1, col2 = st.columns(2)
        with col1:
            deadline_date = st.date_input("📅 Hạn chót:", datetime.now() + timedelta(days=3))
        with col2:
            deadline_time = st.time_input("⏰ Giờ khóa đề:", datetime.strptime("23:59", "%H:%M").time())
            
        note = st.text_area("💬 Lời nhắn cho học sinh:", placeholder="Ví dụ: Các con nhớ xem kỹ bài trước khi làm nhé!")

        if st.button("🚀 XÁC NHẬN GIAO BÀI", type="primary", use_container_width=True):
            if not selected_class:
                st.error("❌ Vui lòng chọn ít nhất 1 lớp để nhận bài!")
            else:
                st.success(f"✅ Đã giao thành công bộ đề '{selected_quiz}' cho {len(selected_class)} lớp!")
                st.info("🔔 Thông báo đã được gửi đến App của Phụ huynh và Học sinh (TV3).")
                st.balloons()