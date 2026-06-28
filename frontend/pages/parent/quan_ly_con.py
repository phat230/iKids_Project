import streamlit as st
import requests
import pandas as pd
from datetime import date
import time
import os
from io import BytesIO

# ================= CRITICAL: CẤU HÌNH TRANG LUÔN ĐỂ ĐẦU FILE =================
st.set_page_config(page_title="Quản Lý Con Em - iKids", layout="wide")


# ================= CẤU HÌNH BACKEND URL =================
BACKEND_URL = st.session_state.get("api_url", os.getenv("API_URL", "http://localhost:8000"))

API_AUTH = f"{BACKEND_URL}/api/auth"
API_TV3 = f"{BACKEND_URL}/api/tv3"
API_FINANCE = f"{BACKEND_URL}/api/finance"


# ================= HÀM ĐỌC FILE CSS =================
def load_css(file_name):
    """
    Tự động tìm file CSS trong thư mục frontend/CSS/
    file_name: tên file kèm thư mục con, ví dụ 'parent/parent_global.css'
    """
    current_dir = os.path.dirname(os.path.abspath(__file__))
    css_root = os.path.abspath(os.path.join(current_dir, "../../CSS"))
    full_path = os.path.join(css_root, file_name)

    if os.path.exists(full_path):
        with open(full_path, "r", encoding="utf-8") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)


load_css("parent/parent_global.css")


# ================= SESSION =================
lang = st.session_state.get("lang", "vi")
parent_id = st.session_state.get("user_id")
token = st.session_state.get("access_token") or st.session_state.get("token")


