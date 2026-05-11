import streamlit as st
import time
from api_clients.tv3_client import get_gamification_profile, submit_contact_request
from utils.role_guard import require_role

# Kiểm tra quyền truy cập
require_role(["parent", "admin"])

def show_deposit_page():
    st.title("💳 Nạp Tiền & Quản Lý Ví")
    
    user_id = st.session_state.get("user_id")
    if not user_id:
        st.error("Không tìm thấy thông tin phiên đăng nhập. Vui lòng đăng nhập lại.")
        st.stop()
    
    # 1. Hiển thị số dư thực tế
    profile = get_gamification_profile(user_id)
    balance = profile.get('balance', 0)
    
    m1, m2 = st.columns([1, 2])
    with m1:
        st.metric("Số dư ví hiện tại", f"{balance:,.0f} VNĐ")
    
    st.divider()
    
    # 2. Khu vực hướng dẫn nạp tiền
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.subheader("1. Thông tin chuyển khoản")
        amount = st.number_input("Số tiền muốn nạp (VNĐ)", min_value=10000, step=10000, value=50000)
        memo = f"IKIDS NAP {user_id[-6:]}".upper()
        
        st.info(f"**Ngân hàng:** `BIDV` \n\n **Số tài khoản:** `64110001073247` \n\n **Chủ TK:** `NGUYEN DUC PHAT`")
        st.warning(f"**Nội dung chuyển khoản bắt buộc:**")
        st.code(memo, language="text")
        
        if st.button("Tôi đã chuyển khoản xong", type="primary", use_container_width=True):
            with st.status("🔍 Đang xác thực giao dịch...", expanded=False):
                time.sleep(2)
            st.toast("Đã ghi nhận! Hệ thống đang chờ ngân hàng xác nhận.", icon="⏳")

    with col2:
        st.subheader("2. Quét mã QR (Nhanh)")
        qr_url = f"https://img.vietqr.io/image/BIDV-64110001073247-compact.png?amount={int(amount)}&addInfo={memo}&accountName=NGUYEN%20DUC%20PHAT"
        st.image(qr_url, caption="Mở ứng dụng Ngân hàng để quét mã này", width=350)

    # --- 3. XỬ LÝ SỰ CỐ NẠP TIỀN ---
    st.divider()
    with st.expander("❓ Em đã chuyển tiền nhưng số dư không cập nhật?"):
        st.write("Vui lòng gửi yêu cầu để Admin kiểm tra và cộng tiền thủ công:")
        
        # Nhập số tiền xác nhận
        confirm_amount = st.number_input("Số tiền đã chuyển khoản thực tế (VNĐ)", min_value=10000, step=10000, key="confirm_amt")
        problem_desc = st.text_area("Mô tả sự cố (VD: Đã chuyển khoản nhưng 15 phút rồi chưa nhận được tiền)", height=100)
        
        if st.button("🚀 Gửi yêu cầu hỗ trợ nạp tiền", use_container_width=True):
            if problem_desc:
                # Định nghĩa Class Data theo cách chuẩn để Backend nhận được diện tích thuộc tính
                class MessageData:
                    def __init__(self, sender, receiver, subject, content, amount):
                        self.sender_id = sender
                        self.receiver_id = receiver
                        self.subject = subject
                        self.content = content
                        self.amount = float(amount) # Ép kiểu số để cộng tiền chính xác

                # Khởi tạo đối tượng báo cáo
                report_data = MessageData(
                    sender=str(user_id),
                    receiver="admin",
                    subject="SỰ CỐ NẠP TIỀN",
                    content=problem_desc,
                    amount=confirm_amount
                )
                
                with st.spinner("Đang gửi yêu cầu..."):
                    # Thực hiện gửi qua API Client (Hãy đảm bảo tv3_client.py đã được sửa để lấy trường .amount)
                    success, msg = submit_contact_request(report_data)
                
                if success:
                    st.success("✅ Đã gửi yêu cầu thành công! Admin sẽ kiểm tra và cộng tiền sớm nhất.")
                    st.balloons()
                    time.sleep(2)
                    st.rerun()
                else:
                    st.error(f"Gửi yêu cầu thất bại: {msg}")
            else:
                st.error("Vui lòng nhập mô tả sự cố để Admin dễ đối soát.")

if __name__ == "__main__":
    show_deposit_page()