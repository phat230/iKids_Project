import streamlit as st
import requests
import time
import os
from datetime import date

API_URL = "http://localhost:8000"

# ================= CRITICAL: CẤU HÌNH TRANG LUÔN ĐỂ ĐẦU FILE =================
st.set_page_config(page_title="Liên Hệ & Xin Nghỉ")

# ================= HÀM ĐỌC FILE CSS (SỬA LỖI ĐƯỜNG DẪN) =================
def load_css(file_name):
    """
    Tự động tìm file CSS trong thư mục frontend/CSS/
    file_name: tên file kèm thư mục con, ví dụ 'parent/lien_he.css'
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
load_css("parent/lien_he.css")

# Lấy cấu hình ngôn ngữ hiện hành từ session_state (Mặc định là "vi")
lang = st.session_state.get("lang", "vi")

# ==========================================
# BỘ TỪ ĐIỂN SONG NGỮ CHI TIẾT CHO LIEN_HE
# ==========================================
CONTACT_LABELS = {
    "vi": {
        "title": "📩 Liên Hệ & Xin Nghỉ Phép",
        "warn_login": "⚠️ Vui lòng đăng nhập để sử dụng chức năng này.",
        "tab_new": "📝 Gửi Yêu Cầu Mới",
        "tab_history": "📋 Lịch Sử Yêu Cầu",
        
        # Biểu mẫu
        "lbl_type": "Loại yêu cầu:",
        "lbl_date": "Ngày áp dụng (nếu xin nghỉ):",
        "lbl_content": "Nội dung chi tiết (*):",
        "placeholder_content": "Vui lòng nhập chi tiết yêu cầu, ví dụ: Xin cho cháu nghỉ học ngày...",
        "btn_submit": "🚀 Gửi Yêu Cầu",
        "spinner_msg": "Đang gửi lên hệ thống...",
        
        # Thông báo phản hồi
        "err_empty": "⚠️ Vui lòng nhập nội dung chi tiết!",
        "success_msg": "✅ Đã gửi yêu cầu thành công! Nhà trường sẽ sớm phản hồi.",
        "err_connection": "❌ Mất kết nối đến Backend Database.",
        
        # Các phân loại yêu cầu (Dropdown Mapping)
        "req_leave": "Xin nghỉ phép",
        "req_homework": "Hỏi bài tập",
        "req_feedback": "Góp ý dịch vụ",
        "req_other": "Khác",
        
        # Lịch sử yêu cầu
        "sub_history": "📜 Lịch Sử Yêu Cầu Đã Gửi",
        "info_empty": "Chưa có yêu cầu nào được ghi nhận.",
        "lbl_row_type": "Loại:",
        "lbl_row_date": "Ngày:",
        "lbl_row_content": "Nội dung:",
        "status_lbl": "Trạng thái:",
        "status_pending": "Đang xử lý",
        "status_approved": "Đã duyệt",
        "status_rejected": "Từ chối"
    },
    "en": {
        "title": "📩 Contact & Leave Request",
        "warn_login": "⚠️ Please log in to submit contact and leave requests.",
        "tab_new": "📝 Submit New Request",
        "tab_history": "📋 Request History",
        
        # Form inputs
        "lbl_type": "Request Type:",
        "lbl_date": "Effective Date (for leave requests):",
        "lbl_content": "Detailed Content (*):",
        "placeholder_content": "Please enter request details, e.g., Request for child absence on...",
        "btn_submit": "🚀 Submit Request",
        "spinner_msg": "Dispatched to system registry...",
        
        # Feedback messages
        "err_empty": "⚠️ Detailed content field cannot be empty!",
        "success_msg": "✅ Request submitted successfully! The school will respond shortly.",
        "err_connection": "❌ Cannot establish connection to Backend Database.",
        
        # Request Types mapping
        "req_leave": "Leave Request",
        "req_homework": "Homework Inquiry",
        "req_feedback": "Service Feedback",
        "req_other": "Other",
        
        # Request History Layout
        "sub_history": "📜 Dispatched Request Logs",
        "info_empty": "No previous contact logs found.",
        "lbl_row_type": "Type:",
        "lbl_row_date": "Date:",
        "lbl_row_content": "Content:",
        "status_lbl": "Status:",
        "status_pending": "Pending",
        "status_approved": "Approved",
        "status_rejected": "Rejected"
    }
}

st.title(CONTACT_LABELS[lang]["title"])

# Kiểm tra trạng thái đăng nhập
if "token" not in st.session_state:
    st.warning(CONTACT_LABELS[lang]["warn_login"])
    st.stop()

tab1, tab2 = st.tabs([CONTACT_LABELS[lang]["tab_new"], CONTACT_LABELS[lang]["tab_history"]])

with tab1:
    with st.form("contact_form"):
        # Ánh xạ danh sách lựa chọn hiển thị theo i18n nhưng lưu giá trị thô chuẩn sang DB
        type_options = {
            CONTACT_LABELS[lang]["req_leave"]: "Xin nghỉ phép",
            CONTACT_LABELS[lang]["req_homework"]: "Hỏi bài tập",
            CONTACT_LABELS[lang]["req_feedback"]: "Góp ý dịch vụ",
            CONTACT_LABELS[lang]["req_other"]: "Khác"
        }
        
        selected_type_display = st.selectbox(CONTACT_LABELS[lang]["lbl_type"], options=list(type_options.keys()))
        type_raw_val = type_options[selected_type_display]
        
        ngay_ap_dung = st.date_input(CONTACT_LABELS[lang]["lbl_date"], date.today())
        noi_dung = st.text_area(CONTACT_LABELS[lang]["lbl_content"], placeholder=CONTACT_LABELS[lang]["placeholder_content"])
        
        submit_btn = st.form_submit_button(CONTACT_LABELS[lang]["btn_submit"], type="primary", use_container_width=True)
        
        if submit_btn:
            if not noi_dung.strip():
                st.error(CONTACT_LABELS[lang]["err_empty"])
            else:
                payload = {
                    "parent_id": st.session_state.get("user_id", "unknown_parent"),
                    "type": type_raw_val,  # Giữ giá trị Tiếng Việt chuẩn để Backend lọc phân quyền đồng bộ sang TV1
                    "date": str(ngay_ap_dung),
                    "content": noi_dung.strip(),
                    "status": "pending"
                }
                
                try:
                    with st.spinner(CONTACT_LABELS[lang]["spinner_msg"]):
                        res = requests.post(f"{API_URL}/api/tv3/contact", json=payload)
                        if res.status_code in [200, 201]:
                            st.success(CONTACT_LABELS[lang]["success_msg"])
                            st.balloons()
                            time.sleep(1)
                            st.rerun()
                        else:
                            st.error(f"Error code: {res.status_code}")
                except Exception:
                    st.error(CONTACT_LABELS[lang]["err_connection"])

with tab2:
    st.subheader(CONTACT_LABELS[lang]["sub_history"])
    
    # Bản đồ dịch ngược loại yêu cầu thô từ DB sang giao diện
    inverse_type_map = {
        "Xin nghỉ phép": CONTACT_LABELS[lang]["req_leave"],
        "Hỏi bài tập": CONTACT_LABELS[lang]["req_homework"],
        "Góp ý dịch vụ": CONTACT_LABELS[lang]["req_feedback"],
        "Khác": CONTACT_LABELS[lang]["req_other"]
    }
    
    try:
        parent_id = st.session_state.get("user_id", "unknown")
        res_history = requests.get(f"{API_URL}/api/tv3/contact/history/{parent_id}")
        
        if res_history.status_code == 200 and res_history.json():
            history_data = res_history.json()
            for item in history_data:
                with st.container(border=True):
                    # Trích xuất phân loại dịch ngược
                    raw_type = item.get('type', 'Khác')
                    display_type = inverse_type_map.get(raw_type, raw_type)
                    
                    st.write(f"**{CONTACT_LABELS[lang]['lbl_row_type']}** {display_type} | **{CONTACT_LABELS[lang]['lbl_row_date']}** {item.get('date')}")
                    st.markdown(f"**{CONTACT_LABELS[lang]['lbl_row_content']}** {item.get('content')}")
                    
                    # Cấu hình đổi màu nhãn trạng thái đa ngôn ngữ
                    status = item.get('status', 'pending').lower()
                    if status == "pending":
                        st.info(f"⚙️ **{CONTACT_LABELS[lang]['status_lbl']}** {CONTACT_LABELS[lang]['status_pending']}")
                    elif status == "approved" or status == "resolved":
                        st.success(f"✅ **{CONTACT_LABELS[lang]['status_lbl']}** {CONTACT_LABELS[lang]['status_approved']}")
                    else:
                        st.error(f"❌ **{CONTACT_LABELS[lang]['status_lbl']}** {CONTACT_LABELS[lang]['status_rejected']}")
        else:
            st.info(CONTACT_LABELS[lang]["info_empty"])
    except Exception:
        st.info(CONTACT_LABELS[lang]["info_empty"])