# ==========================================
# BỘ TỪ ĐIỂN SONG NGỮ
# ==========================================
CHILD_MGMT_LABELS = {
    "vi": {
        "err_session": "⚠️ Phiên làm việc hết hạn. Vui lòng đăng nhập lại.",
        "title": "⚙️ Quản Lý Hồ Sơ & Phê Duyệt",
        "subtitle": "Tại đây, bạn có thể tạo tài khoản cho bé, quản lý ví tiền và phê duyệt các yêu cầu mua sắm.",
        "parent_account_header": "### 💳 Tài Khoản Phụ Huynh",
        "parent_account_desc": "Hệ thống sẽ khấu trừ trực tiếp vào số dư ví của bạn khi gửi tiền cho con hoặc phê duyệt yêu cầu mua sắm.",
        "lbl_parent_balance": "Số dư ví hiện tại",
        "btn_deposit_now": "💰 Nạp tiền ngay",

        "tab_list": "📋 Danh sách con em",
        "tab_approve": "🛍️ Phê duyệt mua sắm",
        "tab_add": "➕ Tạo tài khoản mới",
        "tab_history": "📜 Lịch sử giao dịch",

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
        "success_transfer": "Đã chuyển tiền cho con thành công!",
        "toast_child_notified_send": "Bé đã nhận được thông báo tiền về!",
        "err_server_comm": "Không thể hoàn tất giao dịch với máy chủ.",
        "success_withdraw": "Đã rút tiền về ví phụ huynh thành công.",
        "toast_child_notified_withdraw": "Đã gửi thông báo rút tiền cho bé.",
        "err_insufficient_child": "Số dư của bé không đủ để rút tiền.",

        "sub_approve_header": "Yêu cầu mua dụng cụ học tập/quà tặng",
        "success_no_requests": "🎉 Không có yêu cầu nào cần xử lý.",
        "lbl_wants_to_buy": "muốn mua:",
        "lbl_prod_price": "Giá tiền:",
        "err_insufficient_parent_approve": "Ví của bạn không đủ số dư",
        "btn_approve": "Duyệt",
        "btn_reject": "Từ chối",
        "success_approve": "Đã duyệt yêu cầu mua hàng.",
        "success_reject": "Đã từ chối yêu cầu mua hàng.",

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
        "err_age_validation": "Độ tuổi hoặc định dạng nhập vào không hợp lệ. Bé nên trong độ tuổi 4-16.",
        "err_connection": "❌ Lỗi kết nối đến máy chủ Backend.",

        "history_title": "📜 Lịch sử giao dịch của phụ huynh và con",
        "history_empty": "Chưa có lịch sử giao dịch.",
        "history_total_records": "Tổng số giao dịch",
        "history_total_amount": "Tổng giá trị",
        "history_group": "Nhóm giao dịch",
        "history_chart": "📊 Biểu đồ lịch sử giao dịch",
        "export_excel": "📥 Xuất Excel lịch sử giao dịch",
        "debug_backend": "Backend đang dùng",
    },
    "en": {
        "err_session": "⚠️ Session expired. Please log in again.",
        "title": "⚙️ Profile Management & Approvals",
        "subtitle": "Manage your children's profiles, allowance wallets, and purchase requests.",
        "parent_account_header": "### 💳 Parent Wallet",
        "parent_account_desc": "Your wallet balance will be deducted when transferring allowance or approving requests.",
        "lbl_parent_balance": "Current Wallet Balance",
        "btn_deposit_now": "💰 Top Up Now",

        "tab_list": "📋 Children Directory",
        "tab_approve": "🛍️ Purchase Requests",
        "tab_add": "➕ Link New Profile",
        "tab_history": "📜 Transaction History",

        "sub_children_list": "Enrolled Children Profiles",
        "info_no_children": "No student accounts are currently linked to your profile.",
        "lbl_child_name": "Child:",
        "lbl_child_email": "Email:",
        "lbl_child_birth": "DOB:",
        "lbl_child_balance": "Child's Wallet",
        "expander_wallet": "💵 Wallet Transactions",
        "input_amount": "Amount (VND)",
        "btn_send_money": "Send Funds",
        "btn_withdraw_money": "Withdraw",
        "warn_invalid_amount": "Please enter a valid amount.",
        "err_insufficient_parent": "Insufficient parent wallet balance",
        "success_transfer": "Successfully transferred to child!",
        "toast_child_notified_send": "Your child has been notified.",
        "err_server_comm": "Transaction failed due to server communication error.",
        "success_withdraw": "Successfully withdrawn to your wallet.",
        "toast_child_notified_withdraw": "Withdrawal notification dispatched.",
        "err_insufficient_child": "The child's balance is insufficient.",

        "sub_approve_header": "School Supplies & Reward Requests",
        "success_no_requests": "🎉 No pending purchase requests.",
        "lbl_wants_to_buy": "wants to purchase:",
        "lbl_prod_price": "Price:",
        "err_insufficient_parent_approve": "Insufficient wallet balance",
        "btn_approve": "Approve",
        "btn_reject": "Reject",
        "success_approve": "Purchase request approved.",
        "success_reject": "Purchase request rejected.",

        "form_add_header": "Register New Profile for Child",
        "input_stu_name": "Child's Full Name (*)",
        "input_stu_email": "Child's Login Email (*)",
        "input_stu_birth": "Child's Date of Birth (*)",
        "input_stu_password": "Access Password (*)",
        "btn_submit_create": "Create & Link Account",
        "warn_empty_fields": "⚠️ Please fill in all required fields.",
        "spinner_creating": "Provisioning student credentials...",
        "success_created": "🎉 Child account created and linked successfully!",
        "err_failed_create": "❌ Registration failed:",
        "err_age_validation": "Invalid age or date format. Child should be 4-16 years old.",
        "err_connection": "❌ Cannot connect to Backend server.",

        "history_title": "📜 Parent and Child Transaction History",
        "history_empty": "No transaction history yet.",
        "history_total_records": "Total transactions",
        "history_total_amount": "Total value",
        "history_group": "Transaction groups",
        "history_chart": "📊 Transaction Charts",
        "export_excel": "📥 Export Excel",
        "debug_backend": "Current backend",
    },
}

L = CHILD_MGMT_LABELS.get(lang, CHILD_MGMT_LABELS["vi"])


# ================= KIỂM TRA PHIÊN =================
st.title(L["title"])
st.write(L["subtitle"])

if not parent_id or not token:
    st.error(L["err_session"])
    st.stop()


headers = {
    "Authorization": f"Bearer {token}",
    "parent-id": str(parent_id),
    "Content-Type": "application/json",
}


# ================= HÀM TIỆN ÍCH =================
def to_float(value, default=0.0):
    try:
        if value is None or value == "":
            return default
        return float(value)
    except Exception:
        return default


def format_money(value):
    return f"{to_float(value):,.0f} VNĐ"


def get_child_id(child):
    return str(child.get("id") or child.get("_id") or "")


def get_child_name(child):
    return (
        child.get("full_name")
        or child.get("name")
        or f"Bé {get_child_id(child)[-4:]}"
    )


