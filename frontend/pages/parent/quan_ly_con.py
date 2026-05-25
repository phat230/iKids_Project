import streamlit as st
import requests
import pandas as pd
from datetime import datetime, date
import time
import os

# ================= CRITICAL: CẤU HÌNH TRANG LUÔN ĐỂ ĐẦU FILE =================
st.set_page_config(page_title="Quản Lý Con Em - iKids", layout="wide")

# Cấu hình URL Backend
API_AUTH = "http://localhost:8000/api/auth"
API_TV3 = "http://localhost:8000/api/tv3"
API_FINANCE = "http://localhost:8000/api/finance"

# ================= HÀM ĐỌC FILE CSS =================
def load_css(file_name):
    """
    Tự động tìm file CSS trong thư mục frontend/CSS/
    file_name: tên file kèm thư mục con, ví dụ 'parent/quan_ly_con.css'
    """
    current_dir = os.path.dirname(os.path.abspath(__file__))
    css_root = os.path.abspath(os.path.join(current_dir, "../../CSS"))
    full_path = os.path.join(css_root, file_name)

    if os.path.exists(full_path):
        with open(full_path, "r", encoding="utf-8") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    else:
        st.warning(f"⚠️ Không tìm thấy file CSS tại: {full_path}")

# Tải CSS làm đẹp
load_css("parent/parent_global.css")

# Lấy cấu hình ngôn ngữ hiện hành từ session_state (Mặc định là "vi")
lang = st.session_state.get("lang", "vi")

