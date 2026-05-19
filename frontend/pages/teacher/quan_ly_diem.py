import streamlit as st
import pandas as pd
import requests
import os
import time
from datetime import datetime

# ================= ĐA NGÔN NGỮ =================
lang = st.session_state.get("lang", "vi")

GRADING_LABELS = {
    "vi": {
        "title": "Quản Lý & Ghi Điểm Học Tập",
        "desc": "Hệ thống sẽ tự động tính toán Điểm Tổng Kết dựa trên cấu hình mặc định.",
        "info_no_class": "Hiện tại thầy/cô chưa được Vận hành phân công phụ trách lớp học nào. Vui lòng liên hệ bộ phận Vận hành!",
        "select_class": "Chọn lớp học để ghi điểm:",
        "info_demo": "Lớp học này hiện tại chưa có học sinh thật được xếp vào. Hệ thống đang hiển thị dữ liệu mẫu để trải nghiệm tính năng.",
        "input_name": "Tên Học Sinh",
        "col_id": "Mã HS"
    },
    "en": {
        "title": "Grading & Academic Management",
        "desc": "System automatically calculates Final Grade based on default configuration.",
        "info_no_class": "You are currently not assigned to any classes by Operations. Please contact the Operations Department!",
        "select_class": "Select a class to grade:",
        "info_demo": "This class has no real students enrolled. Showing sample data for preview.",
        "input_name": "Student Name",
        "col_id": "Student ID"
    }
}

st.set_page_config(page_title="Ghi Điểm Học Tập", page_icon=None, layout="wide")

# ================= HÀM ĐỌC FILE CSS =================
def load_css(file_name):
    current_dir = os.path.dirname(os.path.abspath(__file__))
    css_root = os.path.abspath(os.path.join(current_dir, "../../CSS"))
    full_path = os.path.join(css_root, file_name)
    if os.path.exists(full_path):
        with open(full_path, "r", encoding="utf-8") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

load_css("teacher/quan_ly_diem.css")

API_URL = "http://127.0.0.1:8000"

# ================= LẤY THÔNG TIN GIÁO VIÊN =================
def get_teacher_info():
    if "user_info" in st.session_state:
        info = st.session_state.user_info
        t_id = info.get("id", info.get("_id", "gv_demo"))
        name = info.get("name", info.get("full_name", "Giáo viên"))
        return str(t_id), name
    return "gv_demo", "Khách"

teacher_id, teacher_name = get_teacher_info()

if "used_permissions" not in st.session_state:
    st.session_state.used_permissions = []

# ================= API DỮ LIỆU =================
@st.cache_data(ttl=5)
def get_my_classes(t_id):
    try:
        res = requests.get(f"{API_URL}/classes", timeout=10)
        if res.status_code == 200:
            all_classes = res.json()
            return [c for c in all_classes if str(c.get("teacher_id")) == t_id]
        return []
    except: return []

def get_class_students(class_id):
    try:
        res = requests.get(f"{API_URL}/classes/{class_id}/students/details", timeout=10)
        if res.status_code == 200: return res.json()
        return []
    except: return []

# ================= GIAO DIỆN CHÍNH =================
st.title(GRADING_LABELS[lang]["title"])
st.markdown(GRADING_LABELS[lang]["desc"])

# --- BƯỚC 1: CHỌN LỚP HỌC ---
my_classes = get_my_classes(teacher_id)

if not my_classes:
    st.info(GRADING_LABELS[lang]["info_no_class"])
    st.stop()

class_options = {str(c.get("id", c.get("_id"))): f"{c.get('class_name')} - {c.get('subject')}" for c in my_classes}

col_filter, col_empty = st.columns([1, 1])
with col_filter:
    selected_class_id = st.selectbox(GRADING_LABELS[lang]["select_class"], options=list(class_options.keys()), format_func=lambda x: class_options[x])

st.divider()

