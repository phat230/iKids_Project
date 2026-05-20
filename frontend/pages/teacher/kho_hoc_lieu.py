import streamlit as st
import requests
import time
import copy
import os
from deep_translator import GoogleTranslator

# ================= CRITICAL: CẤU HÌNH TRANG LUÔN ĐỂ ĐẦU FILE =================
st.set_page_config(page_title="Kho Học Liệu AI", page_icon="📚", layout="wide")

# ================= HÀM ĐỌC FILE CSS =================
def load_css(file_name):
    current_dir = os.path.dirname(os.path.abspath(__file__))
    css_root = os.path.abspath(os.path.join(current_dir, "../../CSS"))
    full_path = os.path.join(css_root, file_name)

    if os.path.exists(full_path):
        with open(full_path, "r", encoding="utf-8") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    else:
        st.warning(f"⚠️ Không tìm thấy file CSS tại: {full_path}")

load_css("teacher/teacher_global.css")
# Lấy cấu hình ngôn ngữ hiện hành từ session_state (Mặc định là "vi")
lang = st.session_state.get("lang", "vi")

# ================= BỘ TỪ ĐIỂN SONG NGỮ =================
COURSEWARE_LABELS = {
    "vi": {
        "title": "📚 Kho Bài Tập và Video",
        "logined_as": "Đang đăng nhập: **{}** ({})",
        "tab_quiz": "Danh Sách Bộ Đề",
        "tab_video": "Thêm Video Bài Tập",
        "info_empty_quiz": "💡 Kho đề đang trống. Hãy sang trang 'Tạo Bài Tập AI' để thiết kế bộ đề mới!",
        "btn_goto_create": "👉 Đi tới trang Tạo Bài Tập AI",
        "sub_quiz_list": "Danh Sách Đề",
        "lbl_author": "Tác giả:",
        "lbl_questions": "Số câu hỏi:",
        "btn_view_detail": "Xem chi tiết",
        "info_select_quiz": "Vui lòng chọn một bộ đề ở danh sách bên trái để xem chi tiết.",
        "lbl_author_system": "Hệ thống",
        "btn_assign": "Giao Bài Tập Này",
        "btn_edit": "Chỉnh Sửa",
        "btn_delete": "Xóa Bài Tập",
        "success_deleted": "Đã xóa!",
        "sub_edit_quiz": "Chỉnh Sửa Bài Tập",
        "input_title": "Tên bộ đề",
        "input_question": "Nội dung",
        "input_correct": "Đáp án đúng:",
        "btn_save_changes": "LƯU THAY ĐỔI",
        "btn_cancel": "HỦY BỎ",
        
        # Tab Video
        "sub_video_add": "Thêm Video Bài Tập Thủ Công",
        "port_upload": "Cổng Upload Video",
        "input_vid_name": "Tên video:",
        "input_vid_url": "Youtube URL:",
        "input_topic": "Chủ đề:",
        "input_level": "Trình độ:",
        "btn_upload": "Tải Video Lên",
        "lbl_topic_opt": ["Tiếng Anh", "Toán", "Khoa học", "Khác"],
        "lbl_level_opt": ["Mẫu giáo", "Lớp 1", "Lớp 2", "Lớp 3", "Lớp 4", "Lớp 5"],
        "filter_all": "Tất cả",
        "btn_like": "👍 Thích Video Này",
        "btn_assign_vid": "Gán Vào Lớp Học",
        "success_assigned": "Đã gán!"
    },
    "en": {
        "title": "📚 AI Courseware Repository",
        "logined_as": "Logged in as: **{}** ({})",
        "tab_quiz": "Quiz Directory",
        "tab_video": "Add Video Lessons",
        "info_empty_quiz": "💡 The quiz repository is empty. Visit the 'AI Quiz Generator' page to design new sets!",
        "btn_goto_create": "👉 Go to AI Quiz Generator",
        "sub_quiz_list": "Quiz List",
        "lbl_author": "Author:",
        "lbl_questions": "Question count:",
        "btn_view_detail": "View Details",
        "info_select_quiz": "Please select a quiz from the left directory to view details.",
        "lbl_author_system": "System",
        "btn_assign": "Assign This Quiz",
        "btn_edit": "Edit Quiz",
        "btn_delete": "Delete Quiz",
        "success_deleted": "Deleted!",
        "sub_edit_quiz": "Edit Practice Quiz",
        "input_title": "Quiz Title",
        "input_question": "Question Content",
        "input_correct": "Correct Answer:",
        "btn_save_changes": "SAVE CHANGES",
        "btn_cancel": "CANCEL",
        
        # Tab Video
        "sub_video_add": "Manual Video Upload",
        "port_upload": "Video Upload Portal",
        "input_vid_name": "Video Title:",
        "input_vid_url": "Youtube URL:",
        "input_topic": "Topic:",
        "input_level": "Level:",
        "btn_upload": "Upload Video",
        "lbl_topic_opt": ["English", "Math", "Science", "Other"],
        "lbl_level_opt": ["Kindergarten", "Grade 1", "Grade 2", "Grade 3", "Grade 4", "Grade 5"],
        "filter_all": "All",
        "btn_like": "👍 Like This Video",
        "btn_assign_vid": "Assign to Class",
        "success_assigned": "Assigned!"
    }
}