def parse_error_response(res):
    try:
        data = res.json()
        detail = data.get("detail", data)

        if isinstance(detail, list):
            return L["err_age_validation"]

        return str(detail)

    except Exception:
        return res.text


def api_get(url, default_value=None, show_error=False, timeout=15):
    try:
        res = requests.get(url, headers=headers, timeout=timeout)

        if res.status_code == 200:
            try:
                return res.json()
            except Exception:
                return default_value

        if show_error:
            st.error(f"API lỗi {res.status_code}: {res.text}")

        return default_value

    except Exception as e:
        if show_error:
            st.error(f"Lỗi kết nối API: {e}")
        return default_value


def api_post(url, payload, timeout=20):
    try:
        return requests.post(
            url,
            json=payload,
            headers=headers,
            timeout=timeout,
        )
    except Exception as e:
        st.error(f"Lỗi kết nối API: {e}")
        return None


# ================= HÀM GỌI API =================
def fetch_parent_profile():
    data = api_get(
        f"{API_TV3}/gamification/profile/{parent_id}",
        default_value={},
        show_error=False,
    )

    return data if isinstance(data, dict) else {}


def fetch_my_children():
    data = api_get(
        f"{API_TV3}/parent/my-children",
        default_value=[],
        show_error=True,
    )

    return data if isinstance(data, list) else []


def fetch_purchase_requests():
    data = api_get(
        f"{API_TV3}/parent/purchase-requests",
        default_value=[],
        show_error=False,
    )

    return data if isinstance(data, list) else []


def fetch_transaction_history():
    data = api_get(
        f"{API_FINANCE}/parent/history",
        default_value=[],
        show_error=False,
    )

    return data if isinstance(data, list) else []


# ================= DEBUG NHẸ =================
with st.expander("🔧 Debug API", expanded=False):
    st.caption(f"{L['debug_backend']}: `{BACKEND_URL}`")
    st.caption(f"Parent ID: `{parent_id}`")
    st.caption(f"API_TV3: `{API_TV3}`")


# ================= HIỂN THỊ SỐ DƯ VÍ PHỤ HUYNH =================
parent_profile = fetch_parent_profile()
parent_balance = to_float(parent_profile.get("balance", 0.0), 0.0)

with st.container(border=True):
    col_wallet_text, col_wallet_metric = st.columns([3, 1])

    with col_wallet_text:
        st.markdown(L["parent_account_header"])
        st.write(L["parent_account_desc"])

    with col_wallet_metric:
        st.metric(
            label=L["lbl_parent_balance"],
            value=format_money(parent_balance),
        )

        if st.button(
            L["btn_deposit_now"],
            use_container_width=True,
            type="primary",
        ):
            st.switch_page("pages/parent/nap_tien.py")

st.write("")


# ================= TABS =================
tab_list, tab_approve, tab_add, tab_history = st.tabs([
    L["tab_list"],
    L["tab_approve"],
    L["tab_add"],
    L["tab_history"],
])