# --- BƯỚC 2: DỮ LIỆU HỌC SINH ---
real_students = get_class_students(selected_class_id)

if not real_students:
    st.info(GRADING_LABELS[lang]["info_demo"])
    real_students = [
        {GRADING_LABELS[lang]["col_id"]: "HS001_DEMO", GRADING_LABELS[lang]["input_name"]: "Nguyễn Văn A (Demo)"},
        {GRADING_LABELS[lang]["col_id"]: "HS002_DEMO", GRADING_LABELS[lang]["input_name"]: "Trần Thị B (Demo)"},
    ]

# ================= KIỂM TRA QUYỀN TRUY CẬP TỪ ADMIN =================
# Lấy danh sách yêu cầu để kiểm tra trạng thái phê duyệt
try:
    pending_reqs = requests.get(f"{API_URL}/pending-requests", timeout=5).json()
    history_reqs = requests.get(f"{API_URL}/request-history", timeout=5).json()
    all_reqs = pending_reqs + history_reqs
except:
    all_reqs = []

class_full_name = class_options[selected_class_id]

# Lọc các đơn "Xin cấp quyền nhập điểm" của Giáo viên này cho Lớp này
my_grade_reqs = [
    r for r in all_reqs 
    if r.get("teacher_id") == teacher_id 
    and r.get("type") == "Xin cấp quyền nhập điểm" 
    and class_full_name in r.get("details", "")
]

# Sắp xếp để lấy đơn mới nhất
def parse_date(date_str):
    try: return datetime.strptime(date_str, "%d/%m/%Y %H:%M")
    except: return datetime.min

my_grade_reqs.sort(key=lambda x: parse_date(x.get("created_at", "")), reverse=True)
latest_req = my_grade_reqs[0] if my_grade_reqs else None

is_approved = False
is_pending = False
active_req_id = None

if latest_req:
    if latest_req.get("status") == "pending":
        is_pending = True
    elif latest_req.get("status") == "approved":
        req_id = latest_req.get("id")
        # Kiểm tra xem quyền này đã bị sử dụng (thu hồi) chưa
        if req_id not in st.session_state.used_permissions:
            is_approved = True
            active_req_id = req_id

# ================= XỬ LÝ BẢNG ĐIỂM (EXCEL-LIKE) =================
st.markdown("#### Bảng Nhập Điểm Thành Phần (Thang điểm 10)")

if "grades_data_class" not in st.session_state or st.session_state.grades_data_class != selected_class_id:
    df_st = pd.DataFrame(real_students)[["Mã HS", "Tên Học Sinh"]]
    df_st["Chuyên Cần"] = 10.0
    for i in range(1, 6):
        df_st[f"KT {i}"] = 0.0
    df_st["Giữa Kỳ"] = 0.0
    df_st["Cuối Kỳ"] = 0.0
    
    st.session_state.grades_data = df_st
    st.session_state.grades_data_class = selected_class_id

# Phân nhánh hiển thị: Mở khóa (Data Editor) hoặc Khóa (Chỉ đọc)
if is_approved:
    st.success("Quyền nhập/sửa điểm đang được mở. Vui lòng ghi nhận lên hệ thống sau khi hoàn tất.")
    edited_df = st.data_editor(
        st.session_state.grades_data,
        disabled=["Mã HS", "Tên Học Sinh"], 
        use_container_width=True,
        hide_index=True,
        num_rows="dynamic"
    )
