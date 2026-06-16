import streamlit as st
import pandas as pd
import requests
import os
import time

# ================= CRITICAL: CẤU HÌNH TRANG LUÔN ĐỂ ĐẦU FILE =================
st.set_page_config(page_title="Nhật Ký & Điểm Danh", page_icon=None, layout="wide")

# ================= HÀM ĐỌC FILE CSS =================
def load_css(file_name):
    current_dir = os.path.dirname(os.path.abspath(__file__))
    css_root = os.path.abspath(os.path.join(current_dir, "../../CSS"))
    full_path = os.path.join(css_root, file_name)
    if os.path.exists(full_path):
        with open(full_path, "r", encoding="utf-8") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

load_css("teacher/nhat_ky.css")

BACKEND_URL = st.session_state.get("api_url", "http://localhost:8000")
API_URL = BACKEND_URL
# ================= LẤY THÔNG TIN GIÁO VIÊN ĐĂNG NHẬP =================
user_info = st.session_state.get("user_info", {})
teacher_id = str(user_info.get("id", user_info.get("_id", "")))

# ================= HÀM GỌI API =================
@st.cache_data(ttl=5)
def get_my_schedules():
    try:
        headers = {"Authorization": f"Bearer {st.session_state.get('token', '')}"}
        res = requests.get(f"{API_URL}/schedule/list", headers=headers, timeout=10)
        if res.status_code == 200:
            schedules = res.json()
            my_scheds = []
            for s in schedules:
                t_teach = str(s.get("teaching_teacher_id", ""))
                t_resp = str(s.get("teacher_id", ""))
                if (teacher_id == t_teach or teacher_id == t_resp) and teacher_id != "":
                    my_scheds.append(s)
            return my_scheds
    except: pass
    return []

def get_class_students(class_id):
    """Gọi API lấy danh sách học viên theo class_id chuẩn xác"""
    if not class_id: return []
    try:
        res = requests.get(f"{API_URL}/classes/{class_id}/students/details", timeout=10)
        if res.status_code == 200:
            return res.json()
    except: pass
    return []

@st.cache_data(ttl=60)
def get_tv2_content():
    videos, quizzes = [], []
    try:
        v_res = requests.get(f"{API_URL}/api/tv2/videos", timeout=5)
        if v_res.status_code == 200: videos = v_res.json()
        q_res = requests.get(f"{API_URL}/api/tv2/quizzes", timeout=5)
        if q_res.status_code == 200: quizzes = q_res.json()
    except: pass
    return videos, quizzes

# ================= GIAO DIỆN CHÍNH =================
st.markdown("Ghi nhận điểm danh và đánh giá học sinh từ danh sách lớp thực tế.")

# --- PHẦN 1: LỰA CHỌN CA DẠY ---
st.subheader("1. Lựa chọn ca dạy")

c1, c2 = st.columns(2)
with c1:
    selected_date = st.date_input("Ngày dạy")

my_schedules = get_my_schedules()

day_name_mapping = {0: "Thứ 2", 1: "Thứ 3", 2: "Thứ 4", 3: "Thứ 5", 4: "Thứ 6", 5: "Thứ 7", 6: "Chủ nhật"}
selected_weekday = day_name_mapping[selected_date.weekday()]

available_scheds = []
for s in my_schedules:
    if selected_weekday in s.get("days_of_week", []):
        available_scheds.append(s)

with c2:
    if not available_scheds:
        st.warning("Không có lịch dạy nào được xếp vào ngày này.")
        selected_sched_id = None
    else:
        sched_options = {str(s.get("id", s.get("_id"))): f"{s.get('class_name')} - {s.get('subject')} ({s.get('start_time')})" for s in available_scheds}
        selected_sched_id = st.selectbox("Chọn ca dạy từ lịch học:", options=list(sched_options.keys()), format_func=lambda x: sched_options[x])

st.divider()

if not selected_sched_id:
    st.stop()

# --- BÓC TÁCH ID LỚP ĐỂ LẤY HỌC SINH THẬT ---
selected_sched = next((s for s in available_scheds if str(s.get("id", s.get("_id"))) == selected_sched_id), None)

# Lấy chuẩn xác class_id dạng chuỗi từ schedule
class_id = str(selected_sched.get("class_id", "")) if selected_sched else ""
class_name = selected_sched.get("class_name", "Không rõ lớp")

# --- PHẦN 2: CHIA CỘT ĐIỂM DANH & NHẬT KÝ ---
col_left, col_right = st.columns([1.5, 1])

