import streamlit as st
import pandas as pd
import requests

# Cấu hình API
API_TV3 = "http://localhost:8000/api/tv3"

st.set_page_config(page_title="Báo Cáo Học Tập - iKids", page_icon="📊", layout="wide")

# 1. KIỂM TRA ĐĂNG NHẬP
parent_id = st.session_state.get("user_id")
token = st.session_state.get("access_token")

if not parent_id or not token:
    st.error("🔑 Vui lòng đăng nhập để xem báo cáo của các bé.")
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
    """Lấy thống kê chuyên cần, điểm số, video (Giả lập hoặc gọi API từ TV2)"""
    # Trong thực tế, bạn sẽ gọi API đến module của TV2 để lấy điểm thật
    # Ở đây tôi tạo dữ liệu mẫu dựa trên ID của từng bé để bạn thấy sự thay đổi
    stats = {
        "attendance": "98%" if int(child_id[-1], 16) % 2 == 0 else "92%",
        "avg_quiz": 8.8,
        "videos": 15,
        "rank": "Explorer"
    }
    return stats

# --- GIAO DIỆN CHÍNH ---
st.title("📊 Báo Cáo Chuyên Sâu Hành Trình Lớn Khôn")

# 2. CHỌN CON ĐỂ XEM BÁO CÁO (NÂNG CẤP QUAN TRỌNG)
children = get_my_children()

if not children:
    st.info("Bạn chưa liên kết với tài khoản học sinh nào. Vui lòng vào mục 'Quản lý con' để tạo tài khoản cho bé.")
    st.stop()

# Tạo danh sách chọn bé
child_options = {c["id"]: c["name"] for c in children}
selected_child_id = st.selectbox(
    "🔍 Chọn con để xem báo cáo:", 
    options=list(child_options.keys()), 
    format_func=lambda x: child_options[x]
)

st.write(f"Đang hiển thị dữ liệu của bé: **{child_options[selected_child_id]}**")
st.divider()

# 3. THỐNG KÊ NHANH (Dữ liệu thay đổi theo bé được chọn)
child_stats = get_learning_stats(selected_child_id)

col1, col2, col3, col4 = st.columns(4)
col1.metric(label="Tỷ lệ chuyên cần", value=child_stats["attendance"], delta="Tăng 2%")
col2.metric(label="Điểm trung bình Quiz", value=f"{child_stats['avg_quiz']}/10", delta="Tăng 0.5")
col3.metric(label="Video AI đã học", value=f"{child_stats['videos']} video", delta="Mới")
col4.metric(label="Hạng hiện tại", value=child_stats["rank"], delta="Xuất sắc")

st.divider()

# 4. BIỂU ĐỒ TIẾN ĐỘ (Lấy dữ liệu thực tế từ Quiz của TV2)
st.subheader("📈 Biểu đồ điểm số các bài Quiz gần đây")

# Giả lập dữ liệu biểu đồ khác nhau cho từng bé
data_points = [7, 8, 9, 8, 10] if "1" in selected_child_id else [6, 9, 8, 7, 9]
chart_data = pd.DataFrame(data_points, columns=["Điểm số"])
st.line_chart(chart_data)

# 5. NHẬN XÉT CỦA GIÁO VIÊN (Kết nối dữ liệu từ TV2)
st.subheader("👩‍🏫 Nhận xét định kỳ từ Giáo viên")

# Trong thực tế, bạn sẽ gọi API: GET /api/tv2/comments?student_id=selected_child_id
# Dưới đây là cách hiển thị mẫu
comments = [
    {
        "subject": "Tiếng Anh Giao Tiếp",
        "teacher": "Thầy John",
        "date": "20/05/2026",
        "content": f"Bé {child_options[selected_child_id]} rất tích cực phát biểu. Phát âm ngày càng tiến bộ."
    }
]

for comment in comments:
    with st.container(border=True):
        st.markdown(f"### 🌍 {comment['subject']}")
        st.caption(f"Giáo viên: {comment['teacher']} | Ngày: {comment['date']}")
        st.write(f"> *{comment['content']}*")