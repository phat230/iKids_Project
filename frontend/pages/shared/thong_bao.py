import streamlit as st
import requests
import pandas as pd
import os

# ================= CRITICAL: CẤU HÌNH TRANG LUÔN ĐỂ ĐẦU FILE =================
st.set_page_config(page_title="Hộp Thư & Thông Báo", page_icon="📨", layout="wide")

# ================= HÀM ĐỌC FILE CSS =================
def load_css(file_name):
    """
    Tự động tìm file CSS trong thư mục frontend/CSS/
    file_name: tên file kèm thư mục con, ví dụ 'shared/thong_bao.css'
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
load_css("shared/thong_bao.css")

BACKEND_URL = st.session_state.get("api_url", "http://localhost:8000")

# 1. KIỂM TRA ĐĂNG NHẬP
if "token" not in st.session_state:
    st.error("⚠️ Vui lòng đăng nhập để xem thông báo." if st.session_state.get("lang") == "vi" else "⚠️ Authentication required. Please log in to view notifications.")
    st.stop()

user_id = st.session_state.get("user_id")
user_role = st.session_state.get("role", "").lower()
user_name = st.session_state.get("user_info", {}).get("name", "Người dùng")

# Lấy cấu hình ngôn ngữ hiện hành từ session_state (Mặc định là "vi")
lang = st.session_state.get("lang", "vi")

# ==========================================
# BỘ TỪ ĐIỂN SONG NGỮ CHI TIẾT CHO THONG_BAO
# ==========================================
NOTIF_LABELS = {
    "vi": {
        "title": "📨 Trung Tâm Thông Báo & Hộp Thư",
        "tab_inbox": "📥 Hộp Thư Đến",
        "tab_compose": "📝 Soạn Thông Báo",
        "tab_sent": "📤 Lịch Sử Đã Gửi",
        
        # Tab 1: Hộp thư đến
        "filter_lbl": "Lọc theo loại:",
        "btn_refresh": "🔄 Làm Mới",
        "info_empty_inbox": "Hiện tại bạn không có thông báo nào trong mục này.",
        "toast_unread": "Bạn có {} thông báo chưa đọc!",
        "lbl_from": "Từ:",
        "btn_expand": "Xem chi tiết nội dung",
        "btn_mark_read": "Đánh dấu đã đọc",
        
        # Tab 2: Soạn thông báo
        "err_permission": "❌ Vai trò của bạn không có quyền gửi thông báo.",
        "sub_compose": "Gửi thông báo mới",
        "lbl_target_role": "Gửi đến bộ phận (*):",
        "lbl_noti_type": "Loại thông báo (*):",
        "lbl_receiver_id": "Mã người nhận cụ thể (Để trống nếu gửi cho tất cả):",
        "lbl_receiver_info": "Yêu cầu sẽ được gửi đến toàn bộ",
        "lbl_subject": "Tiêu đề (*):",
        "lbl_content": "Nội dung chi tiết (*):",
        "btn_send": "🚀 Gửi Ngay",
        "err_validation": "❌ Vui lòng điền đầy đủ tiêu đề và nội dung.",
        "success_sent": "🎉 Đã gửi thông báo thành công!",
        "err_sent": "Lỗi gửi:",
        
        # Tab 3: Lịch sử đã gửi
        "info_empty_sent": "Lịch sử gửi của bạn đang trống.",
        "lbl_to": "Gửi tới:",
        "lbl_at": "Lúc:",
        
        # Bộ phận RBAC
        "role_admin": "Ban Giám Đốc",
        "role_operator": "Nhân viên vận hành",
        "role_teacher": "Giáo viên",
        "role_student": "Học sinh",
        "role_parent": "Phụ huynh",
        
        # Phân loại thông báo
        "type_message": "💬 Tin nhắn trao đổi",
        "type_schedule": "📅 Lịch học",
        "type_finance": "💰 Tài chính & Học phí",
        "type_request": "📝 Đơn từ & Yêu cầu",
        "type_system": "⚙️ Hệ thống"
    },
    "en": {
        "title": "📨 Notification Center & Inbox",
        "tab_inbox": "📥 Inbox",
        "tab_compose": "📝 Compose Notification",
        "tab_sent": "📤 Sent History",
        
        # Tab 1: Inbox
        "filter_lbl": "Filter by Type:",
        "btn_refresh": "🔄 Refresh",
        "info_empty_inbox": "Your inbox is currently empty.",
        "toast_unread": "You have {} unread notifications!",
        "lbl_from": "From:",
        "btn_expand": "View detailed content",
        "btn_mark_read": "Mark as read",
        
        # Tab 2: Compose
        "err_permission": "❌ Your current account role does not have authorization to broadcast notifications.",
        "sub_compose": "Broadcast New Notification",
        "lbl_target_role": "Send to Department (*):",
        "lbl_noti_type": "Notification Type (*):",
        "lbl_receiver_id": "Specific Receiver ID (Leave blank to send to all):",
        "lbl_receiver_info": "This request will be broadcasted to all",
        "lbl_subject": "Subject / Title (*):",
        "lbl_content": "Detailed Content (*):",
        "btn_send": "🚀 Send Now",
        "err_validation": "❌ Subject title and body content fields cannot be empty.",
        "success_sent": "🎉 Notification broadcasted successfully!",
        "err_sent": "Dispatch error:",
        
        # Tab 3: Sent History
        "info_empty_sent": "Your sent notification log is currently empty.",
        "lbl_to": "Sent to:",
        "lbl_at": "At:",
        
        # RBAC roles mapping
        "role_admin": "Board of Directors",
        "role_operator": "Operations Staff",
        "role_teacher": "Teachers",
        "role_student": "Students",
        "role_parent": "Parents",
        
        # Notification Types mapping
        "type_message": "💬 Communications",
        "type_schedule": "📅 Schedules & Timetables",
        "type_finance": "💰 Finances & Tuition",
        "type_request": "📝 Applications & Requests",
        "type_system": "⚙️ System Alerts"
    }
}

st.title(NOTIF_LABELS[lang]["title"])

# ==========================================
# 2. CẤU HÌNH PHÂN QUYỀN GỬI (ĐA NGÔN NGỮ HIỂN THỊ)
# ==========================================
ROLE_TARGETS_MAP = {
    "admin": {"operator": NOTIF_LABELS[lang]["role_operator"], "teacher": NOTIF_LABELS[lang]["role_teacher"]},
    "operator": {"admin": NOTIF_LABELS[lang]["role_admin"], "teacher": NOTIF_LABELS[lang]["role_teacher"], "student": NOTIF_LABELS[lang]["role_student"], "parent": NOTIF_LABELS[lang]["role_parent"]},
    "teacher": {"operator": NOTIF_LABELS[lang]["role_operator"], "student": NOTIF_LABELS[lang]["role_student"], "parent": NOTIF_LABELS[lang]["role_parent"]},
    "student": {"teacher": NOTIF_LABELS[lang]["role_teacher"], "operator": NOTIF_LABELS[lang]["role_operator"]},
    "parent": {"teacher": NOTIF_LABELS[lang]["role_teacher"], "operator": NOTIF_LABELS[lang]["role_operator"]}
}

# Ánh xạ từ điển cho các loại thông báo hiển thị mượt mà
NOTI_TYPES_DISPLAY = {
    "message": NOTIF_LABELS[lang]["type_message"],
    "schedule": NOTIF_LABELS[lang]["type_schedule"],
    "finance": NOTIF_LABELS[lang]["type_finance"],
    "request": NOTIF_LABELS[lang]["type_request"],
    "system": NOTIF_LABELS[lang]["type_system"]
}

# Từ điển chuẩn Tiếng Việt cố định để chuyển đổi ngược khi mapping tên phòng từ DB
raw_role_vietnamese = {
    "admin": "Ban Giám Đốc", "operator": "Nhân viên vận hành", "teacher": "Giáo viên", "student": "Học sinh", "parent": "Phụ huynh"
}

# =========================
# 3. HÀM XỬ LÝ API
# =========================
def fetch_inbox():
    try:
        res = requests.get(f"{BACKEND_URL}/api/notifications/receive/{user_id}/{user_role}", timeout=5)
        return res.json() if res.status_code == 200 else []
    except: return []

def fetch_sent():
    try:
        res = requests.get(f"{BACKEND_URL}/api/notifications/sent/{user_id}", timeout=5)
        return res.json() if res.status_code == 200 else []
    except: return []

def mark_read(noti_id):
    try: requests.put(f"{BACKEND_URL}/api/notifications/{noti_id}/read", timeout=5)
    except: pass

# =========================
# 4. GIAO DIỆN CHÍNH RENDER TABS
# =========================
tab_inbox, tab_compose, tab_sent = st.tabs([NOTIF_LABELS[lang]["tab_inbox"], NOTIF_LABELS[lang]["tab_compose"], NOTIF_LABELS[lang]["tab_sent"]])

# --- TAB 1: HỘP THƯ ĐẾN ---
with tab_inbox:
    inbox_data = fetch_inbox()
    
    col_f1, col_f2 = st.columns([2, 1])
    with col_f1:
        filter_type = st.multiselect(NOTIF_LABELS[lang]["filter_lbl"], options=list(NOTI_TYPES_DISPLAY.keys()), 
                                     format_func=lambda x: NOTI_TYPES_DISPLAY[x], default=list(NOTI_TYPES_DISPLAY.keys()))
    with col_f2:
        st.write("##")
        if st.button(NOTIF_LABELS[lang]["btn_refresh"], use_container_width=True): st.rerun()

    filtered_data = [n for n in inbox_data if n.get("type") in filter_type]

    if not filtered_data:
        st.info(NOTIF_LABELS[lang]["info_empty_inbox"])
    else:
        unread = [n for n in filtered_data if not n.get("is_read")]
        if unread:
            st.toast(NOTIF_LABELS[lang]["toast_unread"].format(len(unread)), icon="🔔")

        for noti in filtered_data:
            is_read = noti.get("is_read", False)
            
            with st.container(border=True):
                c1, c2 = st.columns([4, 1])
                with c1:
                    type_label = NOTI_TYPES_DISPLAY.get(noti.get('type'), '📨')
                    title_prefix = "• " if not is_read else ""
                    st.markdown(f"**{title_prefix}{type_label} | {noti.get('title')}**")
                    
                    # Quy đổi hiển thị vai trò người gửi đa ngôn ngữ
                    s_role_raw = noti.get('sender_role', '').lower()
                    s_role_display = NOTIF_LABELS[lang].get(f"role_{s_role_raw}", s_role_raw.upper())
                    st.caption(f"👤 {NOTIF_LABELS[lang]['lbl_from']} {noti.get('sender_name')} ({s_role_display})")
                with c2:
                    raw_time = noti.get('created_at', '')
                    time_display = raw_time[:16].replace('T', ' ') if len(raw_time) >= 16 else "---"
                    st.caption(f"🕒 {time_display}")
                
                with st.expander(NOTIF_LABELS[lang]["btn_expand"]):
                    st.markdown(f"<div class='noti-content'>{noti.get('content')}</div>", unsafe_allow_html=True)
                    if not is_read:
                        if st.button(NOTIF_LABELS[lang]["btn_mark_read"], key=f"btn_{noti.get('id')}"):
                            mark_read(noti.get('id'))
                            st.rerun()

# --- TAB 2: SOẠN THÔNG BÁO ---
with tab_compose:
    allowed_targets = ROLE_TARGETS_MAP.get(user_role, {})
    if not allowed_targets:
        st.error(NOTIF_LABELS[lang]["err_permission"])
    else:
        with st.form("compose_form", clear_on_submit=True):
            st.subheader(NOTIF_LABELS[lang]["sub_compose"])
            col_a, col_b = st.columns(2)
            with col_a:
                target_role = st.selectbox(NOTIF_LABELS[lang]["lbl_target_role"], options=list(allowed_targets.keys()), 
                                           format_func=lambda x: allowed_targets[x])
                noti_type = st.selectbox(NOTIF_LABELS[lang]["lbl_noti_type"], options=list(NOTI_TYPES_DISPLAY.keys()), 
                                         format_func=lambda x: NOTI_TYPES_DISPLAY[x])
            with col_b:
                if user_role in ["admin", "operator"]:
                    receiver_id = st.text_input(NOTIF_LABELS[lang]["lbl_receiver_id"])
                else:
                    receiver_id = "all"
                    st.info(f"ℹ️ {NOTIF_LABELS[lang]['lbl_receiver_info']} {allowed_targets[target_role]}")
                
                title = st.text_input(NOTIF_LABELS[lang]["lbl_subject"])
            
            content = st.text_area(NOTIF_LABELS[lang]["lbl_content"], height=150)
            
            if st.form_submit_button(NOTIF_LABELS[lang]["btn_send"], type="primary", use_container_width=True):
                if not title.strip() or not content.strip():
                    st.error(NOTIF_LABELS[lang]["err_validation"])
                else:
                    payload = {
                        "sender_id": user_id,
                        "sender_role": user_role,
                        "sender_name": user_name,
                        "receiver_id": receiver_id.strip() if receiver_id else "all",
                        "receiver_role": target_role,
                        "type": noti_type,
                        "title": title.strip(),
                        "content": content.strip()
                    }
                    res = requests.post(f"{BACKEND_URL}/api/notifications/send", json=payload)
                    if res.status_code == 200:
                        st.success(NOTIF_LABELS[lang]["success_sent"])
                        st.balloons()
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error(f"❌ {NOTIF_LABELS[lang]['err_sent']} {res.text}")

# --- TAB 3: LỊCH SỬ ĐÃ GỬI ---
with tab_sent:
    sent_data = fetch_sent()
    if not sent_data:
        st.info(NOTIF_LABELS[lang]["info_empty_sent"])
    else:
        for noti in sent_data:
            with st.container(border=True):
                st.markdown(f"**{noti.get('title')}**")
                st.markdown(f"<div class='noti-content'>{noti.get('content')}</div>", unsafe_allow_html=True)
                
                # Trích xuất phân quyền đích đa ngôn ngữ
                r_role_raw = noti.get('receiver_role', '').lower()
                target_name = ROLE_TARGETS_MAP.get(user_role, {}).get(r_role_raw, r_role_raw.upper())
                
                raw_sent_time = noti.get('created_at', '')
                sent_time_display = raw_sent_time[:16].replace('T', ' ') if len(raw_sent_time) >= 16 else "---"
                
                st.caption(f"📩 {NOTIF_LABELS[lang]['lbl_to']} {target_name} | {NOTIF_LABELS[lang]['lbl_at']} {sent_time_display}")