import streamlit as st
from api_clients.tv3_client import submit_contact, get_contact_history

st.title("📞 Cổng Liên Hệ & Yêu Cầu")
st.write("Gửi tin nhắn cho giáo viên, trung tâm hoặc tạo yêu cầu xin nghỉ học cho bé.")

# Tạm dùng ID mặc định là 2 để test cho Phụ huynh
parent_id = 2 

# Chia làm 2 Tab để giao diện gọn gàng
tab1, tab2 = st.tabs(["✉️ Gửi Yêu Cầu", "🕒 Lịch Sử Yêu Cầu"])

with tab1:
    with st.form("contact_form"):
        # Selectbox cố tình có tùy chọn "Xin nghỉ học" để kích hoạt trigger tự động bên backend
        subject = st.selectbox("Chủ đề", ["Hỏi thăm tình hình học tập", "Xin nghỉ học", "Phản hồi dịch vụ", "Khác"])
        content = st.text_area("Nội dung tin nhắn / Lý do nghỉ (ghi rõ ngày)")
        
        submit = st.form_submit_button("Gửi Yêu Cầu", use_container_width=True)

        if submit:
            success, data = submit_contact(parent_id, 0, subject, content)
            if success:
                st.success("✅ Đã gửi yêu cầu thành công!")
                # Nếu tiêu đề có chữ "nghỉ học", hiện thêm cảnh báo đã báo cho Vận hành
                if "nghỉ học" in subject.lower():
                    st.info("🤖 Hệ thống đã tự động chuyển yêu cầu xin nghỉ đến bộ phận Vận Hành xếp lịch.")
            else:
                st.error("Có lỗi xảy ra, vui lòng thử lại.")

with tab2:
    history = get_contact_history(parent_id)
    if not history:
        st.write("Chưa có lịch sử liên hệ.")
    else:
        for msg in history:
            # Hiển thị dạng thẻ Accordion mở ra đóng lại được
            with st.expander(f"📅 {msg['created_at'][:10]} - {msg['subject']}"):
                st.write(f"**Nội dung:** {msg['content']}")
                status = "Đã xem" if msg['is_read'] else "Chờ xử lý"
                st.caption(f"Trạng thái: {status}")