# ==========================================
# BỘ TỪ ĐIỂN SONG NGỮ CHI TIẾT CHO QUAN_LY_CON
# ==========================================
CHILD_MGMT_LABELS = {
    "vi": {
        "err_session": "⚠️ Phiên làm việc hết hạn. Vui lòng đăng nhập lại.",
        "title": "⚙️ Quản Lý Hồ Sơ & Phê Duyệt",
        "subtitle": "Tại đây, bạn có thể tạo tài khoản cho bé, quản lý ví tiền và phê duyệt các yêu cầu mua sắm.",
        "parent_account_header": "### 💳 Tài Khoản Phụ Huynh",
        "parent_account_desc": "Hệ thống sẽ khấu trừ trực tiếp vào số dư ví của bạn khi bạn thực hiện gửi tiền cho con em hoặc phê duyệt các yêu cầu mua sắm đồ dùng học tập.",
        "lbl_parent_balance": "Số dư ví hiện tại",
        "btn_deposit_now": "💰 Nạp tiền ngay",
        
        # Tabs
        "tab_list": "📋 Danh sách con em",
        "tab_approve": "🛍️ Phê duyệt mua sắm",
        "tab_add": "➕ Tạo tài khoản mới",
        "tab_history": "📜 Lịch sử giao dịch",
        
        # Tab 1: Danh sách con
        "sub_children_list": "Các con đang theo học",
        "info_no_children": "Bạn chưa liên kết với tài khoản học sinh nào.",
        "lbl_child_name": "Bé:",
        "lbl_child_email": "Email:",
        "lbl_child_birth": "Ngày sinh:",
        "lbl_child_balance": "Ví của con",
        "expander_wallet": "💵 Giao dịch ví của con",
        "input_amount": "Số tiền (VNĐ)",
        "btn_send_money": "Gửi tiền",
        "btn_withdraw_money": "Rút tiền",
        "warn_invalid_amount": "Vui lòng nhập số tiền hợp lệ.",
        "err_insufficient_parent": "Số dư ví phụ huynh không đủ",
        "success_transfer": "Đã chuyển thành công!",
        "toast_child_notified_send": "Bé đã nhận được thông báo tiền về!",
        "err_server_comm": "Không thể hoàn tất giao dịch giao tiếp máy chủ.",
        "success_withdraw": "Đã rút về ví của bạn thành công.",
        "toast_child_notified_withdraw": "Đã gửi thông báo rút tiền cho bé.",
        "err_insufficient_child": "Số dư của bé không đủ để rút tiền mặt.",
        
        # Tab 2: Phê duyệt
        "sub_approve_header": "Yêu cầu mua dụng cụ học tập",
        "success_no_requests": "🎉 Không có yêu cầu nào cần xử lý.",
        "lbl_wants_to_buy": "muốn mua:",
        "lbl_prod_price": "Giá tiền:",
        "err_insufficient_parent_approve": "Ví của bạn không đủ số dư",
        "btn_approve": "Duyệt",
        "btn_reject": "Từ Chối",
        
        # Tab 3: Tạo tài khoản
        "form_add_header": "Đăng ký thêm tài khoản cho bé",
        "input_stu_name": "Họ và tên của bé (*)",
        "input_stu_email": "Email đăng nhập của bé (*)",
        "input_stu_birth": "Ngày tháng năm sinh của bé (*)",
        "input_stu_password": "Mật khẩu truy cập (*)",
        "btn_submit_create": "Tạo & Liên Kết Tài Khoản",
        "warn_empty_fields": "⚠️ Vui lòng điền đầy đủ các trường thông tin có dấu (*).",
        "spinner_creating": "Đang khởi tạo tài khoản học sinh...",
        "success_created": "🎉 Tạo tài khoản và liên kết dữ liệu với bé thành công!",
        "err_failed_create": "❌ Không thể tạo tài khoản:",
        "err_age_validation": "Độ tuổi hoặc định dạng nhập vào không hợp lệ (Bé phải từ 4-16 tuổi).",
        "err_connection": "❌ Lỗi kết nối đến máy chủ Backend. Vui lòng kiểm tra lại trạng thái Uvicorn."
    },
    "en": {
        "err_session": "⚠️ Session expired. Please log in again.",
        "title": "⚙️ Profile Management & Approvals",
        "subtitle": "Manage your children's profiles, handle allowance wallets, and review reward/shopping purchase requests.",
        "parent_account_header": "### 💳 Parent Account Profile",
        "parent_account_desc": "Funds will be directly deducted from your wallet balance when transferring allowance to children or approving school reward purchases.",
        "lbl_parent_balance": "Current Wallet Balance",
        "btn_deposit_now": "💰 Top Up Now",
        
        # Tabs
        "tab_list": "📋 Children Directory",
        "tab_approve": "🛍️ Purchase Requests",
        "tab_add": "➕ Link New Profile",
        "tab_history": "📜 Transaction History",
        
        # Tab 1: Children Directory
        "sub_children_list": "Enrolled Children Profiles",
        "info_no_children": "No student accounts are currently linked to your profile.",
        "lbl_child_name": "Child:",
        "lbl_child_email": "Email:",
        "lbl_child_birth": "DOB:",
        "lbl_child_balance": "Child's Allowance",
        "expander_wallet": "💵 Direct Wallet Transactions",
        "input_amount": "Amount (VND)",
        "btn_send_money": "Send Funds",
        "btn_withdraw_money": "Withdraw",
        "warn_invalid_amount": "Please enter a valid monetary amount.",
        "err_insufficient_parent": "Insufficient parent wallet balance",
        "success_transfer": "Successfully transferred!",
        "toast_child_notified_send": "Your child has been notified of the incoming allowance!",
        "err_server_comm": "Transaction failed. Database server communication error.",
        "success_withdraw": "Successfully withdrawn to your parent wallet.",
        "toast_child_notified_withdraw": "Withdrawal notification dispatched to child's device.",
        "err_insufficient_child": "The child's balance is insufficient for this withdrawal transaction.",
        
        # Tab 2: Approvals
        "sub_approve_header": "School Supplies & Reward Requests",
        "success_no_requests": "🎉 No pending purchase requests require processing.",
        "lbl_wants_to_buy": "wants to purchase:",
        "lbl_prod_price": "Price Value:",
        "err_insufficient_parent_approve": "Your wallet balance is insufficient",
        "btn_approve": "Approve",
        "btn_reject": "Reject",
        
        # Tab 3: Create Profile
        "form_add_header": "Register New Profile for Child",
        "input_stu_name": "Child's Full Name (*)",
        "input_stu_email": "Child's Login Email (*)",
        "input_stu_birth": "Child's Date of Birth (*)",
        "input_stu_password": "Access Password (*)",
        "btn_submit_create": "Create & Link Account",
        "warn_empty_fields": "⚠️ Please fill in all required fields marked with (*).",
        "spinner_creating": "Provisioning student credentials...",
        "success_created": "🎉 Child account created and profile linked successfully!",
        "err_failed_create": "❌ Registration failed:",
        "err_age_validation": "The entered age bounds or format is invalid (Age must be between 4-16).",
        "err_connection": "❌ Cannot connect to Backend server. Please verify that Uvicorn is active."
    }
}

st.title(CHILD_MGMT_LABELS[lang]["title"])
st.write(CHILD_MGMT_LABELS[lang]["subtitle"])

