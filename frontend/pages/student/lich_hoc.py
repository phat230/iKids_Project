import streamlit as st
import pandas as pd
from utils.role_guard import require_role

require_role(["student"])

st.set_page_config(page_title="Lịch Học Của Tôi", page_icon="📅")

st.title("📅 Thời Khóa Biểu")
st.write("Theo dõi lịch học để không bỏ lỡ buổi học nào nhé!")

# Dữ liệu bảng giả lập
data = {
    "Thứ": ["Thứ 2", "Thứ 4", "Thứ 6", "Chủ Nhật"],
    "Ca học": ["17:30 - 19:00", "17:30 - 19:00", "17:30 - 19:00", "08:00 - 09:30"],
    "Môn học": ["Toán Tư Duy", "Anh Văn Giao Tiếp", "Toán Tư Duy", "Kỹ Năng Sống"],
    "Phòng": ["Phòng 101", "Phòng 205", "Phòng 101", "Sân cỏ nhân tạo"]
}
df = pd.DataFrame(data)

st.table(df)