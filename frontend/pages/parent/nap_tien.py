import streamlit as st
import time
import os
from api_clients.tv3_client import get_gamification_profile, submit_contact_request
from utils.role_guard import require_role

# Kiểm tra quyền truy cập
require_role(["parent", "admin"])

# ================= HÀM ĐỌC FILE CSS (SỬA LỖI ĐƯỜNG DẪN) =================
def load_css(file_name):
    """
    Tự động tìm file CSS trong thư mục frontend/CSS/
    file_name: tên file kèm thư mục con, ví dụ 'parent/nap_tien.css'
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

def show_deposit_page():
    # Tải CSS làm đẹp cho trang Nạp Tiền (Chỉ truyền phần sau thư mục CSS/)
    load_css("parent/nap_tien.css")

    st.title("💰 Nạp Tiền & Quản Lý Ví")
    
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
            with st.status("🔄 Đang xác thực giao dịch...", expanded=False):
                time.sleep(2)
            st.toast("Đã ghi nhận! Hệ thống đang chờ ngân hàng xác nhận.", icon="⏳")

    with col2:
        st.subheader("2. Quét mã QR (Nhanh)")
        # Tự động tạo mã QR VietQR kèm số tiền và nội dung
        qr_url = f"https://img.vietqr.io/image/BIDV-64110001073247-compact.png?amount={int(amount)}&addInfo={memo}&accountName=NGUYEN%20DUC%20PHAT"
        st.image(qr_url, caption="Mở ứng dụng Ngân hàng để quét mã này", width=350)

    # --- 3. XỬ LÝ SỰ CỐ NẠP TIỀN ---
    st.divider()
    with st.expander("❓ Bạn đã chuyển tiền nhưng số dư không cập nhật?"):
        st.write("Vui lòng gửi yêu cầu để Admin kiểm tra và cộng tiền thủ công:")
        
        confirm_amount = st.number_input("Số tiền đã chuyển khoản thực tế (VNĐ)", min_value=10000, step=10000, key="confirm_amt")
        problem_desc = st.text_area("Mô tả sự cố (VD: Đã chuyển khoản nhưng 15 phút chưa thấy tiền)", height=100)
        
        if st.button("📨 Gửi yêu cầu hỗ trợ nạp tiền", use_container_width=True):
            if problem_desc:
                class MessageData:
                    def __init__(self, sender, receiver, subject, content, amount):
                        self.sender_id = sender
                        self.receiver_id = receiver
                        self.subject = subject
                        self.content = content
                        self.amount = float(amount)

                report_data = MessageData(
                    sender=str(user_id),
                    receiver="admin",
                    subject="SỰ CỐ NẠP TIỀN",
                    content=problem_desc,
                    amount=confirm_amount
                )
                
                with st.spinner("Đang gửi yêu cầu..."):
                    success, msg = submit_contact_request(report_data)
                
                if success:
                    st.success("✅ Đã gửi yêu cầu thành công! Admin sẽ kiểm tra sớm nhất.")
                    st.balloons()
                    time.sleep(2)
                    st.rerun()
                else:
                    st.error(f"Gửi yêu cầu thất bại: {msg}")
            else:
                st.error("Vui lòng nhập mô tả sự cố.")

if __name__ == "__main__":
    show_deposit_page()