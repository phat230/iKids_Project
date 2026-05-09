import streamlit as st
import time
from api_clients.tv3_client import get_gamification_profile, submit_contact_request
from utils.role_guard import require_role

require_role(["parent", "admin"])

def show_deposit_page():
    st.title("💳 Nạp Tiền & Quản Lý Ví")
    user_id = st.session_state.get("user_id")
    
    # 1. Hiển thị số dư
    profile = get_gamification_profile(user_id)
    balance = profile.get('balance', 0)
    st.metric("Số dư ví hiện tại", f"{balance:,.0f} VNĐ")
    
    st.divider()
    
    col1, col2 = st.columns([1, 1])
    
    # --- PHẦN NẠP TIỀN (GIỮ NGUYÊN LOGIC CŨ) ---
    with col1:
        st.subheader("1. Thông tin chuyển khoản")
        amount = st.number_input("Số tiền nạp (VNĐ)", min_value=10000, step=10000, value=50000)
        memo = f"IKIDS NAP {user_id[-6:]}".upper()
        
        st.info(f"**BIDV:** `64110001073247` \n\n **Chủ TK:** NGUYEN DUC PHAT")
        st.code(memo, language="text")
        
        if st.button("Tôi đã chuyển khoản xong", type="primary", use_container_width=True):
            with st.status("🔍 Đang xác thực giao dịch...", expanded=False):
                time.sleep(2)
            st.toast("Đã ghi nhận! Hệ thống đang chờ ngân hàng xác nhận.", icon="⏳")

    with col2:
        st.subheader("2. Quét mã QR BIDV")
        qr_url = f"https://img.vietqr.io/image/BIDV-64110001073247-compact.png?amount={int(amount)}&addInfo={memo}&accountName=NGUYEN%20DUC%20PHAT"
        st.image(qr_url, width=350)

    # --- 3. PHẦN MỚI: XỬ LÝ KHI KHÔNG NHẬN ĐƯỢC TIỀN (GIAI ĐOẠN 4) ---
    st.divider()
    with st.expander("❓ Em đã chuyển tiền nhưng số dư không cập nhật?"):
        st.write("""
        Thông thường tiền sẽ vào ví sau 1-3 phút. Nếu sau 10 phút vẫn chưa thấy tiền, 
        vui lòng gửi yêu cầu để Admin kiểm tra thủ công:
        """)
        
        problem_desc = st.text_area("Mô tả sự cố (VD: Đã chuyển 50k lúc 10h nhưng chưa thấy tiền)", height=100)
        
        if st.button("Gửi yêu cầu hỗ trợ nạp tiền", use_container_width=True):
            if problem_desc:
                # Gọi hàm từ services.py (đã sửa ở bước trước) để đẩy vào operator_requests
                # Mình giả lập payload message_data
                class MessageData:
                    sender_id = user_id
                    receiver_id = "admin"
                    subject = "SỰ CỐ NẠP TIỀN"
                    content = problem_desc
                
                # Hàm này trong services.py sẽ tự nhận diện từ khóa và đẩy sang TV1
                success, msg = submit_contact_request(MessageData())
                
                if success:
                    st.success("✅ Đã gửi yêu cầu thành công! Admin sẽ kiểm tra và cộng tiền cho em sớm nhất.")
                    st.balloons()
            else:
                st.error("Vui lòng nhập mô tả sự cố để Admin dễ đối soát.")

if __name__ == "__main__":
    show_deposit_page()