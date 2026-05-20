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
    current_dir = os.path.dirname(os.path.abspath(__file__))
    css_root = os.path.abspath(os.path.join(current_dir, "../../CSS"))
    full_path = os.path.join(css_root, file_name)

    if os.path.exists(full_path):
        with open(full_path, "r", encoding="utf-8") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    else:
        st.warning(f"⚠️ Không tìm thấy file CSS tại: {full_path}")

def show_deposit_page():
    # Tải CSS làm đẹp cho trang Nạp Tiền
    load_css("parent/parent_global.css")

    # Lấy cấu hình ngôn ngữ hiện hành từ session_state (Mặc định là "vi")
    lang = st.session_state.get("lang", "vi")

    # ==========================================
    # BỘ TỪ ĐIỂN SONG NGỮ CHI TIẾT CHO NAP_TIEN
    # ==========================================
    DEPOSIT_LABELS = {
        "vi": {
            "title": "💳 Nạp Tiền & Quản Lý Ví",
            "err_session": "❌ Không tìm thấy thông tin phiên đăng nhập. Vui lòng đăng nhập lại.",
            "lbl_balance": "Số dư ví hiện tại",
            "sub_bank_info": "1. Thông tin chuyển khoản",
            "input_amount": "Số tiền muốn nạp (VNĐ)",
            "bank_details": "**Ngân hàng:** `BIDV` \n\n **Số tài khoản:** `64110001073247` \n\n **Chủ TK:** `NGUYEN DUC PHAT`",
            "warn_memo": "**Nội dung chuyển khoản bắt buộc:**",
            "btn_done": "Tôi đã chuyển khoản xong",
            "status_verifying": "Đang xác thực giao dịch...",
            "toast_logged": "Đã ghi nhận! Hệ thống đang chờ ngân hàng xác nhận.",
            "qr_title": "2. Quét mã QR (Nhanh)",
            "qr_caption": "Mở ứng dụng Ngân hàng để quét mã này",
            
            # Xử lý sự cố
            "expander_title": "❓ Bạn đã chuyển tiền nhưng số dư không cập nhật?",
            "expander_desc": "Vui lòng gửi yêu cầu để Admin kiểm tra và cộng tiền thủ công:",
            "input_confirm_amount": "Số tiền đã chuyển khoản thực tế (VNĐ)",
            "input_desc": "Mô tả sự cố (VD: Đã chuyển khoản nhưng 15 phút chưa thấy tiền)",
            "placeholder_desc": "Vui lòng nhập chi tiết tại đây...",
            "btn_submit_report": "💥 Gửi Yêu Cầu Hỗ Trợ Nạp Tiền",
            "spinner_sending": "Đang gửi yêu cầu...",
            "success_report": "✅ Đã gửi yêu cầu thành công! Admin sẽ kiểm tra sớm nhất.",
            "err_failed_report": "Gửi yêu cầu thất bại:",
            "err_empty_desc": "⚠️ Vui lòng nhập mô tả sự cố."
        },
        "en": {
            "title": "💳 Wallet Top-up & Management",
            "err_session": "❌ Session credentials not found. Please log in again.",
            "lbl_balance": "Current Wallet Balance",
            "sub_bank_info": "1. Bank Transfer Information",
            "input_amount": "Deposit Amount (VND)",
            "bank_details": "**Bank Name:** `BIDV` \n\n **Account Number:** `64110001073247` \n\n **Account Holder:** `NGUYEN DUC PHAT`",
            "warn_memo": "**Mandatory Transfer Content Description:**",
            "btn_done": "I Have Completed the Transfer",
            "status_verifying": "Verifying transaction streams...",
            "toast_logged": "Transaction recorded! Awaiting bank confirmation.",
            "qr_title": "2. Scan QR Code (Instant)",
            "qr_caption": "Open your Mobile Banking app to scan this QR code",
            
            # Issue handling
            "expander_title": "❓ Transferred money but balance did not update?",
            "expander_desc": "Please submit a support ticket for an Administrator to verify and manually credit your account:",
            "input_confirm_amount": "Actual Transferred Amount (VND)",
            "input_desc": "Issue Description (e.g., Transferred but balance not updated after 15 minutes)",
            "placeholder_desc": "Please enter specific details here...",
            "btn_submit_report": "💥 Submit Deposit Support Ticket",
            "spinner_sending": "Submitting support ticket...",
            "success_report": "✅ Ticket submitted successfully! An Admin will review it shortly.",
            "err_failed_report": "Failed to submit ticket:",
            "err_empty_desc": "⚠️ Issue description field cannot be empty."
        }
    }

    st.title(DEPOSIT_LABELS[lang]["title"])
    
    user_id = st.session_state.get("user_id")
    if not user_id:
        st.error(DEPOSIT_LABELS[lang]["err_session"])
        st.stop()
    
    # 1. Hiển thị số dư thực tế
    profile = get_gamification_profile(user_id)
    balance = profile.get('balance', 0)
    
    m1, m2 = st.columns([1, 2])
    with m1:
        st.metric(DEPOSIT_LABELS[lang]["lbl_balance"], f"{balance:,.0f} VNĐ")
    
    st.divider()
    
    # 2. Khu vực hướng dẫn nạp tiền
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.subheader(DEPOSIT_LABELS[lang]["sub_bank_info"])
        amount = st.number_input(DEPOSIT_LABELS[lang]["input_amount"], min_value=10000, step=10000, value=50000)
        memo = f"IKIDS NAP {user_id[-6:]}".upper()
        
        st.info(DEPOSIT_LABELS[lang]["bank_details"])
        st.warning(DEPOSIT_LABELS[lang]["warn_memo"])
        st.code(memo, language="text")
        
        if st.button(DEPOSIT_LABELS[lang]["btn_done"], type="primary", use_container_width=True):
            with st.status(DEPOSIT_LABELS[lang]["status_verifying"], expanded=False):
                time.sleep(2)
            st.toast(DEPOSIT_LABELS[lang]["toast_logged"])

    with col2:
        st.subheader(DEPOSIT_LABELS[lang]["qr_title"])
        # Tự động tạo mã QR VietQR kèm số tiền và nội dung nội bộ
        qr_url = f"https://img.vietqr.io/image/BIDV-64110001073247-compact.png?amount={int(amount)}&addInfo={memo}&accountName=NGUYEN%20DUC%20PHAT"
        st.image(qr_url, caption=DEPOSIT_LABELS[lang]["qr_caption"], width=350)

    # --- 3. XỬ LÝ SỰ CỐ NẠP TIỀN ---
    st.divider()
    with st.expander(DEPOSIT_LABELS[lang]["expander_title"]):
        st.write(DEPOSIT_LABELS[lang]["expander_desc"])
        
        confirm_amount = st.number_input(DEPOSIT_LABELS[lang]["input_confirm_amount"], min_value=10000, step=10000, key="confirm_amt")
        problem_desc = st.text_area(DEPOSIT_LABELS[lang]["input_desc"], placeholder=DEPOSIT_LABELS[lang]["placeholder_desc"], height=100)
        
        if st.button(DEPOSIT_LABELS[lang]["btn_submit_report"], use_container_width=True):
            if problem_desc.strip():
                class MessageData:
                    def __init__(self, sender, receiver, subject, content, amount):
                        self.sender_id = sender
                        self.receiver_id = receiver
                        self.subject = subject
                        self.content = content
                        self.amount = float(amount)

                # Lưu subject cố định Tiếng Việt để webhook/API Admin phía sau xử lý phân rã tự động
                report_data = MessageData(
                    sender=str(user_id),
                    receiver="admin",
                    subject="SỰ CỐ NẠP TIỀN",
                    content=problem_desc.strip(),
                    amount=confirm_amount
                )
                
                with st.spinner(DEPOSIT_LABELS[lang]["spinner_sending"]):
                    success, msg = submit_contact_request(report_data)
                
                if success:
                    st.success(DEPOSIT_LABELS[lang]["success_report"])
                    st.balloons()
                    time.sleep(1.5)
                    st.rerun()
                else:
                    st.error(f"❌ {DEPOSIT_LABELS[lang]['err_failed_report']} {msg}")
            else:
                st.error(DEPOSIT_LABELS[lang]["err_empty_desc"])

if __name__ == "__main__":
    show_deposit_page()