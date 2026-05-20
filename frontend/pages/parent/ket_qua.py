import streamlit as st
import pandas as pd
import requests
import os

# ================= CRITICAL: CẤU HÌNH TRANG LUÔN ĐỂ ĐẦU FILE =================
st.set_page_config(page_title="Báo Cáo Học Tập - iKids", layout="wide")

# Cấu hình API
API_TV3 = "http://localhost:8000/api/tv3"

# ================= HÀM ĐỌC FILE CSS (SỬA LỖI ĐƯỜNG DẪN TUYỆT ĐỐI) =================
def load_css(file_name):
    """
    Tự động tìm file CSS trong thư mục frontend/CSS/
    file_name: tên file kèm thư mục con, ví dụ 'parent/ket_qua.css'
    """
    current_dir = os.path.dirname(os.path.abspath(__file__))
    css_root = os.path.abspath(os.path.join(current_dir, "../../CSS"))
    full_path = os.path.join(css_root, file_name)

    if os.path.exists(full_path):
        with open(full_path, "r", encoding="utf-8") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    else:
        st.warning(f"⚠️ Không tìm thấy file CSS tại: {full_path}")

# Tải CSS làm đẹp
load_css("parent/parent_global.css")
# Lấy cấu hình ngôn ngữ hiện hành từ session_state (Mặc định là "vi")
lang = st.session_state.get("lang", "vi")

# ==========================================
# BỘ TỪ ĐIỂN SONG NGỮ CHI TIẾT CHO KET_QUA
# ==========================================
REPORT_LABELS = {
    "vi": {
        "err_login": "⚠️ Vui lòng đăng nhập để xem báo cáo của các bé.",
        "title": "📊 Báo Cáo Chuyên Sâu Hành Trình Lớn Khôn",
        "warn_no_child": "ℹ️ Bạn chưa liên kết với tài khoản học sinh nào. Vui lòng vào mục 'Quản lý con em' để tạo tài khoản cho bé.",
        "select_child": "👧 Chọn con để xem báo cáo:",
        "lbl_viewing": "Đang hiển thị dữ liệu của bé:",
        
        # Chỉ số Metrics
        "metric_attendance": "Tỷ lệ chuyên cần",
        "metric_quiz": "Điểm trung bình Quiz",
        "metric_videos": "Video AI đã học",
        "metric_rank": "Hạng hiện tại",
        "delta_attendance": "Tăng 2%",
        "delta_quiz": "Tăng 0.5",
        "delta_videos": "Mới",
        "delta_rank": "Xuất sắc",
        "unit_videos": "video",
        
        # Biểu đồ & Nhận xét
        "chart_title": "📈 Biểu đồ điểm số các bài tập Quiz gần đây",
        "chart_y_label": "Điểm số",
        "comment_title": "📝 Nhận xét định kỳ từ Giáo viên",
        "comment_lbl_teacher": "Giáo viên",
        "comment_lbl_date": "Ngày",
        "comment_lbl_content": "Nhận xét:",
        
        # Nội dung nhận xét mẫu được dịch thuật chuyên nghiệp
        "sub_english": "Tiếng Anh Giao Tiếp",
        "teacher_john": "Thầy John",
        "comment_john": "rất tích cực phát biểu trên lớp. Khả năng phát âm tiếng Anh ngày càng tự tin và tiến bộ rõ rệt.",
        "sub_math": "Toán Tư Duy",
        "teacher_lan": "Cô Lan",
        "comment_lan": "nắm vững các quy tắc logic rất tốt, tập trung nghe giảng và làm bài tập về nhà đầy đủ."
    },
    "en": {
        "err_login": "⚠️ Authentication required. Please log in to view student learning reports.",
        "title": "📊 Growth Journey & Learning Analytics",
        "warn_no_child": "ℹ️ No student profiles found associated with your account. Please go to 'Manage Children' to register a profile first.",
        "select_child": "👧 Select child to view reports:",
        "lbl_viewing": "Displaying academic reports for:",
        
        # Metrics labels
        "metric_attendance": "Attendance Rate",
        "metric_quiz": "Average Quiz Score",
        "metric_videos": "AI Videos Completed",
        "metric_rank": "Current Rank",
        "delta_attendance": "+2% Up",
        "delta_quiz": "+0.5 Up",
        "delta_videos": "New",
        "delta_rank": "Excellent",
        "unit_videos": "videos",
        
        # Charts & Comments
        "chart_title": "📈 Recent AI Quiz Score Progress Chart",
        "chart_y_label": "Score",
        "comment_title": "📝 Academic Progress Comments from Instructors",
        "comment_lbl_teacher": "Instructor",
        "comment_lbl_date": "Date",
        "comment_lbl_content": "Feedback Notes:",
        
        # Translated comment payloads
        "sub_english": "Communicative English",
        "teacher_john": "Mr. John",
        "comment_john": "participates very actively in class discussions. English pronunciation is becoming noticeably more confident and progressive.",
        "sub_math": "Critical Thinking Math",
        "teacher_lan": "Ms. Lan",
        "comment_lan": "demonstrates a solid grasp of logical reasoning rules, stays highly focused, and finishes all homework diligently."
    }
}

