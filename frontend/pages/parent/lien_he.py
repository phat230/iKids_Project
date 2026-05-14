import streamlit as st
import requests
import time
import os
from datetime import date

API_URL = "http://localhost:8000"

st.set_page_config(page_title="Liên Hệ & Xin Nghỉ", page_icon="✉️")

# ================= HÀM ĐỌC FILE CSS (SỬA LỖI ĐƯỜNG DẪN) =================
def load_css(file_name):
    """
    Tự động tìm file CSS trong thư mục frontend/CSS/
    file_name: tên file kèm thư mục con, ví dụ 'parent/lien_he.css'
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

# Tải CSS làm đẹp cho trang Liên hệ (Chỉ truyền phần sau thư mục CSS/)
load_css("parent/lien_he.css")

st.title("✉️ Liên Hệ & Xin Nghỉ Phép")

# Kiểm tra đăng nhập
if "token" not in st.session_state:
    st.warning("⚠️ Vui lòng đăng nhập để sử dụng chức năng này.")
    st.stop()

tab1, tab2 = st.tabs(["📝 Gửi yêu cầu mới", "🕒 Lịch sử yêu cầu"])

with tab1:
    with st.form("contact_form"):
        loai_yeu_cau = st.selectbox("Loại yêu cầu:", ["Xin nghỉ phép", "Hỏi bài tập", "Góp ý dịch vụ", "Khác"])
        ngay_ap_dung = st.date_input("Ngày áp dụng (nếu xin nghỉ):", date.today())
        noi_dung = st.text_area("Nội dung chi tiết (*):", placeholder="Vui lòng nhập chi tiết yêu cầu, ví dụ: Xin cho cháu nghỉ ốm...")
        
        submit_btn = st.form_submit_button("📤 Gửi Yêu Cầu", type="primary", use_container_width=True)
        
        if submit_btn:
            if not noi_dung.strip():
                st.error("⚠️ Vui lòng nhập nội dung chi tiết!")
            else:
                payload = {
                    "parent_id": st.session_state.get("user_id", "unknown_parent"),
                    "type": loai_yeu_cau,
                    "date": str(ngay_ap_dung),
                    "content": noi_dung,
                    "status": "pending"
                }
                
                try:
                    # Gửi yêu cầu qua API
                    res = requests.post(f"{API_URL}/api/tv3/contact", json=payload)
                    with st.spinner("Đang gửi lên hệ thống..."):
                        time.sleep(1)
                        st.success("✅ Đã gửi yêu cầu thành công! Nhà trường sẽ sớm phản hồi.")
                        st.balloons()
                except Exception as e:
                    st.error("❌ Mất kết nối đến Backend Database.")

with tab2:
    st.subheader("🕒 Lịch sử yêu cầu đã gửi")
    
    try:
        parent_id = st.session_state.get("user_id", "unknown")
        res_history = requests.get(f"{API_URL}/api/tv3/contact/history/{parent_id}")
        
        if res_history.status_code == 200 and res_history.json():
            history_data = res_history.json()
            for item in history_data:
                with st.container(border=True):
                    st.write(f"**Loại:** {item.get('type')} | **Ngày:** {item.get('date')}")
                    st.caption(f"Nội dung: {item.get('content')}")
                    # Hiển thị trạng thái màu sắc
                    status = item.get('status', 'pending')
                    if status == "pending":
                        st.info("Trạng thái: ⏳ Đang xử lý")
                    elif status == "approved":
                        st.success("Trạng thái: ✅ Đã duyệt")
                    else:
                        st.error("Trạng thái: ❌ Từ chối")
        else:
            st.info("Chưa có yêu cầu nào được ghi nhận.")
    except:
        st.info("Chưa có yêu cầu nào được ghi nhận.")