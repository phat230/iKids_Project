import streamlit as st
from datetime import datetime

# Cài đặt layout rộng để hiển thị thoáng hơn
st.set_page_config(page_title="Nhật ký giảng dạy", page_icon="📝", layout="wide")

# ================= CSS CUSTOM =================
st.markdown("""
    <style>
    /* Chỉnh màu tiêu đề phân mục */
    .section-header {
        color: #FF4B4B;
        border-bottom: 2px solid #FF4B4B;
        padding-bottom: 5px;
        margin-top: 20px;
        margin-bottom: 15px;
        font-family: 'Arial', sans-serif;
    }
    /* Chỉnh tên học sinh cho nổi bật */
    .student-name {
        font-size: 1.15rem;
        font-weight: bold;
        color: #1F77B4;
        margin-bottom: 10px;
    }
    /* Khoảng cách cho nút submit */
    .stButton>button {
        font-weight: bold;
        font-size: 18px;
        margin-top: 20px;
    }
    </style>
""", unsafe_allow_html=True)
# ==============================================

st.title("📝 Nhật ký & Điểm danh Lớp học")

# Giả lập dữ liệu được hệ thống Vận Hành (TV1) đẩy sang
mock_class_data = {
    "class_id": "Lop_T6",
    "class_name": "Tiếng Anh Thiếu Nhi - Lớp T6",
    "students": [
        {"id": "hs1", "name": "Nguyễn Văn A"},
        {"id": "hs2", "name": "Trần Thị B"},
        {"id": "hs3", "name": "Lê Hoàng C"},
    ]
}

# --- HEADER THÔNG TIN LỚP HỌC ---
col_info1, col_info2 = st.columns(2)
with col_info1:
    st.info(f"📚 **Lớp đang dạy:** {mock_class_data['class_name']}")
with col_info2:
    st.success(f"📅 **Ngày:** {datetime.now().strftime('%d/%m/%Y')} | 👥 **Sĩ số:** {len(mock_class_data['students'])} học sinh")

# Bắt đầu Form
with st.form("journal_form"):
    
    # --- PHẦN 1: NỘI DUNG BÀI GIẢNG ---
    st.markdown("<h3 class='section-header'>1. Nội dung bài giảng</h3>", unsafe_allow_html=True)
    with st.container(border=True): # Đóng khung phần nội dung
        content = st.text_area("Hôm nay lớp đã học những gì?", placeholder="Nhập tóm tắt nội dung bài học để Phụ huynh theo dõi...", height=100)
        used_video = st.selectbox("🎬 Video AI đã sử dụng (Tùy chọn)", ["Không có", "Video: Động vật quanh ta", "Video: Đếm số 1-10"])

    # --- PHẦN 2: ĐIỂM DANH & NHẬN XÉT ---
    st.markdown("<h3 class='section-header'>2. Điểm danh & Đánh giá chi tiết</h3>", unsafe_allow_html=True)
    
    attendance_data = []
    
    # Lặp qua từng học sinh, mỗi học sinh là một thẻ (Card) riêng
    for student in mock_class_data["students"]:
        with st.container(border=True): # Đóng khung từng học sinh cho dễ nhìn
            st.markdown(f"<div class='student-name'>👤 {student['name']} (Mã: {student['id']})</div>", unsafe_allow_html=True)
            
            # Chia cột bên trong Card học sinh
            c1, c2, c3 = st.columns([1, 1.5, 1.5])
            
            with c1:
                # Dùng toggle thay cho checkbox nhìn mượt như app mobile
                is_present = st.toggle("✅ Có mặt", value=True, key=f"att_{student['id']}")
            
            with c2:
                # Nếu vắng mặt (toggle off) thì vô hiệu hóa nhập điểm
                score = st.number_input("🎯 Điểm số", min_value=0.0, max_value=10.0, step=0.5, key=f"score_{student['id']}", disabled=not is_present)
            
            with c3:
                emoji = st.selectbox("🌟 Đánh giá thái độ", ["🌟 Xuất sắc", "👍 Tốt", "💪 Cố gắng", "😴 Thiếu tập trung"], key=f"emoji_{student['id']}", disabled=not is_present)
            
            comment = st.text_input("💬 Nhận xét chi tiết", placeholder="Giáo viên nhận xét thêm...", key=f"comment_{student['id']}", disabled=not is_present)
            
            # Gom data lại chuẩn bị gửi Backend
            attendance_data.append({
                "student_id": student["id"],
                "is_present": is_present,
                "score": score if is_present else None,
                "teacher_comment": comment if is_present else "",
                "emoji_feedback": emoji if is_present else ""
            })

    # Nút Submit bự, căn giữa form
    submitted = st.form_submit_button("🚀 LƯU NHẬT KÝ & GỬI BÁO CÁO", use_container_width=True)
    
    if submitted:
        # Giả lập logic gửi API
        if len(content) < 5:
            st.error("⚠️ Vui lòng nhập nội dung bài giảng cụ thể hơn!")
        else:
            st.success("✅ Đã lưu nhật ký thành công! Hệ thống đã gửi thông báo tới Phụ huynh và ghi nhận EXP cho Học sinh chuyên cần.")
            st.balloons() # Thêm hiệu ứng cho vui mắt