# ==========================================
# TAB 1: DANH SÁCH & QUẢN LÝ VÍ CON
# ==========================================
with tab_list:
    st.subheader(L["sub_children_list"])

    children = fetch_my_children()

    if not children:
        st.info(L["info_no_children"])
    else:
        for child in children:
            child_key_id = get_child_id(child)
            child_name = get_child_name(child)
            child_email = child.get("email", "")
            child_birth = child.get("birth_date") or child.get("dob") or child.get("birthday") or ""
            child_balance = to_float(child.get("balance", 0), 0.0)

            with st.container(border=True):
                col1, col2, col3 = st.columns([2, 2, 2])

                with col1:
                    st.markdown(f"**{L['lbl_child_name']}** {child_name}")
                    st.caption(f"📧 {L['lbl_child_email']} {child_email or '---'}")

                    if child_birth:
                        st.caption(f"📅 {L['lbl_child_birth']} {child_birth}")

                with col2:
                    st.metric(
                        L["lbl_child_balance"],
                        format_money(child_balance),
                    )

                with col3:
                    with st.expander(L["expander_wallet"]):
                        amount = st.number_input(
                            L["input_amount"],
                            min_value=0,
                            step=10000,
                            key=f"amt_{child_key_id}",
                        )

                        c_btn1, c_btn2 = st.columns(2)

                        # --- GỬI TIỀN CHO CON ---
                        if c_btn1.button(
                            L["btn_send_money"],
                            key=f"send_{child_key_id}",
                            use_container_width=True,
                            type="primary",
                        ):
                            if amount <= 0:
                                st.warning(L["warn_invalid_amount"])

                            elif amount > parent_balance:
                                st.error(
                                    f"❌ {L['err_insufficient_parent']} "
                                    f"({L['lbl_parent_balance'].lower()}: {format_money(parent_balance)})."
                                )

                            else:
                                with st.spinner("Đang xử lý..."):
                                    res = api_post(
                                        f"{API_TV3}/parent/transfer-to-child",
                                        {
                                            "child_id": child_key_id,
                                            "amount": amount,
                                        },
                                    )

                                    if res is not None and res.status_code == 200:
                                        data = res.json()

                                        if data.get("status") == "failed":
                                            st.error(data.get("message", L["err_server_comm"]))
                                        else:
                                            st.success(f"✅ {L['success_transfer']} +{format_money(amount)}")
                                            st.toast(L["toast_child_notified_send"])
                                            time.sleep(1)
                                            st.rerun()
                                    else:
                                        detail = parse_error_response(res) if res is not None else L["err_server_comm"]
                                        st.error(f"❌ {detail}")

                        # --- RÚT TIỀN TỪ VÍ CON ---
                        if c_btn2.button(
                            L["btn_withdraw_money"],
                            key=f"withdraw_{child_key_id}",
                            use_container_width=True,
                        ):
                            if amount <= 0:
                                st.warning(L["warn_invalid_amount"])

                            elif amount > child_balance:
                                st.error(f"❌ {L['err_insufficient_child']}")

                            else:
                                with st.spinner("Đang xử lý..."):
                                    res = api_post(
                                        f"{API_TV3}/parent/withdraw-from-child",
                                        {
                                            "child_id": child_key_id,
                                            "amount": amount,
                                        },
                                    )

                                    if res is not None and res.status_code == 200:
                                        data = res.json()

                                        if data.get("status") == "failed":
                                            st.error(data.get("message", L["err_server_comm"]))
                                        else:
                                            st.success(f"✅ {L['success_withdraw']} +{format_money(amount)}")
                                            st.toast(L["toast_child_notified_withdraw"], icon="ℹ️")
                                            time.sleep(1)
                                            st.rerun()
                                    else:
                                        detail = parse_error_response(res) if res is not None else L["err_server_comm"]
                                        st.error(f"❌ {detail}")


# ==========================================
# TAB 2: PHÊ DUYỆT MUA SẮM
# ==========================================
with tab_approve:
    st.subheader(L["sub_approve_header"])

    requests_list = fetch_purchase_requests()

    if not requests_list:
        st.success(L["success_no_requests"])
    else:
        for req in requests_list:
            req_id = str(req.get("id") or req.get("_id") or "")
            price = to_float(req.get("price", 0), 0.0)

            child_name = req.get("child_name") or req.get("student_name") or "Bé"
            product_name = req.get("product_name") or "Sản phẩm"

            with st.container(border=True):
                col_info, col_action = st.columns([3, 1])

                with col_info:
                    st.markdown(
                        f"👤 **{child_name}** {L['lbl_wants_to_buy']} "
                        f"`{product_name}`"
                    )
                    st.markdown(
                        f"💰 {L['lbl_prod_price']} "
                        f":orange[**{format_money(price)}**]"
                    )

                with col_action:
                    if parent_balance < price:
                        st.error(L["err_insufficient_parent_approve"])
                        st.button(
                            L["btn_approve"],
                            key=f"app_{req_id}",
                            type="primary",
                            use_container_width=True,
                            disabled=True,
                        )
                    else:
                        if st.button(
                            L["btn_approve"],
                            key=f"app_{req_id}",
                            type="primary",
                            use_container_width=True,
                        ):
                            res = api_post(
                                f"{API_TV3}/parent/approve-purchase/{req_id}",
                                {"action": "approve"},
                            )

                            if res is not None and res.status_code == 200:
                                st.success(L["success_approve"])
                                time.sleep(0.5)
                                st.rerun()
                            else:
                                detail = parse_error_response(res) if res is not None else L["err_server_comm"]
                                st.error(detail)

                    if st.button(
                        L["btn_reject"],
                        key=f"rej_{req_id}",
                        use_container_width=True,
                    ):
                        res = api_post(
                            f"{API_TV3}/parent/approve-purchase/{req_id}",
                            {"action": "reject"},
                        )

                        if res is not None and res.status_code == 200:
                            st.success(L["success_reject"])
                            time.sleep(0.5)
                            st.rerun()
                        else:
                            detail = parse_error_response(res) if res is not None else L["err_server_comm"]
                            st.error(detail)


