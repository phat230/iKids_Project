import streamlit as st
import pandas as pd
from utils.role_guard import require_role

# 1. Lính gác: Chỉ cho phép tài khoản học sinh truy cập trang này
require_role(["student"])

# Lưu ý: Không dùng st.set_page_config ở đây nữa vì đã gọi ở app.py rồi

st.title("📈 Bảng Điểm Cá Nhân")
st.write("Theo dõi sự tiến bộ của bạn qua từng bài kiểm tra và các kỳ thi nhé!")
st.divider()

# 2. Dữ liệu giả lập (Sau này sẽ gọi API lấy từ Backend - TV2)
data = {
    "Môn học": ["Toán Tư Duy", "Anh Văn", "Khoa Học", "Kỹ Năng Sống"],
    "Điểm Giữa Kỳ": [8.5, 9.0, 7.5, 10.0],
    "Điểm Cuối Kỳ": ["Chưa có", "Chưa có", "Chưa có", "Chưa có"],
    "Đánh giá": ["Khá", "Tốt", "Cần cố gắng", "Xuất sắc"]
}

# 3. Hiển thị bảng dữ liệu đẹp mắt
df = pd.DataFrame(data)
st.dataframe(df, use_container_width=True)

st.divider()

# 4. Góc phân tích thông minh của AI (Smart Recommendation)
st.subheader("🧠 Phân Tích Từ Hệ Thống AI")
st.info("🤖 **AI Nhận xét:** Bạn đang làm rất tốt môn Kỹ Năng Sống và Anh Văn! Tuy nhiên, điểm môn Khoa Học đang hơi thấp. Hãy vào mục **Bài Tập AI** để ôn luyện thêm phần này, vừa cải thiện điểm số vừa nhận thêm thật nhiều iKids Xu nhé!")