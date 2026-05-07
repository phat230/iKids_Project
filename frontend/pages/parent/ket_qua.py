import streamlit as st
import pandas as pd

st.set_page_config(page_title="Báo Cáo Học Tập", page_icon="📊", layout="wide")

st.title("📊 Báo Cáo Chuyên Sâu Hành Trình Lớn Khôn")
st.write("Theo dõi tiến độ, điểm số và chuyên cần của bé trong tháng qua.")

# 1. Thống kê nhanh bằng thẻ Metric (Giả lập dữ liệu)
col1, col2, col3, col4 = st.columns(4)
col1.metric(label="Tỷ lệ chuyên cần", value="95%", delta="Tăng 5%")
col2.metric(label="Điểm trung bình Quiz", value="8.5/10", delta="Tăng 1.2 điểm")
col3.metric(label="Video AI đã học", value="12 video", delta="3 video tuần này")
col4.metric(label="Tổng iKids Xu kiếm được", value="150 Xu", delta="Hạng: Explorer")

st.divider()

# 2. Biểu đồ trực quan tiến độ học tập
st.subheader("📈 Biểu đồ điểm số các bài Quiz gần đây")
# Khởi tạo dữ liệu giả lập cho biểu đồ
chart_data = pd.DataFrame(
    [7.5, 8.0, 9.0, 8.5, 10.0],
    columns=["Điểm số"]
)
# Vẽ biểu đồ đường
st.line_chart(chart_data)

# 3. Góc nhận xét của Giáo viên
st.subheader("👩‍🏫 Nhận xét định kỳ từ Giáo viên")

with st.container(border=True):
    st.markdown("### 🧮 Lớp Toán Tư Duy")
    st.caption("Giáo viên: Cô Alice | Ngày nhận xét: 15/05/2026")
    st.write("> *Bé tiếp thu bài rất tốt, làm bài tập về nhà đầy đủ. Khi tham gia hệ thống Quiz AI, bé trả lời đúng phần lớn các câu hỏi tính nhẩm. Gia đình có thể cho bé thực hành thêm phần đếm hình học.*")

with st.container(border=True):
    st.markdown("### 🌍 Lớp Tiếng Anh Giao Tiếp")
    st.caption("Giáo viên: Thầy John | Ngày nhận xét: 10/05/2026")
    st.write("> *Bé phát âm chuẩn, tự tin giơ tay phát biểu trong lớp. Đã đổi được huy hiệu 'Học Bá' tuần vừa rồi. Rất đáng khen ngợi! 🌟*")