# ==========================================
# TAB 3: TẠO TÀI KHOẢN MỚI CHO BÉ & LIÊN KẾT
# ==========================================
with tab_add:
    with st.form("create_student_form"):
        st.subheader(L["form_add_header"])

        stu_name = st.text_input(L["input_stu_name"])
        stu_email = st.text_input(L["input_stu_email"])

        # Giới hạn động: bé từ 4 đến 16 tuổi
        today = date.today()
        min_birth_date = date(today.year - 16, today.month, today.day)
        max_birth_date = date(today.year - 4, today.month, today.day)

        default_birth_date = date(2018, 1, 1)
        if default_birth_date < min_birth_date:
            default_birth_date = min_birth_date
        if default_birth_date > max_birth_date:
            default_birth_date = max_birth_date

        stu_birth = st.date_input(
            L["input_stu_birth"],
            min_value=min_birth_date,
            max_value=max_birth_date,
            value=default_birth_date,
        )

        stu_password = st.text_input(
            L["input_stu_password"],
            type="password",
        )

        st.write("")

        submit_create = st.form_submit_button(
            L["btn_submit_create"],
            use_container_width=True,
            type="primary",
        )

        if submit_create:
            if not stu_name.strip() or not stu_email.strip() or not stu_password:
                st.warning(L["warn_empty_fields"])
            else:
                payload = {
                    "name": stu_name.strip(),
                    "full_name": stu_name.strip(),
                    "email": stu_email.strip().lower(),
                    "password": stu_password,
                    "role": "student",
                    "birth_date": stu_birth.isoformat(),
                    "phone_number": None,
                    "balance": 0,
                    "exp": 0,
                    "rank": "Beginner",
                }

                try:
                    with st.spinner(L["spinner_creating"]):
                        res = requests.post(
                            f"{API_AUTH}/parent/create-student",
                            json=payload,
                            headers=headers,
                            timeout=20,
                        )

                        if res.status_code in [200, 201]:
                            st.success(L["success_created"])
                            st.balloons()
                            time.sleep(1.5)
                            st.rerun()
                        else:
                            err_detail = parse_error_response(res)

                            if lang == "en" and "đã tồn tại" in str(err_detail):
                                err_detail = "This email address is already registered."

                            st.error(f"{L['err_failed_create']} {err_detail}")

                except Exception as e:
                    st.error(f"{L['err_connection']} {e}")


# ==========================================
# TAB 4: LỊCH SỬ GIAO DỊCH
# ==========================================
with tab_history:
    st.subheader(L["history_title"])

    history = fetch_transaction_history()
    df = pd.DataFrame(history)

    if df.empty:
        st.info(L["history_empty"])
    else:
        st.dataframe(df, use_container_width=True, hide_index=True)

        st.divider()

        col1, col2, col3 = st.columns(3)

        total_records = len(df)
        total_amount = 0.0

        for money_col in ["amount", "price", "total_amount"]:
            if money_col in df.columns:
                total_amount += pd.to_numeric(
                    df[money_col],
                    errors="coerce"
                ).fillna(0).sum()

        col1.metric(L["history_total_records"], total_records)
        col2.metric(L["history_total_amount"], format_money(total_amount))

        if "group" in df.columns:
            col3.metric(L["history_group"], df["group"].nunique())

        st.divider()
        st.subheader(L["history_chart"])

        if "group" in df.columns:
            chart_count = df.groupby("group").size().reset_index(name="Số lượng")
            st.bar_chart(chart_count.set_index("group"))

        money_col = None

        for col in ["amount", "price", "total_amount"]:
            if col in df.columns:
                money_col = col
                break

        if money_col and "group" in df.columns:
            df[money_col] = pd.to_numeric(
                df[money_col],
                errors="coerce"
            ).fillna(0)

            chart_money = df.groupby("group")[money_col].sum().reset_index()
            st.bar_chart(chart_money.set_index("group"))

        st.divider()

        output = BytesIO()

        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            df.to_excel(
                writer,
                index=False,
                sheet_name="Lich_su_giao_dich",
            )

        st.download_button(
            L["export_excel"],
            data=output.getvalue(),
            file_name="lich_su_giao_dich_phu_huynh.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
        )