# 1. KIỂM TRA XÁC THỰC PHIÊN LÀM VIỆC
parent_id = st.session_state.get("user_id")
token = st.session_state.get("access_token") or st.session_state.get("token")

if not parent_id or not token:
    st.error(CHILD_MGMT_LABELS[lang]["err_session"])
    st.stop()

headers = {
    "Authorization": f"Bearer {token}", 
    "parent-id": str(parent_id)
}

# --- HÀM HỖ TRỢ GỌI API ---
def fetch_parent_profile():
    try:
        res = requests.get(f"{API_TV3}/gamification/profile/{parent_id}", headers=headers)
        return res.json() if res.status_code == 200 else {}
    except:
        return {}

def fetch_my_children():
    try:
        res = requests.get(f"{API_TV3}/parent/my-children", headers=headers)
        return res.json() if res.status_code == 200 else []
    except:
        return []

def fetch_purchase_requests():
    try:
        res = requests.get(f"{API_TV3}/parent/purchase-requests", headers=headers)
        return res.json() if res.status_code == 200 else []
    except:
        return []
def fetch_transaction_history():
    try:
        res = requests.get(f"{API_FINANCE}/parent/history", headers=headers)
        return res.json() if res.status_code == 200 else []
    except:
        return []

# ================= HIỂN THỊ SỐ DƯ VÍ PHỤ HUYNH VÀ ĐIỀU HƯỚNG NẠP TIỀN =================
parent_profile = fetch_parent_profile()
parent_balance = parent_profile.get('balance', 0.0)

with st.container(border=True):
    col_wallet_text, col_wallet_metric = st.columns([3, 1])
    with col_wallet_text:
        st.markdown(CHILD_MGMT_LABELS[lang]["parent_account_header"])
        st.write(CHILD_MGMT_LABELS[lang]["parent_account_desc"])
    with col_wallet_metric:
        st.metric(label=CHILD_MGMT_LABELS[lang]["lbl_parent_balance"], value=f"{parent_balance:,.0f} VNĐ")
        if st.button(CHILD_MGMT_LABELS[lang]["btn_deposit_now"], use_container_width=True, type="primary"):
            st.switch_page("pages/parent/nap_tien.py")
st.write("")

# --- GIAO DIỆN CÁC TÁC VỤ ---
tab_list, tab_approve, tab_add, tab_history = st.tabs([
    CHILD_MGMT_LABELS[lang]["tab_list"], 
    CHILD_MGMT_LABELS[lang]["tab_approve"], 
    CHILD_MGMT_LABELS[lang]["tab_add"],
    CHILD_MGMT_LABELS[lang]["tab_history"]
])