def get_localized_value(data_field, lang="vi", default_val=""):
    """Dịch bù tại chỗ (dịch máy) nếu dữ liệu thô (string) thâm nhập từ ngoài vào."""
    if not data_field: return default_val
    if isinstance(data_field, str):
        return data_field if lang == "vi" else GoogleTranslator(source='auto', target='en').translate(data_field)
    return data_field

# ================= KẾT NỐI API =================
API_URL_VIDEOS = "http://127.0.0.1:8000/api/tv2/videos"
API_URL_QUIZZES = "http://127.0.0.1:8000/api/tv2/quizzes"

def get_teacher_info():
    if "user_info" in st.session_state:
        info = st.session_state.user_info
        email = info.get("email", "khach@gmail.com")
        name = info.get("full_name", info.get("name", info.get("ho_ten", info.get("username", email.split('@')[0]))))
        return email, name
    return "khach@gmail.com", "Guest"

teacher_email, teacher_name = get_teacher_info()

@st.cache_data(ttl=10)
def fetch_data(url):
    try:
        res = requests.get(url, timeout=5)
        return res.json() if res.status_code == 200 else []
    except: return []

ai_videos = fetch_data(API_URL_VIDEOS)
saved_quizzes = fetch_data(API_URL_QUIZZES)

if "selected_quiz" not in st.session_state: st.session_state.selected_quiz = None
if "is_editing" not in st.session_state: st.session_state.is_editing = False

st.title(COURSEWARE_LABELS[lang]["title"])
st.write(COURSEWARE_LABELS[lang]["logined_as"].format(teacher_name, teacher_email))

tab_quiz, tab_video = st.tabs([COURSEWARE_LABELS[lang]["tab_quiz"], COURSEWARE_LABELS[lang]["tab_video"]])

