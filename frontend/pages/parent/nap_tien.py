import streamlit as st
import os
from api_clients.tv3_client import get_gamification_profile, deposit_money
from utils.role_guard import require_role

# 4.3: Bảo mật - Chặn người lạ, chỉ cho phép Phụ huynh và Admin truy cập
require_role(["parent", "admin"])

def show_deposit_page():
    st.title("💳 Nạp Tiền & Quản Lý Ví")
    user_id = st.session_state.get("user_id")
    
    if not user_id:
        st.warning("Vui lòng đăng nhập để thực hiện nạp tiền.")
        st.stop()
    
    # 1. Hiển thị số dư hiện tại từ Backend
    profile = get_gamification_profile(user_id)
    balance = profile.get('balance', 0)
    st.metric("Số dư ví hiện tại", f"{balance:,.0f} VNĐ")
    
    st.divider()
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.subheader("1. Thông tin chuyển khoản")
        # Ô nhập số tiền linh hoạt
        amount = st.number_input("Nhập số tiền muốn nạp (VNĐ)", min_value=10000, step=10000, value=50000)
        
        # Tạo nội dung chuyển khoản tự động dựa trên 6 số cuối ID
        memo = f"IKIDS NAP {user_id[-6:]}".upper()
        
        st.info(f"""
        **🏦 Ngân hàng BIDV**
        - **Số tài khoản:** `64110001073247`
        - **Chủ tài khoản:** NGUYEN DUC PHAT
        """)
        
        st.markdown("**Nội dung chuyển khoản:**")
        st.code(memo, language="text")
        st.caption("⚠️ Lưu ý: Hệ thống dựa vào nội dung trên để tự động cộng tiền.")
        
        # Nút xác nhận gửi yêu cầu (Dành cho TV3 xử lý)
        if st.button("Tôi đã chuyển khoản xong", type="primary", use_container_width=True):
            with st.spinner("Đang đồng bộ với hệ thống ngân hàng..."):
                success, msg = deposit_money(user_id, amount)
                if success:
                    st.success(f"Yêu cầu nạp {amount:,.0f} VNĐ đã được ghi nhận!")
                    st.balloons()
                else:
                    st.error(msg)

    with col2:
        st.subheader("2. Quét mã QR BIDV")
        
        # Tạo link VietQR động theo chuẩn BIDV-64110001073247-compact
        # Sử dụng URL encoding để đảm bảo các khoảng trắng trong tên không làm lỗi link
        account_name_encoded = "NGUYEN%20DUC%20PHAT"
        memo_encoded = memo.replace(" ", "%20")
        
        bidv_qr_url = f"https://img.vietqr.io/image/BIDV-64110001073247-compact.png?amount={int(amount)}&addInfo={memo_encoded}&accountName={account_name_encoded}"
        
        # Hiển thị mã QR
        st.image(bidv_qr_url, width=350, caption="Dùng App Ngân hàng quét mã để tự điền thông tin")
        
        st.warning("Mã QR này chứa thông tin số tiền và nội dung chuyển khoản của em.")

if __name__ == "__main__":
    show_deposit_page()