# ==========================================
# TAB 1: DANH SÁCH & QUẢN LÝ VÍ CON
# ==========================================
with tab_list:
    st.subheader(CHILD_MGMT_LABELS[lang]["sub_children_list"])
    children = fetch_my_children()
    
    if not children:
        st.info(CHILD_MGMT_LABELS[lang]["info_no_children"])
    else:
        for child in children:
            with st.container(border=True):
                col1, col2, col3 = st.columns([2, 2, 2])
                with col1:
                    st.markdown(f"**{CHILD_MGMT_LABELS[lang]['lbl_child_name']}** {child.get('name', 'N/A')}")
                    st.caption(f"📧 {CHILD_MGMT_LABELS[lang]['lbl_child_name'] if lang=='en' else 'Email:'} {child.get('email', '')}")
                    if child.get('birth_date'):
                        st.caption(f"📅 {CHILD_MGMT_LABELS[lang]['lbl_child_birth']} {child.get('birth_date')}")
                with col2:
                    balance = child.get('balance', 0)
                    st.metric(CHILD_MGMT_LABELS[lang]["lbl_child_balance"], f"{balance:,.0f} VNĐ")
                with col3:
                    child_key_id = str(child.get('id') or child.get('_id', ''))
                    
                    with st.expander(CHILD_MGMT_LABELS[lang]["expander_wallet"]):
                        amount = st.number_input(CHILD_MGMT_LABELS[lang]["input_amount"], min_value=0, step=10000, key=f"amt_{child_key_id}")
                        c_btn1, c_btn2 = st.columns(2)
                        
                        # --- HÀNH ĐỘNG GỬI TIỀN CHO CON ---
                        if c_btn1.button(CHILD_MGMT_LABELS[lang]["btn_send_money"], key=f"send_{child_key_id}", use_container_width=True, type="primary"):
                            if amount <= 0:
                                st.warning(CHILD_MGMT_LABELS[lang]["warn_invalid_amount"])
                            elif amount > parent_balance:
                                st.error(f"❌ {CHILD_MGMT_LABELS[lang]['err_insufficient_parent']} ({CHILD_MGMT_LABELS[lang]['lbl_parent_balance'].lower()}: {parent_balance:,.0f} VNĐ).")
                            else:
                                with st.spinner(CHILD_MGMT_LABELS[lang]["spinner_creating"]):
                                    res = requests.post(f"{API_TV3}/parent/transfer-to-child", 
                                                        json={"child_id": child_key_id, "amount": amount}, headers=headers)
                                    if res.status_code == 200:
                                        st.success(f"✅ {CHILD_MGMT_LABELS[lang]['success_transfer']} +{amount:,.0f} VNĐ")
                                        st.toast(CHILD_MGMT_LABELS[lang]["toast_child_notified_send"])
                                        time.sleep(1)
                                        st.rerun()
                                    else:
                                        st.error(f"❌ {CHILD_MGMT_LABELS[lang]['err_server_comm']}")

                        # --- HÀNH ĐỘNG RÚT TIỀN TỪ VÍ CON QUAY VỀ ---
                        if c_btn2.button(CHILD_MGMT_LABELS[lang]["btn_withdraw_money"], key=f"withdraw_{child_key_id}", use_container_width=True):
                            if amount <= 0:
                                st.warning(CHILD_MGMT_LABELS[lang]["warn_invalid_amount"])
                            elif amount > balance:
                                st.error(f"❌ {CHILD_MGMT_LABELS[lang]['err_insufficient_child']}")
                            else:
                                with st.spinner(CHILD_MGMT_LABELS[lang]["spinner_creating"]):
                                    res = requests.post(f"{API_TV3}/parent/withdraw-from-child", 
                                                        json={"child_id": child_key_id, "amount": amount}, headers=headers)
                                    if res.status_code == 200:
                                        st.success(f"✅ {CHILD_MGMT_LABELS[lang]['success_withdraw']} +{amount:,.0f} VNĐ")
                                        st.toast(CHILD_MGMT_LABELS[lang]["toast_child_notified_withdraw"], icon="ℹ️")
                                        time.sleep(1)
                                        st.rerun()
                                    else:
                                        st.error(f"❌ {CHILD_MGMT_LABELS[lang]['err_insufficient_child']}")

# ==========================================
# TAB 2: PHÊ DUYỆT MUA SẮM 
# ==========================================
with tab_approve:
    st.subheader(CHILD_MGMT_LABELS[lang]["sub_approve_header"])
    requests_list = fetch_purchase_requests()
    
    if not requests_list:
        st.success(CHILD_MGMT_LABELS[lang]["success_no_requests"])
    else:
        for req in requests_list:
            req_id = str(req.get('id') or req.get('_id', ''))
            with st.container(border=True):
                col_info, col_action = st.columns([3, 1])
                with col_info:
                    st.markdown(f"👤 **{req.get('child_name')}** {CHILD_MGMT_LABELS[lang]['lbl_wants_to_buy']} `{req.get('product_name')}`")
                    st.markdown(f"💰 {CHILD_MGMT_LABELS[lang]['lbl_prod_price']} :orange[**{req.get('price', 0):,} VNĐ**]")
                with col_action:
                    if parent_balance < req.get('price', 0):
                        st.error(CHILD_MGMT_LABELS[lang]["err_insufficient_parent_approve"])
                        st.button(CHILD_MGMT_LABELS[lang]["btn_approve"], key=f"app_{req_id}", type="primary", use_container_width=True, disabled=True)
                    else:
                        if st.button(CHILD_MGMT_LABELS[lang]["btn_approve"], key=f"app_{req_id}", type="primary", use_container_width=True):
                            requests.post(f"{API_TV3}/parent/approve-purchase/{req_id}", 
                                          json={"action": "approve"}, headers=headers)
                            st.rerun()
                            
                    if st.button(CHILD_MGMT_LABELS[lang]["btn_reject"], key=f"rej_{req_id}", use_container_width=True):
                        requests.post(f"{API_TV3}/parent/approve-purchase/{req_id}", 
                                      json={"action": "reject"}, headers=headers)
                        st.rerun()

