import streamlit as st
import pandas as pd
import requests
import os

# Cấu hình API
API_TV3 = "http://localhost:8000/api/tv3"

st.set_page_config(page_title="Báo Cáo Học Tập - iKids", page_icon="📈", layout="wide")

# ================= HÀM ĐỌC FILE CSS (SỬA LỖI ĐƯỜNG DẪN TUYỆT ĐỐI) =================
def load_css(file_name):
    """
    Tự động tìm file CSS trong thư mục frontend/CSS/
    file_name: tên file kèm thư mục con, ví dụ 'parent/ket_qua.css'
    """
    # Lấy đường dẫn tuyệt đối đến thư mục chứa file hiện tại (frontend/pages/parent)
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Tìm đường dẫn đến thư mục CSS (lùi 2 cấp rồi vào CSS/)
    css_root = os.path.abspath(os.path.join(current_dir, "../../CSS"))
    full_path = os.path.join(css_root, file_name)

    if os.path.exists(full_path):
        with open(full_path, "r", encoding="utf-8") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    else:
        st.warning(f"⚠️ Không tìm thấy file CSS tại: {full_path}")

# Tải CSS làm đẹp cho trang Báo cáo kết quả (Chỉ truyền phần sau thư mục CSS/)
load_css("parent/ket_qua.css")

# 1. KIỂM TRA ĐĂNG NHẬP
parent_id = st.session_state.get("user_id")
token = st.session_state.get("access_token")

if not parent_id or not token:
    st.error("⚠️ Vui lòng đăng nhập để xem báo cáo của các bé.")
    st.stop()

headers = {"Authorization": f"Bearer {token}", "parent-id": str(parent_id)}

# --- HÀM HỖ TRỢ LẤY DỮ LIỆU ---
def get_my_children():
    try:
        res = requests.get(f"{API_TV3}/parent/my-children", headers=headers)
        return res.json() if res.status_code == 200 else []
    except:
        return []

def get_learning_stats(child_id):
    """Lấy thống kê học tập (Giả lập dữ liệu theo ID bé)"""
    # Logic giả lập dựa trên ký tự cuối của ID để tạo sự khác biệt giữa các bé
    last_char = child_id[-1] if child_id else "0"
    is_even = int(last_char, 16) % 2 == 0
    
    stats = {
        "attendance": "98%" if is_even else "92%",
        "avg_quiz": 8.8 if is_even else 7.5,
        "videos": 15 if is_even else 8,
        "rank": "Explorer" if is_even else "Beginner"
    }
    return stats

# --- GIAO DIỆN CHÍNH ---
st.title("📊 Báo Cáo Chuyên Sâu Hành Trình Lớn Khôn")

# 2. CHỌN CON ĐỂ XEM BÁO CÁO
children = get_my_children()

if not children:
    st.info("Bạn chưa liên kết với tài khoản học sinh nào. Vui lòng vào mục 'Quản lý con' để tạo tài khoản cho bé.")
    st.stop()

child_options = {c["id"]: c["name"] for c in children}
selected_child_id = st.selectbox(
    "👦👧 Chọn con để xem báo cáo:", 
    options=list(child_options.keys()), 
    format_func=lambda x: child_options[x]
)

st.write(f"Đang hiển thị dữ liệu của bé: **{child_options[selected_child_id]}**")
st.divider()

# 3. THỐNG KÊ NHANH
child_stats = get_learning_stats(selected_child_id)

col1, col2, col3, col4 = st.columns(4)
col1.metric(label="Tỷ lệ chuyên cần", value=child_stats["attendance"], delta="Tăng 2%")
col2.metric(label="Điểm trung bình Quiz", value=f"{child_stats['avg_quiz']}/10", delta="Tăng 0.5")
col3.metric(label="Video AI đã học", value=f"{child_stats['videos']} video", delta="Mới")
col4.metric(label="Hạng hiện tại", value=child_stats["rank"], delta="Xuất sắc")

st.divider()

# 4. BIỂU ĐỒ TIẾN ĐỘ
st.subheader("📈 Biểu đồ điểm số các bài Quiz gần đây")
data_points = [7, 8, 9, 8, 10] if int(selected_child_id[-1], 16) % 2 == 0 else [6, 9, 8, 7, 9]
chart_data = pd.DataFrame(data_points, columns=["Điểm số"])
st.line_chart(chart_data)

# 5. NHẬN XÉT CỦA GIÁO VIÊN
st.subheader("👨‍🏫 Nhận xét định kỳ từ Giáo viên")

comments = [
    {
        "subject": "Tiếng Anh Giao Tiếp",
        "teacher": "Thầy John",
        "date": "20/05/2026",
        "content": f"Bé {child_options[selected_child_id]} rất tích cực phát biểu. Phát âm ngày càng tiến bộ."
    },
    {
        "subject": "Toán Tư Duy",
        "teacher": "Cô Lan",
        "date": "18/05/2026",
        "content": "Bé nắm vững các quy tắc logic, làm bài tập về nhà đầy đủ."
    }
]

for comment in comments:
    with st.container(border=True):
        st.markdown(f"### 📘 {comment['subject']}")
        st.caption(f"Giáo viên: {comment['teacher']} | Ngày: {comment['date']}")
        st.markdown(f"**Nhận xét:**")
        st.markdown(f"> {comment['content']}")