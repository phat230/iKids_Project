import streamlit as st
import pandas as pd
import os
from utils.role_guard import require_role

# 1. Lính gác: Chỉ cho phép tài khoản học sinh truy cập trang này
require_role(["student"])

# ================= HÀM ĐỌC FILE CSS (SỬA LỖI ĐƯỜNG DẪN) =================
def load_css(file_name):
    """
    Tự động tìm file CSS trong thư mục frontend/CSS/
    file_name: tên file kèm thư mục con, ví dụ 'student/ket_qua.css'
    """
    # Lấy đường dẫn tuyệt đối đến thư mục chứa file ket_qua.py hiện tại
    current_dir = os.path.dirname(os.path.abspath(__file__)) # frontend/pages/student
    
    # Tìm đường dẫn đến thư mục CSS (lùi 2 cấp rồi vào CSS/)
    css_root = os.path.abspath(os.path.join(current_dir, "../../CSS"))
    full_path = os.path.join(css_root, file_name)

    if os.path.exists(full_path):
        with open(full_path, "r", encoding="utf-8") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    else:
        # Hiển thị đường dẫn chính xác mà hệ thống đang tìm để bạn kiểm tra
        st.warning(f"⚠️ Không tìm thấy file CSS tại: {full_path}")

# Tải CSS làm đẹp cho bảng điểm (Chỉ truyền phần sau thư mục CSS/)
load_css("student/ket_qua.css")

# ================= GIAO DIỆN CHÍNH =================
st.title("📊 Bảng Điểm Cá Nhân")
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
st.dataframe(df, use_container_width=True, hide_index=True)

st.divider()

# 4. Góc phân tích thông minh của AI (Smart Recommendation)
st.subheader("🤖 Phân Tích Từ Hệ Thống AI")
st.info("💡 **AI Nhận xét:** Bạn đang làm rất tốt môn Kỹ Năng Sống và Anh Văn! Tuy nhiên, điểm môn Khoa Học đang hơi thấp. Hãy vào mục **Bài Tập AI** để ôn luyện thêm phần này, vừa cải thiện điểm số vừa nhận thêm thật nhiều iKids Xu nhé!")