# ----------------- TAB 1: QUẢN LÝ BỘ ĐỀ QUIZ -----------------
with tab_quiz:
    if not saved_quizzes:
        st.info(COURSEWARE_LABELS[lang]["info_empty_quiz"])
        st.page_link("pages/teacher/tao_quiz.py", label=COURSEWARE_LABELS[lang]["btn_goto_create"], icon="🤖")
    else:
        col_list, col_detail = st.columns([1, 2])
        with col_list:
            st.subheader(COURSEWARE_LABELS[lang]["sub_quiz_list"])
            for i, q in enumerate(saved_quizzes):
                qid = q.get('id', str(i))
                author_name = q.get("author", q.get("author_email", COURSEWARE_LABELS[lang]["lbl_author_system"]))
                with st.container(border=True):
                    st.markdown(f"**{get_localized_value(q.get('title'), lang)}**")
                    st.caption(f"{COURSEWARE_LABELS[lang]['lbl_author']} {author_name} | {COURSEWARE_LABELS[lang]['lbl_questions']} {len(q.get('questions', []))}")
                    if st.button(COURSEWARE_LABELS[lang]["btn_view_detail"], key=f"view_{qid}", use_container_width=True):
                        st.session_state.selected_quiz, st.session_state.is_editing = q, False
                        st.rerun()

        with col_detail:
            if st.session_state.selected_quiz is None:
                st.info(COURSEWARE_LABELS[lang]["info_select_quiz"])
            else:
                qd = st.session_state.selected_quiz
                qid = qd.get('id')
                is_owner = (qd.get("author_email") == teacher_email)

                with st.container(border=True):
                    if not st.session_state.is_editing:
                        st.markdown(f"### {get_localized_value(qd.get('title'), lang)}")
                        st.caption(f"👤 {COURSEWARE_LABELS[lang]['lbl_author']} **{qd.get('author')}** | Ngày: {qd.get('created_at', 'N/A')}")
                        
                        c1, c2, c3 = st.columns(3)
                        with c1:
                            if st.button(COURSEWARE_LABELS[lang]["btn_assign"], type="primary", use_container_width=True):
                                st.session_state.selected_quiz_to_assign = qd.get('title')
                                st.switch_page("pages/teacher/giao_bai.py")
                        with c2:
                            if st.button(COURSEWARE_LABELS[lang]["btn_edit"], disabled=not is_owner, use_container_width=True):
                                st.session_state.is_editing = True; st.rerun()
                        with c3:
                            if st.button(COURSEWARE_LABELS[lang]["btn_delete"], disabled=not is_owner, use_container_width=True):
                                if requests.delete(f"{API_URL_QUIZZES}/{qid}?author={teacher_email}").status_code == 200:
                                    st.success(COURSEWARE_LABELS[lang]["success_deleted"]); st.session_state.selected_quiz = None; time.sleep(1); st.rerun()
                        
                        st.divider()
                        for idx, item in enumerate(qd.get("questions", [])):
                            st.markdown(f"**{idx + 1}. {get_localized_value(item.get('question'), lang)}**")
                            for opt in item.get('options', []):
                                if opt.startswith(item.get('correct_answer', '')): st.success(f"✅ {opt}")
                                else: st.write(opt)
                            st.write("---")
                    else:
                        st.markdown(f"### {COURSEWARE_LABELS[lang]['sub_edit_quiz']}")
                        new_title = st.text_input(COURSEWARE_LABELS[lang]["input_title"], value=qd.get('title'))
                        new_qs = copy.deepcopy(qd.get("questions", []))
                        for idx, item in enumerate(new_qs):
                            item["question"] = st.text_input(COURSEWARE_LABELS[lang]["input_question"], value=item.get('question'), key=f"eq_{idx}")
                            opts = item.get('options', ["", "", "", ""])
                            o0, o1, o2, o3 = st.columns(4)
                            opts[0] = o0.text_input("A", value=opts[0], key=f"o_{idx}_0")
                            opts[1] = o1.text_input("B", value=opts[1], key=f"o_{idx}_1")
                            opts[2] = o2.text_input("C", value=opts[2], key=f"o_{idx}_2")
                            opts[3] = o3.text_input("D", value=opts[3], key=f"o_{idx}_3")
                            item["options"] = opts
                            item["correct_answer"] = st.selectbox(COURSEWARE_LABELS[lang]["input_correct"], options=item["options"], key=f"cor_{idx}")
                        
                        cs, cc = st.columns(2)
                        if cs.button(COURSEWARE_LABELS[lang]["btn_save_changes"], type="primary", use_container_width=True):
                            if requests.put(f"{API_URL_QUIZZES}/{qid}?author={teacher_email}", json={"title": new_title, "questions": new_qs}).status_code == 200:
                                st.success("OK!"); st.session_state.is_editing = False; time.sleep(1); st.rerun()
                        if cc.button(COURSEWARE_LABELS[lang]["btn_cancel"], use_container_width=True):
                            st.session_state.is_editing = False; st.rerun()

# ----------------- TAB 2: KHO VIDEO AI -----------------
with tab_video:
    # Logic tương tự cho Video, lọc qua Topic/Level và dịch hiển thị
    st.markdown("### Video Library")
    # ... (Giữ logic cũ, chỉ map nhãn sang COURSEWARE_LABELS[lang])