# ==========================================
# TAB 3: TẠO TÀI KHOẢN MỚI CHO BÉ & LIÊN KẾT
# ==========================================
with tab_add:
    with st.form("create_student_form"):
        st.subheader(CHILD_MGMT_LABELS[lang]["form_add_header"])
        stu_name = st.text_input(CHILD_MGMT_LABELS[lang]["input_stu_name"])
        stu_email = st.text_input(CHILD_MGMT_LABELS[lang]["input_stu_email"])
        
        stu_birth = st.date_input(
            CHILD_MGMT_LABELS[lang]["input_stu_birth"],
            min_value=date(2010, 1, 1),
            max_value=date.today(),
            value=date(2018, 1, 1)
        )
        
        stu_password = st.text_input(CHILD_MGMT_LABELS[lang]["input_stu_password"], type="password")
        st.write("")
        submit_create = st.form_submit_button(CHILD_MGMT_LABELS[lang]["btn_submit_create"], use_container_width=True, type="primary")
        
        if submit_create:
            if not stu_name.strip() or not stu_email.strip() or not stu_password:
                st.warning(CHILD_MGMT_LABELS[lang]["warn_empty_fields"])
            else:
                # ĐỒNG BỘ PAYLOAD: Đồng nhất Schema gửi lên Backend
                payload = {
                    "name": stu_name.strip(), 
                    "email": stu_email.strip().lower(), 
                    "password": stu_password, 
                    "role": "student",
                    "birth_date": stu_birth.isoformat(),
                    "phone_number": None 
                }
                try:
                    with st.spinner(CHILD_MGMT_LABELS[lang]["spinner_creating"]):
                        res = requests.post(f"{API_AUTH}/parent/create-student", json=payload, headers=headers)
                        
                        if res.status_code == 200:
                            st.success(CHILD_MGMT_LABELS[lang]["success_created"])
                            st.balloons()
                            time.sleep(1.5)
                            st.rerun()
                        else:
                            err_detail = res.json().get('detail', '')
                            # Xử lý bóc tách mảng lỗi Pydantic validation hoặc lỗi trùng email
                            if isinstance(err_detail, list):
                                err_detail = CHILD_MGMT_LABELS[lang]["err_age_validation"]
                            elif lang == "en" and "đã tồn tại" in str(err_detail):
                                err_detail = "This email address is already registered."
                                
                            st.error(f"{CHILD_MGMT_LABELS[lang]['err_failed_create']} {err_detail}")
                except Exception:
                    st.error(CHILD_MGMT_LABELS[lang]["err_connection"])

# ==========================================
# TAB 4: LỊCH SỬ GIAO DỊCH
# ==========================================
with tab_history:
    st.subheader("📜 Lịch sử giao dịch của phụ huynh và con")

    history = fetch_transaction_history()
    df = pd.DataFrame(history)

    if df.empty:
        st.info("Chưa có lịch sử giao dịch.")
    else:
        st.dataframe(df, use_container_width=True)

        st.divider()

        col1, col2, col3 = st.columns(3)

        total_records = len(df)

        total_amount = 0
        if "amount" in df.columns:
            total_amount += pd.to_numeric(df["amount"], errors="coerce").fillna(0).sum()

        if "price" in df.columns:
            total_amount += pd.to_numeric(df["price"], errors="coerce").fillna(0).sum()

        if "total_amount" in df.columns:
            total_amount += pd.to_numeric(df["total_amount"], errors="coerce").fillna(0).sum()

        col1.metric("Tổng số giao dịch", total_records)
        col2.metric("Tổng giá trị", f"{total_amount:,.0f} VNĐ")

        if "group" in df.columns:
            col3.metric("Nhóm giao dịch", df["group"].nunique())

        st.divider()

        st.subheader("📊 Biểu đồ lịch sử giao dịch")

        if "group" in df.columns:
            chart_count = df.groupby("group").size().reset_index(name="Số lượng")
            st.bar_chart(chart_count.set_index("group"))

        money_col = None
        for col in ["amount", "price", "total_amount"]:
            if col in df.columns:
                money_col = col
                break

        if money_col and "group" in df.columns:
            df[money_col] = pd.to_numeric(df[money_col], errors="coerce").fillna(0)
            chart_money = df.groupby("group")[money_col].sum().reset_index()
            st.bar_chart(chart_money.set_index("group"))

        st.divider()

        from io import BytesIO

        output = BytesIO()
        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            df.to_excel(writer, index=False, sheet_name="Lich_su_giao_dich")

        st.download_button(
            "📥 Xuất Excel lịch sử giao dịch",
            data=output.getvalue(),
            file_name="lich_su_giao_dich_phu_huynh.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )