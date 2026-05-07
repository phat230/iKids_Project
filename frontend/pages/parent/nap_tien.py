import streamlit as st
import pandas as pd
from api_clients.tv3_client import get_gamification_profile, deposit_money

st.title("💳 Quản Lý Tài Chính Gia Đình")
st.write("Nạp tiền vào ví và theo dõi các hoạt động chi tiêu tại iKids.")

parent_id = st.session_state.get("user_id")

if not parent_id:
    st.error("Phiên đăng nhập hết hạn. Vui lòng đăng nhập lại.")
    st.stop()

# --- PHẦN 1: THÔNG TIN SỐ DƯ ---
profile = get_gamification_profile(parent_id)
current_balance = profile.get('balance', 0.0)

col_balance, col_rank = st.columns(2)
with col_balance:
    st.metric(label="Số dư khả dụng", value=f"{current_balance:,.0f} VNĐ")
with col_rank:
    st.metric(label="Hạng thành viên", value=profile.get('rank_level', 'Beginner'))

st.divider()

# --- PHẦN 2: FORM NẠP TIỀN ---
with st.expander("➕ Nạp tiền mới vào tài khoản", expanded=True):
    with st.form("deposit_form"):
        amount = st.number_input("Số tiền muốn nạp (VNĐ)", min_value=10000, step=10000, value=50000)
        method = st.selectbox("Phương thức thanh toán", ["Chuyển khoản Ngân hàng (QR)", "Ví MoMo / ZaloPay", "Thanh toán tại trung tâm"])
        
        submit = st.form_submit_button("Xác Nhận Nạp Tiền", use_container_width=True)
        
        if submit:
            success, msg = deposit_money(parent_id, amount)
            if success:
                st.success(f"🎉 Giao dịch thành công! Đã nạp {amount:,.0f} VNĐ.")
                st.balloons()
                st.rerun()
            else:
                st.error(f"Lỗi: {msg}")

# --- PHẦN 3: LỊCH SỬ GIAO DỊCH ---
st.subheader("📜 Lịch sử giao dịch gần đây")

# Giả lập dữ liệu lịch sử nếu Backend chưa trả về list transactions chi tiết
# Trong đồ án, bạn nên lấy dữ liệu này từ db.purchase_history và db.deposit_history
mock_history = [
    {"Ngày": "2026-05-06 14:20", "Nội dung": "Nạp tiền vào tài khoản", "Số tiền": "+ 50,000", "Trạng thái": "Thành công"},
    {"Ngày": "2026-05-05 09:15", "Nội dung": "Mua Sách Toán Tư Duy Tập 1", "Số tiền": "- 85,000", "Trạng thái": "Hoàn tất"},
    {"Ngày": "2026-05-04 16:45", "Nội dung": "Nạp tiền vào tài khoản", "Số tiền": "+ 100,000", "Trạng thái": "Thành công"},
]

if mock_history:
    df_history = pd.DataFrame(mock_history)
    st.table(df_history) # Dùng st.table để hiển thị danh sách rõ ràng, không thể chỉnh sửa
else:
    st.info("Chưa có lịch sử giao dịch nào được ghi nhận.")

st.caption("ℹ️ Mọi thắc mắc về giao dịch, vui lòng liên hệ bộ phận Chăm sóc khách hàng trong mục 'Liên hệ'.")