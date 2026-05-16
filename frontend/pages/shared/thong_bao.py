import streamlit as st
import requests
import pandas as pd
import os

# 1. CẤU HÌNH TRANG
st.set_page_config(page_title="Hộp Thư & Thông Báo", page_icon="📨", layout="wide")
# ================= HÀM ĐỌC FILE CSS =================
def load_css(file_name):
    """
    Tự động tìm file CSS trong thư mục frontend/CSS/
    file_name: tên file kèm thư mục con, ví dụ 'shared/thong_bao.css'
    """
    # Lấy đường dẫn đến thư mục iKids_Project (gốc)
    # __file__ là đường dẫn của file thong_bao.py hiện tại
    current_dir = os.path.dirname(os.path.abspath(__file__)) # Đang ở frontend/pages/shared
    
    # Tìm đường dẫn đến thư mục CSS (lùi 2 cấp từ pages/shared/ rồi vào CSS/)
    css_root = os.path.abspath(os.path.join(current_dir, "../../CSS"))
    full_path = os.path.join(css_root, file_name)

    if os.path.exists(full_path):
        with open(full_path, "r", encoding="utf-8") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    else:
        # Nếu vẫn lỗi, nó sẽ in ra đường dẫn chính xác mà máy đang tìm để bạn kiểm tra
        st.warning(f"⚠️ Không tìm thấy file CSS tại: {full_path}")

# Tải CSS (Chỉ cần truyền phần đuôi sau thư mục CSS/)
load_css("shared/thong_bao.css")

API_URL = "http://localhost:8000"

# 1. KIỂM TRA ĐĂNG NHẬP
if "token" not in st.session_state:
    st.error("⚠️ Vui lòng đăng nhập để xem thông báo.")
    st.stop()

user_id = st.session_state.get("user_id")
user_role = st.session_state.get("role", "").lower()
user_name = st.session_state.get("user_info", {}).get("name", "Người dùng")

st.title(" Trung Tâm Thông Báo & Hộp Thư")

# =========================
# 2. CẤU HÌNH PHÂN QUYỀN GỬI
# =========================
ROLE_TARGETS = {
    "admin": {"operator": "Nhân viên vận hành", "teacher": "Giáo viên"},
    "operator": {"admin": "Ban Giám Đốc", "teacher": "Giáo viên", "student": "Học sinh", "parent": "Phụ huynh"},
    "teacher": {"operator": "Nhân viên vận hành", "student": "Học sinh", "parent": "Phụ huynh"},
    "student": {"teacher": "Giáo viên", "operator": "Nhân viên vận hành"},
    "parent": {"teacher": "Giáo viên", "operator": "Nhân viên vận hành"}
}

NOTI_TYPES = {
    "message": " Tin nhắn trao đổi",
    "schedule": " Lịch học",
    "finance": " Tài chính & Học phí",
    "request": " Đơn từ & Yêu cầu",
    "system": " Hệ thống"
}

# =========================
# 3. HÀM XỬ LÝ API
# =========================
def fetch_inbox():
    try:
        res = requests.get(f"{API_URL}/api/notifications/receive/{user_id}/{user_role}", timeout=5)
        return res.json() if res.status_code == 200 else []
    except: return []

def fetch_sent():
    try:
        res = requests.get(f"{API_URL}/api/notifications/sent/{user_id}", timeout=5)
        return res.json() if res.status_code == 200 else []
    except: return []

def mark_read(noti_id):
    try: requests.put(f"{API_URL}/api/notifications/{noti_id}/read", timeout=5)
    except: pass

# =========================
# 4. GIAO DIỆN CHÍNH
# =========================
tab_inbox, tab_compose, tab_sent = st.tabs([" Hộp Thư Đến", " Soạn Thông Báo", " Lịch Sử Đã Gửi"])