# 1. KIỂM TRA ĐĂNG NHẬP
parent_id = st.session_state.get("user_id")
token = st.session_state.get("access_token") or st.session_state.get("token")

if not parent_id or not token:
    st.error(REPORT_LABELS[lang]["err_login"])
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
    last_char = child_id[-1] if child_id else "0"
    try:
        is_even = int(last_char, 16) % 2 == 0
    except ValueError:
        is_even = True
        
    stats = {
        "attendance": "98%" if is_even else "92%",
        "avg_quiz": 8.8 if is_even else 7.5,
        "videos": 15 if is_even else 8,
        "rank": "Explorer" if is_even else "Beginner"
    }
    return stats

# --- GIAO DIỆN CHÍNH ---
st.title(REPORT_LABELS[lang]["title"])

# 2. CHỌN CON ĐỂ XEM BÁO CÁO
children = get_my_children()

if not children:
    st.info(REPORT_LABELS[lang]["warn_no_child"])
    st.stop()

child_options = {c["id"]: c["name"] for c in children}
selected_child_id = st.selectbox(
    REPORT_LABELS[lang]["select_child"], 
    options=list(child_options.keys()), 
    format_func=lambda x: child_options[x]
)

st.write(f"ℹ️ {REPORT_LABELS[lang]['lbl_viewing']} **{child_options[selected_child_id]}**")
st.divider()

# 3. THỐNG KÊ KPI NHANH VỚI TRẠNG THÁI i18n
child_stats = get_learning_stats(selected_child_id)

col1, col2, col3, col4 = st.columns(4)
col1.metric(label=REPORT_LABELS[lang]["metric_attendance"], value=child_stats["attendance"], delta=REPORT_LABELS[lang]["delta_attendance"])
col2.metric(label=REPORT_LABELS[lang]["metric_quiz"], value=f"{child_stats['avg_quiz']}/10", delta=REPORT_LABELS[lang]["delta_quiz"])
col3.metric(label=REPORT_LABELS[lang]["metric_videos"], value=f"{child_stats['videos']} {REPORT_LABELS[lang]['unit_videos']}", delta=REPORT_LABELS[lang]["delta_videos"])
col4.metric(label=REPORT_LABELS[lang]["metric_rank"], value=child_stats["rank"], delta=REPORT_LABELS[lang]["delta_rank"])

st.divider()

# 4. BIỂU ĐỒ TIẾN ĐỘ DỊCH TÊN TRỤC Y
st.subheader(REPORT_LABELS[lang]["chart_title"])
try:
    last_val = int(selected_child_id[-1], 16) % 2 == 0
except ValueError:
    last_val = True

data_points = [7, 8, 9, 8, 10] if last_val else [6, 9, 8, 7, 9]
chart_data = pd.DataFrame(data_points, columns=[REPORT_LABELS[lang]["chart_y_label"]])
st.line_chart(chart_data)

# 5. NHẬN XÉT ĐA NGÔN NGỮ CỦA GIÁO VIÊN
st.subheader(REPORT_LABELS[lang]["comment_title"])

# Tạo chuỗi lắp ráp tên bé động để bản dịch tiếng Anh và tiếng Việt thuận tai, tự nhiên
child_name = child_options[selected_child_id]
comment_english_text = f"Student {child_name} {REPORT_LABELS[lang]['comment_john']}" if lang == "en" else f"Bé {child_name} {REPORT_LABELS[lang]['comment_john']}"
comment_math_text = f"Student {child_name} {REPORT_LABELS[lang]['comment_lan']}" if lang == "en" else f"Bé {child_name} {REPORT_LABELS[lang]['comment_lan']}"

comments = [
    {
        "subject": REPORT_LABELS[lang]["sub_english"],
        "teacher": REPORT_LABELS[lang]["teacher_john"],
        "date": "20/05/2026",
        "content": comment_english_text
    },
    {
        "subject": REPORT_LABELS[lang]["sub_math"],
        "teacher": REPORT_LABELS[lang]["teacher_lan"],
        "date": "18/05/2026",
        "content": comment_math_text
    }
]

for comment in comments:
    with st.container(border=True):
        st.markdown(f"### 📚 {comment['subject']}")
        st.caption(f"👤 {REPORT_LABELS[lang]['comment_lbl_teacher']}: {comment['teacher']} | 📅 {REPORT_LABELS[lang]['comment_lbl_date']}: {comment['date']}")
        st.markdown(f"**{REPORT_LABELS[lang]['comment_lbl_content']}**")
        st.markdown(f"> {comment['content']}")