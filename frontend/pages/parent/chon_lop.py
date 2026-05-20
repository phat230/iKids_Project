import streamlit as st
import requests
import os

# ================= CRITICAL: CẤU HÌNH TRANG LUÔN ĐỂ ĐẦU FILE =================
st.set_page_config(page_title="Đăng Ký Lớp Học", page_icon="🏫")

# Cấu hình API Backend
API_URL = "http://localhost:8000"
API_TV3 = "http://localhost:8000/api/tv3"

# ================= HÀM ĐỌC FILE CSS (SỬA LỖI ĐƯỜNG DẪN TUYỆT ĐỐI) =================
def load_css(file_name):
    """
    Tự động tìm file CSS trong thư mục frontend/CSS/
    file_name: tên file kèm thư mục con, ví dụ 'parent/chon_lop.css'
    """
    current_dir = os.path.dirname(os.path.abspath(__file__))
    css_root = os.path.abspath(os.path.join(current_dir, "../../CSS"))
    full_path = os.path.join(css_root, file_name)

    if os.path.exists(full_path):
        with open(full_path, "r", encoding="utf-8") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    else:
        st.warning(f"⚠️ Không tìm thấy file CSS tại: {full_path}")

# Tải CSS
load_css("parent/parent_global.css")
# Lấy cấu hình ngôn ngữ hiện hành từ session_state (Mặc định là "vi")
lang = st.session_state.get("lang", "vi")

# ==========================================
# BỘ TỪ ĐIỂN SONG NGỮ CHI TIẾT CHO CHON_LOP
# ==========================================
ENROLL_LABELS = {
    "vi": {
        "title": "🏫 Đăng Ký Lớp Học Cho Con",
        "subtitle": "Dưới đây là danh sách các lớp học đang mở. Phụ huynh có thể chọn lớp phù hợp cho con em mình.",
        "err_login": "⚠️ Vui lòng đăng nhập với tài khoản Phụ huynh để đăng ký lớp học.",
        "warn_no_child": "⚠️ Bạn chưa có hồ sơ học sinh nào. Vui lòng sang trang 'Quản Lý Con Em' để tạo tài khoản cho bé trước khi đăng ký lớp!",
        "err_connection": "⚠️ Không thể kết nối đến máy chủ Backend:",
        "info_empty_classes": "ℹ️ Hiện tại hệ thống chưa có lớp học nào đang mở đăng ký công khai.",
        "lbl_class_unknown": "Tên lớp chưa rõ",
        "lbl_subject": "Môn học:",
        "lbl_sub_unassigned": "Chưa cập nhật",
        "lbl_teacher": "Giáo viên phụ trách:",
        "lbl_teacher_arranging": "Đang xếp",
        "select_child": "👧 Chọn bé tham gia lớp này:",
        "btn_enroll": "🚀 Đăng Ký Học Ngay",
        "warn_already_enrolled": "Bé đã được đăng ký lớp này từ trước rồi!",
        "success_enrolled": "🎉 Đã đăng ký thành công cho bé",
        "err_failed_enroll": "❌ Đăng ký thất bại. Lớp học có thể đã đầy hoặc đóng sổ.",
        "err_post_connection": "❌ Lỗi kết nối khi gửi yêu cầu đăng ký học."
    },
    "en": {
        "title": "🏫 Course Enrollment for Children",
        "subtitle": "Below is the list of active open classes. Parents can review and select the most suitable option for their children.",
        "err_login": "⚠️ Authentication required. Please log in with a Parent account to enroll in classes.",
        "warn_no_child": "⚠️ No student profiles found associated with your account. Please go to 'Manage Children' to create a profile for your child first!",
        "err_connection": "⚠️ Unable to establish a connection to the Backend server:",
        "info_empty_classes": "ℹ️ There are currently no open classes available for public registration.",
        "lbl_class_unknown": "Unknown Class Title",
        "lbl_subject": "Subject:",
        "lbl_sub_unassigned": "Unassigned",
        "lbl_teacher": "Instructor:",
        "lbl_teacher_arranging": "TBD",
        "select_child": "👧 Select child for this class:",
        "btn_enroll": "🚀 Enroll Now",
        "warn_already_enrolled": "is already registered and enrolled in this class session!",
        "success_enrolled": "🎉 Registration successful for",
        "err_failed_enroll": "❌ Enrollment failed. The selected class might be fully occupied.",
        "err_post_connection": "❌ Connection error occurred while submitting enrollment request."
    }
}