# --- TAB 1: HỘP THƯ ĐẾN ---
with tab_inbox:
    inbox_data = fetch_inbox()
    
    col_f1, col_f2 = st.columns([2, 1])
    with col_f1:
        filter_type = st.multiselect("Lọc theo loại:", options=list(NOTI_TYPES.keys()), 
                                     format_func=lambda x: NOTI_TYPES[x], default=list(NOTI_TYPES.keys()))
    with col_f2:
        st.write("##")
        if st.button(" Làm Mới", use_container_width=True): st.rerun()

    filtered_data = [n for n in inbox_data if n.get("type") in filter_type]

    if not filtered_data:
        st.info("Hiện tại bạn không có thông báo nào trong mục này.")
    else:
        unread = [n for n in filtered_data if not n.get("is_read")]
        if unread:
            st.toast(f"Bạn có {len(unread)} thông báo chưa đọc!", icon="🔔")

        for noti in filtered_data:
            is_read = noti.get("is_read", False)
            
            with st.container(border=True):
                c1, c2 = st.columns([4, 1])
                with c1:
                    type_label = NOTI_TYPES.get(noti.get('type'), '📨')
                    # Đánh dấu in đậm tiêu đề nếu chưa đọc
                    title_prefix = " " if not is_read else ""
                    st.markdown(f"**{title_prefix}{type_label} | {noti.get('title')}**")
                    st.caption(f"Từ: {noti.get('sender_name')} ({noti.get('sender_role').upper()})")
                with c2:
                    st.caption(f" {noti.get('created_at', '')[:16].replace('T', ' ')}")
                
                with st.expander("Xem chi tiết nội dung"):
                    st.markdown(f"<div class='noti-content'>{noti.get('content')}</div>", unsafe_allow_html=True)
                    if not is_read:
                        if st.button("Đánh dấu đã đọc", key=f"btn_{noti.get('id')}"):
                            mark_read(noti.get('id'))
                            st.rerun()

# --- TAB 2: SOẠN THÔNG BÁO ---
with tab_compose:
    allowed_targets = ROLE_TARGETS.get(user_role, {})
    if not allowed_targets:
        st.error("Vai trò của bạn không có quyền gửi thông báo.")
    else:
        with st.form("compose_form", clear_on_submit=True):
            st.subheader("Gửi thông báo mới")
            col_a, col_b = st.columns(2)
            with col_a:
                target_role = st.selectbox("Gửi đến bộ phận (*):", options=list(allowed_targets.keys()), 
                                           format_func=lambda x: allowed_targets[x])
                noti_type = st.selectbox("Loại thông báo (*):", options=list(NOTI_TYPES.keys()), 
                                         format_func=lambda x: NOTI_TYPES[x])
            with col_b:
                if user_role in ["admin", "operator"]:
                    receiver_id = st.text_input("Mã người nhận cụ thể (Để trống nếu gửi cho tất cả):")
                else:
                    receiver_id = "all"
                    st.info(f"Yêu cầu sẽ được gửi đến toàn bộ {allowed_targets[target_role]}")
                
                title = st.text_input("Tiêu đề (*):")
            
            content = st.text_area("Nội dung chi tiết (*):", height=150)
            
            if st.form_submit_button(" Gửi Ngay", type="primary", use_container_width=True):
                if not title or not content:
                    st.error("Vui lòng điền đầy đủ tiêu đề và nội dung.")
                else:
                    payload = {
                        "sender_id": user_id,
                        "sender_role": user_role,
                        "sender_name": user_name,
                        "receiver_id": receiver_id if receiver_id else "all",
                        "receiver_role": target_role,
                        "type": noti_type,
                        "title": title,
                        "content": content
                    }
                    res = requests.post(f"{API_URL}/api/notifications/send", json=payload)
                    if res.status_code == 200:
                        st.success("Đã gửi thành công!")
                        st.balloons()
                    else:
                        st.error(f"Lỗi gửi: {res.text}")

# --- TAB 3: LỊCH SỬ ĐÃ GỬI ---
with tab_sent:
    sent_data = fetch_sent()
    if not sent_data:
        st.info("Lịch sử gửi của bạn đang trống.")
    else:
        for noti in sent_data:
            with st.container(border=True):
                st.markdown(f"**{noti.get('title')}**")
                st.write(noti.get("content"))
                target_name = ROLE_TARGETS.get(user_role, {}).get(noti.get('receiver_role'), noti.get('receiver_role'))
                st.caption(f"Gửi tới: {target_name} | Lúc: {noti.get('created_at', '')[:16].replace('T', ' ')}")