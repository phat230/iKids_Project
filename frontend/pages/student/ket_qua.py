import streamlit as st
import pandas as pd
from utils.role_guard import require_role

require_role(["student"])

st.set_page_config(page_title="Kết Quả Học Tập", page_icon="📈")

st.title("📈 Bảng Điểm Cá Nhân")
st.write("Theo dõi sự tiến bộ của bạn qua từng tuần.")
st.divider()

data = {
    "Môn học": ["Toán Tư Duy", "Anh Văn", "Khoa Học", "Kỹ Năng Sống"],
    "Điểm Giữa Kỳ": [8.5, 9.0, 7.5, 10.0],
    "Điểm Cuối Kỳ": ["Chưa có", "Chưa có", "Chưa có", "Chưa có"],
    "Đánh giá": ["Khá", "Tốt", "Cần cố gắng", "Xuất sắc"]
}

st.dataframe(pd.DataFrame(data), use_container_width=True)
st.info("🤖 **AI Nhận xét:** Bạn đang làm rất tốt môn Kỹ Năng Sống. Hãy dành thêm chút thời gian ôn tập môn Khoa Học để đạt điểm cao hơn nhé!")