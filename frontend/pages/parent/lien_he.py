import streamlit as st
import requests
import time
from datetime import date

API_URL = "http://localhost:8000"

st.set_page_config(page_title="Liên Hệ & Xin Nghỉ", page_icon="📞")
st.title("📞 Liên Hệ & Xin Nghỉ Phép")

# Kiểm tra đăng nhập
if "token" not in st.session_state:
    st.warning("🔒 Vui lòng đăng nhập để sử dụng chức năng này.")
    st.stop()

tab1, tab2 = st.tabs(["📝 Gửi yêu cầu mới", "🕒 Lịch sử yêu cầu"])

with tab1:
    with st.form("contact_form"):
        loai_yeu_cau = st.selectbox("Loại yêu cầu:", ["Xin nghỉ phép", "Hỏi bài tập", "Góp ý dịch vụ", "Khác"])
        ngay_ap_dung = st.date_input("Ngày áp dụng (nếu xin nghỉ):", date.today())
        noi_dung = st.text_area("Nội dung chi tiết (*):", placeholder="Vui lòng nhập chi tiết yêu cầu, ví dụ: Xin cho cháu nghỉ ốm...")
        
        submit_btn = st.form_submit_button("🚀 Gửi Yêu Cầu", type="primary", use_container_width=True)
        
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
                    # Gửi trực tiếp API bằng requests
                    res = requests.post(f"{API_URL}/api/tv3/contact", json=payload)
                    with st.spinner("Đang gửi lên hệ thống..."):
                        time.sleep(1)
                        st.success("✅ Đã gửi yêu cầu thành công! Nhà trường sẽ sớm phản hồi.")
                        st.balloons()
                except Exception as e:
                    st.error("❌ Mất kết nối đến Backend Database.")

with tab2:
    st.subheader("📋 Lịch sử yêu cầu đã gửi")
    
    try:
        parent_id = st.session_state.get("user_id", "unknown")
        res_history = requests.get(f"{API_URL}/api/tv3/contact/history/{parent_id}")
        
        if res_history.status_code == 200 and res_history.json():
            history_data = res_history.json()
            for item in history_data:
                with st.container(border=True):
                    st.write(f"**Loại:** {item.get('type')} | **Ngày:** {item.get('date')}")
                    st.caption(f"Nội dung: {item.get('content')}")
                    st.info(f"Trạng thái: {item.get('status', 'Đang xử lý')}")
        else:
            st.info("Chưa có yêu cầu nào được ghi nhận.")
    except:
        st.info("Chưa có yêu cầu nào được ghi nhận.")