# CỘT TRÁI: ĐIỂM DANH
with col_left:
    st.subheader(f"Điểm danh lớp: {class_name}")
    
    # Kéo dữ liệu thực tế từ Database
    real_students = get_class_students(class_id)
    
    # Dự phòng dữ liệu ảo
    if not real_students:
        st.info("Lớp học này hiện tại chưa có học sinh thật. Hệ thống tự động kích hoạt dữ liệu mẫu ổn định.")
        real_students = [
            {"Mã HS": "HS001_DEMO", "Tên Học Sinh": f"Nguyễn Văn A ({class_name} Demo)"},
            {"Mã HS": "HS002_DEMO", "Tên Học Sinh": f"Trần Thị B ({class_name} Demo)"},
            {"Mã HS": "HS003_DEMO", "Tên Học Sinh": f"Lê Hoàng C ({class_name} Demo)"},
            {"Mã HS": "HS004_DEMO", "Tên Học Sinh": f"Phạm Mai D ({class_name} Demo)"},
        ]
    
    # Đồng bộ hóa khởi tạo DataFrame động
    state_key = f"df_att_state_{selected_sched_id}"
    if state_key not in st.session_state:
        df_init = pd.DataFrame(real_students)[["Mã HS", "Tên Học Sinh"]]
        df_init["Có mặt"] = True
        df_init["Vắng"] = False
        df_init["Đi trễ"] = False
        df_init["Nhận Xét (Tùy chọn)"] = ""
        st.session_state[state_key] = df_init

    current_df = st.session_state[state_key]

    # Bảng Editor siêu mượt
    edited_att = st.data_editor(
        current_df,
        key=f"editor_widget_{selected_sched_id}",
        disabled=["Mã HS", "Tên Học Sinh"],
        column_config={
            "Có mặt": st.column_config.CheckboxColumn("Có mặt"),
            "Vắng": st.column_config.CheckboxColumn("Vắng"),
            "Đi trễ": st.column_config.CheckboxColumn("Đi trễ")
        },
        use_container_width=True,
        hide_index=True
    )
    
    # Xử lý Checkbox 1 trong 3 mượt mà
    for idx in range(len(edited_att)):
        row = edited_att.iloc[idx]
        old_row = current_df.iloc[idx]
        
        if row["Có mặt"] != old_row["Có mặt"] or row["Vắng"] != old_row["Vắng"] or row["Đi trễ"] != old_row["Đi trễ"]:
            if row["Có mặt"] and not old_row["Có mặt"]:
                st.session_state[state_key].at[idx, "Có mặt"] = True
                st.session_state[state_key].at[idx, "Vắng"] = False
                st.session_state[state_key].at[idx, "Đi trễ"] = False
                st.rerun()
            elif row["Vắng"] and not old_row["Vắng"]:
                st.session_state[state_key].at[idx, "Có mặt"] = False
                st.session_state[state_key].at[idx, "Vắng"] = True
                st.session_state[state_key].at[idx, "Đi trễ"] = False
                st.rerun()
            elif row["Đi trễ"] and not old_row["Đi trễ"]:
                st.session_state[state_key].at[idx, "Có mặt"] = False
                st.session_state[state_key].at[idx, "Vắng"] = False
                st.session_state[state_key].at[idx, "Đi trễ"] = True
                st.rerun()

# CỘT PHẢI: NHẬT KÝ BÀI GIẢNG
with col_right:
    st.subheader("Nhật Ký Bài Giảng")
    
    videos, quizzes = get_tv2_content()
    vid_options = {str(v.get("id", v.get("_id"))): v.get("title", "Video") for v in videos}
    quiz_options = {str(q.get("id", q.get("_id"))): q.get("title", "Bài tập") for q in quizzes}

    with st.form("journal_form", clear_on_submit=False):
        topic = st.text_input("Chủ Đề Giảng Dạy:", value=selected_sched.get("subject", ""))
        
        sel_vids = st.multiselect("Video Bài Tập Đã Dùng:", options=list(vid_options.keys()), format_func=lambda x: vid_options[x])
        sel_quizzes = st.multiselect("Giao Bài Tập Về Nhà:", options=list(quiz_options.keys()), format_func=lambda x: quiz_options[x])
        
        notes = st.text_area("Chi Tiết Nội Dung Giảng Dạy:")
        
        if st.form_submit_button("LƯU & GỬI BÁO CÁO", type="primary", use_container_width=True):
            if not topic or not notes:
                st.error("Vui lòng điền Chủ đề và Nội dung giảng dạy.")
            else:
                with st.spinner("Đang lưu nhật ký lên hệ thống..."):
                    # Gói dữ liệu để đẩy lên Backend
                    payload = {
                        "class_id": class_id,
                        "class_name": class_name,
                        "teacher_id": teacher_id,
                        "date": selected_date.strftime("%d/%m/%Y"),
                        "topic": topic,
                        "videos_used": sel_vids,
                        "quizzes_assigned": sel_quizzes,
                        "notes": notes,
                        "attendance": edited_att.to_dict('records') # Chuyển bảng điểm danh thành List JSON
                    }
                    
                    try:
                        headers = {"Authorization": f"Bearer {st.session_state.get('token', '')}"}
                        res = requests.post(f"{API_URL}/api/tv2/journal", json=payload, headers=headers)
                        
                        if res.status_code in [200, 201]:
                            st.session_state[state_key] = edited_att
                            st.success("Đã lưu nhật ký và điểm danh lên hệ thống thành công!")
                        else:
                            st.error(f"Lỗi từ máy chủ: {res.text}")
                    except Exception as e:
                        st.error(f"Lỗi kết nối đến Backend: {e}")