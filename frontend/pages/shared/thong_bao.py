import streamlit as st
import requests
from datetime import datetime

st.set_page_config(page_title="Hộp Thư & Thông Báo", page_icon="🔔", layout="wide")

API_URL = "http://localhost:8000"

# =========================
# 1. KIỂM TRA ĐĂNG NHẬP
# =========================
if "token" not in st.session_state or "role" not in st.session_state:
    st.error("🔒 Vui lòng đăng nhập để xem thông báo.")
    st.stop()

user_id = st.session_state.get("user_id")
user_role = st.session_state.get("role")
user_name = st.session_state.get("user_info", {}).get("name", "Người dùng")

st.title("🔔 Trung Tâm Thông Báo & Hộp Thư")
st.write("Tại đây bạn có thể kiểm tra các thông báo mới nhất và gửi tin nhắn đến các bộ phận khác.")

# =========================
# 2. CẤU HÌNH QUYỀN GỬI THEO ROLE
# =========================
# Định nghĩa Role đang đăng nhập được phép gửi thông báo cho ai
ROLE_TARGETS = {
    "admin": {"operator": "Nhân viên vận hành", "teacher": "Giáo viên"},
    "operator": {"admin": "Ban Giám Đốc", "teacher": "Giáo viên", "student": "Học sinh", "parent": "Phụ huynh"},
    "teacher": {"operator": "Nhân viên vận hành", "student": "Học sinh", "parent": "Phụ huynh"},
    "student": {"teacher": "Giáo viên", "operator": "Nhân viên vận hành"},
    "parent": {"teacher": "Giáo viên", "operator": "Nhân viên vận hành"}
}

NOTI_TYPES = {
    "message": "💬 Tin nhắn trao đổi",
    "schedule": "📅 Về Lịch học",
    "finance": "💰 Tài chính / Học phí",
    "request": "📝 Đơn từ / Yêu cầu",
    "system": "⚙️ Hệ thống"
}

# =========================
# 3. CÁC HÀM GỌI API
# =========================
def fetch_inbox():
    try:
        res = requests.get(f"{API_URL}/api/notifications/receive/{user_id}/{user_role}", timeout=5)
        return res.json() if res.status_code == 200 else []
    except:
        return []

def fetch_sent():
    try:
        res = requests.get(f"{API_URL}/api/notifications/sent/{user_id}", timeout=5)
        return res.json() if res.status_code == 200 else []
    except:
        return []

def mark_read(noti_id):
    try:
        requests.put(f"{API_URL}/api/notifications/{noti_id}/read", timeout=5)
    except:
        pass

# =========================
# 4. GIAO DIỆN CHÍNH (TABS)
# =========================
tab_inbox, tab_compose, tab_sent = st.tabs(["📥 Hộp thư đến", "✍️ Soạn thông báo", "📤 Đã gửi"])

# --- TAB 1: HỘP THƯ ĐẾN ---
with tab_inbox:
    st.subheader("📬 Các thông báo bạn nhận được")
    if st.button("🔄 Làm mới hộp thư"):
        st.rerun()
        
    inbox_data = fetch_inbox()
    
    if not inbox_data:
        st.info("Trống! Bạn không có thông báo nào mới.")
    else:
        unread_count = sum(1 for n in inbox_data if not n.get("is_read"))
        if unread_count > 0:
            st.warning(f"Bạn có {unread_count} thông báo chưa đọc!")
            
        for noti in inbox_data:
            noti_id = noti.get("id")
            is_read = noti.get("is_read", False)
            icon = "⚪" if is_read else "🔴"
            
            # Khung hiển thị từng thông báo
            with st.expander(f"{icon} [{NOTI_TYPES.get(noti.get('type'), 'Thông báo')}] {noti.get('title')} (Từ: {noti.get('sender_name')})"):
                st.write(f"**Nội dung:**\n{noti.get('content')}")
                st.caption(f"📅 Nhận lúc: {noti.get('created_at', '')[:16].replace('T', ' ')} | 👤 Gửi từ: {noti.get('sender_role').upper()}")
                
                # Nút đánh dấu đã đọc
                if not is_read:
                    if st.button("✅ Đánh dấu đã đọc", key=f"read_{noti_id}"):
                        mark_read(noti_id)
                        st.rerun()

# --- TAB 2: SOẠN THÔNG BÁO ---
with tab_compose:
    st.subheader("✍️ Soạn thông báo / Tin nhắn mới")
    
    allowed_targets = ROLE_TARGETS.get(user_role, {})
    if not allowed_targets:
        st.error("Vai trò của bạn không được cấp quyền gửi thông báo.")
    else:
        with st.form("compose_form", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                # Chọn nhóm người nhận dựa trên quyền
                target_role_key = st.selectbox(
                    "Gửi đến bộ phận (*):", 
                    options=list(allowed_targets.keys()), 
                    format_func=lambda x: allowed_targets[x]
                )
                
                noti_type_key = st.selectbox(
                    "Chủ đề / Loại thông báo (*):", 
                    options=list(NOTI_TYPES.keys()), 
                    format_func=lambda x: NOTI_TYPES[x]
                )
            
            with col2:
                receiver_id_input = st.text_input(
                    "Mã người nhận (Tùy chọn):", 
                    placeholder="Để trống nếu muốn gửi chung cho tất cả"
                )
                
                title = st.text_input("Tiêu đề (*):", placeholder="Nhập tóm tắt vấn đề...")
                
            content = st.text_area("Nội dung thông báo (*):", height=150)
            
            if st.form_submit_button("🚀 Gửi Thông Báo", type="primary"):
                if not title or not content:
                    st.error("⚠️ Vui lòng nhập đầy đủ Tiêu đề và Nội dung!")
                else:
                    payload = {
                        "sender_id": user_id,
                        "sender_role": user_role,
                        "sender_name": user_name,
                        "receiver_id": receiver_id_input.strip() if receiver_id_input.strip() else "all",
                        "receiver_role": target_role_key,
                        "type": noti_type_key,
                        "title": title,
                        "content": content
                    }
                    
                    try:
                        res = requests.post(f"{API_URL}/api/notifications/send", json=payload)
                        if res.status_code in [200, 201]:
                            st.success("✅ Đã gửi thông báo thành công!")
                            st.balloons()
                        else:
                            st.error(f"❌ Lỗi: {res.text}")
                    except Exception as e:
                        st.error(f"Lỗi kết nối Server: {e}")

# --- TAB 3: LỊCH SỬ ĐÃ GỬI ---
with tab_sent:
    st.subheader("📤 Lịch sử thông báo bạn đã gửi đi")
    sent_data = fetch_sent()
    
    if not sent_data:
        st.info("Bạn chưa gửi thông báo nào.")
    else:
        for noti in sent_data:
            receiver = "Tất cả" if noti.get("receiver_id") == "all" else f"Mã ID: {noti.get('receiver_id')}"
            with st.container(border=True):
                st.markdown(f"**{noti.get('title')}**")
                st.write(noti.get("content"))
                st.caption(f"Gửi tới: {noti.get('receiver_role').upper()} ({receiver}) | 🕒 Lúc: {noti.get('created_at', '')[:16].replace('T', ' ')}")