st.title(ENROLL_LABELS[lang]["title"])
st.write(ENROLL_LABELS[lang]["subtitle"])

# 1. KIỂM TRA ĐĂNG NHẬP
parent_id = st.session_state.get("user_id")
token = st.session_state.get("access_token") or st.session_state.get("token")

if not parent_id or not token:
    st.error(ENROLL_LABELS[lang]["err_login"])
    st.stop()

headers = {"Authorization": f"Bearer {token}", "parent-id": str(parent_id)}

# 2. LẤY DANH SÁCH CÁC CON CỦA PHỤ HUYNH
@st.cache_data(ttl=30)
def get_my_children():
    try:
        res = requests.get(f"{API_TV3}/parent/my-children", headers=headers)
        return res.json() if res.status_code == 200 else []
    except:
        return []

children = get_my_children()

if not children:
    st.warning(ENROLL_LABELS[lang]["warn_no_child"])
    st.stop()

# Tạo Dictionary để đưa vào ô Selectbox
child_options = {c["id"]: c["name"] for c in children}

st.divider()

# 3. GỌI API LẤY DANH SÁCH LỚP PUBLIC
try:
    res = requests.get(f"{API_URL}/classes/public")
    public_classes = res.json() if res.status_code == 200 else []
except Exception as e:
    st.error(f"{ENROLL_LABELS[lang]['err_connection']} {e}")
    public_classes = []

# 4. HIỂN THỊ DANH SÁCH LỚP HỌC
if not public_classes:
    st.info(ENROLL_LABELS[lang]["info_empty_classes"])
else:
    for cls in public_classes:
        with st.container(border=True):
            col1, col2 = st.columns([3, 2])
            
            class_id = cls.get('id', cls.get('_id', ''))
            
            with col1:
                st.markdown(f"#### 📚 {cls.get('class_name', ENROLL_LABELS[lang]['lbl_class_unknown'])}")
                
                # Tận dụng dịch động môn học nếu thâm nhập thô dạng chuỗi phẳng chữ Việt gốc
                subject_raw = cls.get('subject', ENROLL_LABELS[lang]['lbl_sub_unassigned'])
                subject_display = subject_raw
                if lang == "en" and subject_raw == "Chưa xác định":
                    subject_display = "Unassigned"
                
                st.write(f"**{ENROLL_LABELS[lang]['lbl_subject']}** {subject_display}")
                
                t_name = cls.get('teacher_name') or ENROLL_LABELS[lang]['lbl_teacher_arranging']
                if t_name == "Chưa phân công":
                    t_name = "Unassigned" if lang == "en" else "Chưa phân công"
                st.caption(f"👤 {ENROLL_LABELS[lang]['lbl_teacher']} {t_name}")
            
            with col2:
                selected_child_id = st.selectbox(
                    ENROLL_LABELS[lang]["select_child"],
                    options=list(child_options.keys()),
                    format_func=lambda x: child_options[x],
                    key=f"child_select_{class_id}"
                )
                
                if st.button(ENROLL_LABELS[lang]["btn_enroll"], key=f"btn_{class_id}", type="primary", use_container_width=True):
                    current_students = cls.get("student_ids", [])
                    
                    if selected_child_id in current_students:
                        if lang == "vi":
                            st.warning(f"Bé **{child_options[selected_child_id]}** {ENROLL_LABELS[lang]['warn_already_enrolled']}")
                        else:
                            st.warning(f"**{child_options[selected_child_id]}** {ENROLL_LABELS[lang]['warn_already_enrolled']}")
                    else:
                        payload = {"class_id": class_id, "student_id": selected_child_id}
                        try:
                            register_res = requests.post(f"{API_URL}/classes/register", json=payload)
                            
                            if register_res.status_code in [200, 201]:
                                st.success(f"{ENROLL_LABELS[lang]['success_enrolled']} **{child_options[selected_child_id]}**!")
                                st.balloons()
                                time.sleep(1)
                                st.rerun()
                            else:
                                st.error(ENROLL_LABELS[lang]["err_failed_enroll"])
                        except Exception:
                            st.error(ENROLL_LABELS[lang]["err_post_connection"])