import streamlit as st
import pandas as pd
from utils.role_guard import require_role

# Bảo vệ: Chỉ cho phép phụ huynh
require_role(["parent"])

st.set_page_config(page_title="Kết Quả Học Tập", page_icon="📊", layout="wide")

user_info = st.session_state.get("user_info", {"name": "Phụ huynh"})

st.title(" Báo Cáo Học Tập & Tư Vấn AI")
st.write(f"Kính chào phụ huynh **{user_info['name']}**. Dưới đây là tình hình học tập mới nhất của bé.")
st.divider()

# Dữ liệu giả lập
mock_metrics = {"toan": 9.0, "anh_van": 8.5, "ky_nang": 10.0, "xu_tich_luy": 450}
mock_chart_data = pd.DataFrame({
    "Tuần": ["Tuần 1", "Tuần 2", "Tuần 3", "Tuần 4"],
    "Điểm Trung Bình": [7.5, 8.0, 8.5, 9.0]
})

tab1, tab2 = st.tabs([" Tiến Độ Học Tập", " Chuyên Gia AI Gợi Ý"])

with tab1:
    st.subheader("📌 Tổng quan tháng này")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Toán Tư Duy", f"{mock_metrics['toan']} ⭐️", "+0.5")
    col2.metric("Anh Văn", f"{mock_metrics['anh_van']} ⭐️", "Ổn định")
    col3.metric("Kỹ Năng Sống", f"{mock_metrics['ky_nang']} ⭐️", "Xuất sắc")
    col4.metric("Ví Xu Hiện Tại", f"{mock_metrics['xu_tich_luy']} 💰", "Đủ đổi quà")

    st.markdown("---")
    left_col, right_col = st.columns([2, 1])
    with left_col:
        st.write("**Biểu đồ sự tiến bộ**")
        st.line_chart(mock_chart_data.set_index("Tuần"))
    
    with right_col:
        st.write("**Nhận xét từ giáo viên**")
        st.info("Con đi học chuyên cần, hăng hái phát biểu. Tuy nhiên, môn Tiếng Anh con còn hơi rụt rè khi giao tiếp. Gia đình nên động viên con thêm.")

with tab2:
    st.subheader(" Lời khuyên hành động từ AI")
    st.write("Hệ thống AI đã phân tích dữ liệu và đưa ra lộ trình cá nhân hóa cho bé:")
    
    with st.container(border=True):
        st.success("** Điểm Mạnh:** Tư duy logic toán học rất nhạy bén, tốc độ giải bài tập nằm trong top 10% của lớp.")
        st.warning("** Cần Cải Thiện:** Kỹ năng phát âm (Pronunciation) đang chững lại. Bé thường bỏ qua bài tập luyện nói.")
        st.info("** Hành Động Đề Xuất Tuần Này:**\n"
                "1. Nhắc bé xem video *Luyện phát âm đuôi -ed/s* trên hệ thống (Thưởng 20 Xu).\n"
                "2. Đăng ký CLB Tiếng Anh cuối tuần (Miễn phí).")
        
        if st.button("Đăng ký CLB cuối tuần ngay", type="primary"):
            st.toast("✅ Đã gửi yêu cầu đăng ký lên Trung tâm!")