else:
    edited_df = st.session_state.grades_data.copy()
    st.dataframe(edited_df, use_container_width=True, hide_index=True)
    
    if is_pending:
        st.warning("Đơn yêu cầu cấp quyền nhập điểm đang chờ Admin phê duyệt...")
    else:
        st.warning("Bảng điểm hiện đang bị khóa. Bạn cần gửi yêu cầu để được cấp quyền nhập hoặc sửa điểm.")
        if st.button("Yêu cầu cấp quyền nhập/sửa điểm", type="primary"):
            new_req = {
                "teacher_id": teacher_id,
                "teacher_name": teacher_name,
                "type": "Xin cấp quyền nhập điểm",
                "details": f"Lớp: {class_full_name}",
                "reason": "Yêu cầu mở khóa bảng điểm để cập nhật điểm số cho học viên.",
                "status": "pending",
                "created_at": datetime.now().strftime("%d/%m/%Y %H:%M")
            }
            try:
                headers = {"Authorization": f"Bearer {st.session_state.get('token', '')}"}
                requests.post(f"{API_URL}/requests/create", json=new_req, headers=headers)
                st.success("Đã gửi yêu cầu thành công!")
                time.sleep(0.5)
                st.rerun()
            except:
                st.error("Lỗi kết nối đến máy chủ.")

# ================= TỰ ĐỘNG TÍNH TOÁN =================
st.markdown("#### Bảng Điểm Tổng Kết Môn Học")

kt_cols = [f"KT {i}" for i in range(1, 6)]
edited_df["TB Kiểm Tra"] = edited_df[kt_cols].mean(axis=1).fillna(0)

# Trọng số mặc định chạy ngầm (Không hiển thị ra UI)
midterm_weight = 30
final_weight = 70
weight_gk = midterm_weight / 100
weight_ck = final_weight / 100

edited_df["ĐIỂM TỔNG KẾT"] = (edited_df["Chuyên Cần"] * 0.1) + \
                             (edited_df["TB Kiểm Tra"] * 0.2) + \
                             (edited_df["Giữa Kỳ"] * 0.7 * weight_gk) + \
                             (edited_df["Cuối Kỳ"] * 0.7 * weight_ck)

edited_df["TB Kiểm Tra"] = edited_df["TB Kiểm Tra"].round(2)
edited_df["ĐIỂM TỔNG KẾT"] = edited_df["ĐIỂM TỔNG KẾT"].round(2)

def xep_loai(diem):
    if diem >= 8.5: return "Giỏi"
    elif diem >= 6.5: return "Khá"
    elif diem >= 5.0: return "TB"
    return "Yếu"

edited_df["Xếp Loại"] = edited_df["ĐIỂM TỔNG KẾT"].apply(xep_loai)

display_cols = ["Mã HS", "Tên Học Sinh", "Chuyên Cần", "TB Kiểm Tra", "Giữa Kỳ", "Cuối Kỳ", "ĐIỂM TỔNG KẾT", "Xếp Loại"]
st.dataframe(edited_df[display_cols], use_container_width=True, hide_index=True)

# ================= LƯU & XUẤT BÁO CÁO =================
c_btn1, c_btn2 = st.columns([2, 8])

# Nút Lưu chỉ hiện khi đang được cấp quyền
if is_approved:
    with c_btn1:
        if st.button("Ghi Nhận Lên Hệ Thống", type="primary", use_container_width=True):
            with st.spinner("Đang lưu trữ..."):
                time.sleep(1) 
                st.session_state.grades_data = edited_df.drop(columns=["TB Kiểm Tra", "ĐIỂM TỔNG KẾT", "Xếp Loại"])
                
                # Thu hồi quyền sau khi lưu thành công
                st.session_state.used_permissions.append(active_req_id)
                
                st.success("Đã đồng bộ điểm số lên Cơ sở dữ liệu của trung tâm!")
                time.sleep(1)
                st.rerun()

with c_btn2:
    current_date = datetime.now().strftime("%d%m%Y")
    file_name = f"Bang_Diem_{class_options[selected_class_id].replace(' ', '_')}_{current_date}.csv"
    st.download_button(
        "Xuất Báo Cáo (CSV)", 
        data=edited_df[display_cols].to_csv(index=False).encode('utf-8-sig'), 
        file_name=file_name, 
        mime="text/csv"
    )