import streamlit as st
import os
from api_clients.tv3_client import get_memories, like_memory
from deep_translator import GoogleTranslator  # Thêm bộ dịch dự phòng trực tiếp tại chỗ

# ================= CRITICAL: CẤU HÌNH TRANG LUÔN ĐỂ ĐẦU FILE =================
st.set_page_config(page_title="Góc Kỷ Niệm", page_icon="📸")

# ================= HÀM ĐỌC FILE CSS (SỬA LỖI ĐƯỜNG DẪN) =================
def load_css(file_name):
    """
    Tự động tìm file CSS trong thư mục frontend/CSS/
    file_name: tên file kèm thư mục con, ví dụ 'student/ky_niem.css'
    """
    # Lấy đường dẫn tuyệt đối của thư mục chứa file hiện tại (frontend/pages/student)
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Lùi 2 cấp để về thư mục iKids_Project, sau đó vào frontend/CSS
    css_root = os.path.abspath(os.path.join(current_dir, "../../CSS"))
    full_path = os.path.join(css_root, file_name)

    if os.path.exists(full_path):
        with open(full_path, "r", encoding="utf-8") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    else:
        st.warning(f"⚠️ Không tìm thấy file CSS tại: {full_path}")

# Tải CSS làm đẹp cho trang Kỷ Niệm học sinh
load_css("student/student_global.css")
BACKEND_URL = st.session_state.get("api_url", "http://localhost:8000")
lang = st.session_state.get("lang", "vi")

# ==========================================
# BỘ TỪ ĐIỂN SONG NGỮ CHI TIẾT CHO STUDENT KY_NIEM
# ==========================================
STUDENT_MEMORY_LABELS = {
    "vi": {
        "title": "📸 Góc Kỷ Niệm",
        "subtitle": "Nơi lưu giữ những khoảnh khắc học tập và vui chơi tuyệt vời của các bé!",
        "info_empty": "✨ Hiện chưa có khoảnh khắc kỷ niệm nào được chia sẻ.",
        "lbl_teacher_share": "đã chia sẻ một khoảnh khắc:",
        "default_teacher": "Giáo viên",
        "no_description": "Không có mô tả."
    },
    "en": {
        "title": "📸 Memories Corner",
        "subtitle": "A magical place holding all our wonderful learning and playing moments! ✨",
        "info_empty": "✨ No class memories have been shared here yet.",
        "lbl_teacher_share": "shared a wonderful moment:",
        "default_teacher": "Teacher",
        "no_description": "No description provided."
    }
}

def get_localized_value(data_field, lang="vi", default_val=""):
    """
    Hàm bóc tách dữ liệu thông minh cho phần mô tả kỷ niệm:
    - Nếu là dict đa ngôn ngữ: Lấy chính xác ngôn ngữ đích.
    - Nếu là chuỗi phẳng tiếng Việt thô: Tự động dịch bù sang tiếng Anh tức thì tại chỗ.
    """
    if not data_field:
        return default_val
    if isinstance(data_field, dict):
        return data_field.get(lang, data_field.get("vi", default_val))
    if isinstance(data_field, str):
        if lang == "vi":
            return data_field
        else:
            try:
                # Tự động nhận diện tiếng Việt thô và dịch sang English cho các em nhỏ
                return GoogleTranslator(source='auto', target='en').translate(data_field)
            except Exception:
                return data_field  # Trả về bản gốc nếu mất kết nối mạng
    return default_val

# ================= GIAO DIỆN CHÍNH =================
st.title(STUDENT_MEMORY_LABELS[lang]["title"])
st.write(STUDENT_MEMORY_LABELS[lang]["subtitle"])
st.divider()

try:
    memories = get_memories()
except Exception:
    memories = []

if not memories:
    st.info(STUDENT_MEMORY_LABELS[lang]["info_empty"])
else:
    # Hiển thị giống dạng feed của mạng xã hội (Social Media Timeline Grid)
    for item in memories:
        with st.container(border=True):
            # Phần tiêu đề bài đăng
            t_name = item.get('teacher_name') or STUDENT_MEMORY_LABELS[lang]["default_teacher"]
            if t_name == "Giáo viên" and lang == "en":
                t_name = "Teacher"
                
            st.markdown(f"**👨‍🏫 {t_name}** {STUDENT_MEMORY_LABELS[lang]['lbl_teacher_share']}")
            
            # Cắt chuỗi ngày tháng an toàn đề phòng dữ liệu trống
            raw_date = item.get('created_at', '')
            time_str = raw_date[:16].replace('T', ' ') if len(raw_date) >= 16 else "---"
            st.caption(f"🗓️ {time_str}")
            
            # Hiển thị ảnh kỷ niệm lớp học
            st.image(item.get("media_url", "https://via.placeholder.com/800x500"), use_container_width=True)
            
            # Mô tả bài viết (Tự động thích ứng đa ngôn ngữ và xử lý dịch máy bù tại chỗ)
            memory_description = get_localized_value(item.get('description'), lang=lang, default_val=STUDENT_MEMORY_LABELS[lang]["no_description"])
            st.markdown(f"<div class='memory-desc'>{memory_description}</div>", unsafe_allow_html=True)
            
            # Khu vực tương tác (Thả tim)
            col1, col2 = st.columns([1, 5])
            with col1:
                likes = item.get('likes', 0)
                m_id = item.get('_id', item.get('id'))
                # Dùng key động để Streamlit phân biệt các nút thả tim khác nhau
                if st.button(f"❤️ {likes}", key=f"like_{m_id}"):
                    if like_memory(m_id):
                        st.rerun()  # Load lại trang để cập nhật số tim tăng lên ngay lập tức