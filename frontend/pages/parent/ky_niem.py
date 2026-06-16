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
    file_name: tên file kèm thư mục con, ví dụ 'parent/ky_niem.css'
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

load_css("parent/parent_global.css")
# Lấy cấu hình ngôn ngữ hiện hành từ session_state (Mặc định là "vi")
lang = st.session_state.get("lang", "vi")

# ==========================================
# BỘ TỪ ĐIỂN SONG NGỮ CHI TIẾT CHO KY_NIEM
# ==========================================
MEMORY_LABELS = {
    "vi": {
        "title": "📸 Góc Kỷ Niệm",
        "subtitle": "Nơi lưu giữ những khoảnh khắc học tập và vui chơi tuyệt vời của các bé!",
        "info_empty": "✨ Hiện chưa có kỷ niệm nào được chia sẻ. Những khoảnh khắc đáng yêu sẽ xuất hiện tại đây!",
        "default_teacher": "Giáo viên iKids",
        "hint_like": "Hãy nhấn tim để ủng hộ khoảnh khắc này của bé!",
        "no_description": "Không có mô tả bài viết."
    },
    "en": {
        "title": "📸 Class Memories Corner",
        "subtitle": "Preserving the wonderful and lovely learning and playing moments of our children!",
        "info_empty": "✨ There are currently no memories shared yet. Adorable moments will appear here soon!",
        "default_teacher": "iKids Teacher",
        "hint_like": "Click the heart button to show love and support for this moment!",
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
                # Tự động nhận diện tiếng Việt thô và dịch cưỡng bức sang English
                return GoogleTranslator(source='auto', target='en').translate(data_field)
            except Exception:
                return data_field  # Trả về bản gốc nếu mất kết nối mạng
    return default_val

# --- GIAO DIỆN CHÍNH ---
st.title(MEMORY_LABELS[lang]["title"])
st.write(MEMORY_LABELS[lang]["subtitle"])
st.divider()

# Lấy dữ liệu từ API
try:
    memories = get_memories()
except Exception:
    memories = []

if not memories:
    st.info(MEMORY_LABELS[lang]["info_empty"])
else:
    # Hiển thị dưới dạng dòng thời gian (Social Media Feed)
    for item in memories:
        with st.container(border=True):
            # Phần tiêu đề bài đăng (Avatar giả lập & Tên giáo viên)
            col_head1, col_head2 = st.columns([1, 10])
            with col_head1:
                st.write("")  # Có thể bổ sung avatar graphic nếu cần
            with col_head2:
                # Đồng bộ tên giáo viên mặc định nếu dữ liệu trả về rỗng
                t_name = item.get('teacher_name') or MEMORY_LABELS[lang]["default_teacher"]
                if t_name == "Giáo viên iKids" and lang == "en":
                    t_name = "iKids Teacher"
                
                st.markdown(f"**{t_name}**")
                
                # Cắt chuỗi ngày tháng an toàn đề phòng dữ liệu trống
                raw_date = item.get('created_at', '')
                time_str = raw_date[:16].replace('T', ' ') if len(raw_date) >= 16 else "---"
                st.caption(f"🕒 {time_str}")
            
            # ĐÃ SỬA: Xử lý an toàn triệt để cho ảnh hiển thị, loại bỏ via.placeholder
            media_url = item.get("media_url")
            if not media_url or "via.placeholder.com" in media_url:
                media_url = "static/anh_laptop.jpg"
            st.image(media_url, use_container_width=True)
            
            # Mô tả ảnh (Tự động thích ứng đa ngôn ngữ và xử lý dịch máy bù)
            memory_description = get_localized_value(item.get('description'), lang=lang, default_val=MEMORY_LABELS[lang]["no_description"])
            st.markdown(f"<div class='memory-desc'>{memory_description}</div>", unsafe_allow_html=True)
            
            # Khu vực tương tác (Thả tim)
            st.divider()
            col1, col2 = st.columns([1, 5])
            with col1:
                likes = item.get('likes', 0)
                m_id = str(item.get('_id', item.get('id')))
                # Sử dụng key động để Streamlit không bị loạn trạng thái giữa các dòng dữ liệu
                if st.button(f"❤️ {likes}", key=f"like_{m_id}"):
                    if like_memory(m_id):
                        st.rerun()  # Làm mới lại tại chỗ để cập nhật số lượng tim tăng lên lập tức
            with col2:
                st.caption(MEMORY_LABELS[lang]["hint_like"])