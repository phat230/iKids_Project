import streamlit as st
import os
from api_clients.tv3_client import get_gamification_profile, deposit_money
from utils.role_guard import require_role

# 4.3: Bảo mật - Chỉ cho phép Phụ huynh và Admin truy cập trang nạp tiền
require_role(["parent", "admin"])

def show_deposit_page():
    st.title("💳 Nạp Tiền & Quản Lý Ví")
    user_id = st.session_state.get("user_id")
    
    if not user_id:
        st.warning("Vui lòng đăng nhập để thực hiện nạp tiền.")
        st.stop()
    
    # 1. Hiển thị số dư hiện tại
    profile = get_gamification_profile(user_id)
    balance = profile.get('balance', 0)
    st.metric("Số dư ví hiện tại", f"{balance:,.0f} VNĐ")
    
    st.divider()
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.subheader("1. Thông tin chuyển khoản")
        amount = st.number_input("Nhập số tiền muốn nạp (VNĐ)", min_value=10000, step=10000, value=50000)
        
        memo = f"IKIDS NAP {user_id[-6:]}"
        
        # Thống nhất tên chủ tài khoản là NGUYEN DUC PHAT
        st.info(f"""
        **🏦 Ngân hàng BIDV**
        - **Số tài khoản:** `64110001073247`
        - **Chủ tài khoản:** NGUYEN DUC PHAT
        """)
        
        st.markdown("**Nội dung chuyển khoản:**")
        st.code(memo, language="text")
        st.caption("⚠️ Lưu ý: Hãy copy đúng nội dung trên để hệ thống tự động cộng tiền.")
        
        if st.button("Tôi đã chuyển khoản xong", type="primary", use_container_width=True):
            with st.spinner("Đang gửi yêu cầu xác nhận..."):
                success, msg = deposit_money(user_id, amount)
                if success:
                    st.success(f"Yêu cầu nạp {amount:,.0f} VNĐ đã được ghi nhận!")
                    st.balloons()
                else:
                    st.error(msg)

    with col2:
        st.subheader("2. Quét mã QR BIDV")
        
        # Cập nhật accountName trong link QR khớp với thông tin bên trái
        bidv_qr_url = f"https://img.vietqr.io/image/BIDV-64110001073247-compact.png?amount={int(amount)}&addInfo={memo}&accountName=NGUYEN%20DUC%20PHAT"
        
        st.image(bidv_qr_url, width=350, caption="Quét mã bằng App Ngân hàng để tự điền thông tin")
        
        st.warning("Nội dung chuyển khoản phải khớp với mã QR phía trên.")

if __name__ == "__main__":
    show_deposit_page()