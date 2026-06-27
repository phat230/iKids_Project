import streamlit as st
import requests
import os
import time
from datetime import datetime

from utils.role_guard import require_role

# ================= CRITICAL: CẤU HÌNH TRANG LUÔN ĐỂ ĐẦU FILE =================
st.set_page_config(page_title="Học Phí", page_icon="💳", layout="wide")

require_role(["parent", "admin"])

BACKEND_URL = st.session_state.get("api_url", "http://localhost:8000")
API_TV3 = f"{BACKEND_URL}/api/tv3"
API_TUITION = f"{BACKEND_URL}/api/tuition"

lang = st.session_state.get("lang", "vi")
parent_id = st.session_state.get("user_id")
token = st.session_state.get("access_token") or st.session_state.get("token")


# ================= HÀM ĐỌC FILE CSS =================
def load_css(file_name):
    current_dir = os.path.dirname(os.path.abspath(__file__))
    css_root = os.path.abspath(os.path.join(current_dir, "../../CSS"))
    full_path = os.path.join(css_root, file_name)

    if os.path.exists(full_path):
        with open(full_path, "r", encoding="utf-8") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)


load_css("parent/parent_global.css")


TUITION_LABELS = {
    "vi": {
        "title": "💳 Học Phí",
        "subtitle": "Theo dõi hóa đơn học phí, đóng học phí bằng ví phụ huynh và xem lịch sử thanh toán.",
        "err_login": "Vui lòng đăng nhập bằng tài khoản phụ huynh.",
        "wallet": "Số dư ví",
        "pending_amount": "Cần thanh toán",
        "overdue_amount": "Quá hạn",
        "paid_amount": "Đã thanh toán",
        "tab_unpaid": "Chưa đóng",
        "tab_paid": "Đã đóng",
        "tab_history": "Lịch sử thanh toán",
        "tab_all": "Tất cả hóa đơn",
        "filter_status": "Lọc trạng thái",
        "filter_child": "Lọc theo bé",
        "all": "Tất cả",
        "invoice": "Hóa đơn",
        "class": "Lớp",
        "student": "Học sinh",
        "period": "Kỳ học phí",
        "amount": "Số tiền",
        "due_date": "Hạn đóng",
        "status": "Trạng thái",
        "paid_at": "Ngày đóng",
        "payment_method": "Phương thức",
        "balance_after": "Số dư sau thanh toán",
        "btn_pay": "Đóng học phí",
        "btn_refresh": "Làm mới",
        "msg_paid_success": "Đóng học phí thành công!",
        "msg_pay_failed": "Thanh toán thất bại:",
        "info_no_invoice": "Không có hóa đơn nào.",
        "info_no_payment": "Chưa có lịch sử thanh toán.",
        "warn_low_balance": "Số dư ví hiện tại không đủ để thanh toán hóa đơn này.",
        "hint_topup": "Nếu ví không đủ tiền, vui lòng nạp thêm tiền vào ví phụ huynh trước khi đóng học phí.",
        "status_pending": "Chưa đóng",
        "status_paid": "Đã đóng",
        "status_overdue": "Quá hạn",
        "status_cancelled": "Đã hủy",
        "confirm_pay": "Xác nhận thanh toán hóa đơn này?",
        "yes_pay": "Xác nhận đóng",
        "cancel": "Hủy",
    },
    "en": {
        "title": "💳 Tuition",
        "subtitle": "Track tuition invoices, pay by parent wallet, and review payment history.",
        "err_login": "Please log in with a parent account.",
        "wallet": "Wallet Balance",
        "pending_amount": "Pending Amount",
        "overdue_amount": "Overdue",
        "paid_amount": "Paid",
        "tab_unpaid": "Unpaid",
        "tab_paid": "Paid",
        "tab_history": "Payment History",
        "tab_all": "All Invoices",
        "filter_status": "Filter status",
        "filter_child": "Filter by child",
        "all": "All",
        "invoice": "Invoice",
        "class": "Class",
        "student": "Student",
        "period": "Period",
        "amount": "Amount",
        "due_date": "Due date",
        "status": "Status",
        "paid_at": "Paid at",
        "payment_method": "Method",
        "balance_after": "Balance after payment",
        "btn_pay": "Pay Tuition",
        "btn_refresh": "Refresh",
        "msg_paid_success": "Tuition paid successfully!",
        "msg_pay_failed": "Payment failed:",
        "info_no_invoice": "No invoices found.",
        "info_no_payment": "No payment history yet.",
        "warn_low_balance": "Your wallet balance is not enough to pay this invoice.",
        "hint_topup": "If your wallet balance is insufficient, please top up the parent wallet before paying tuition.",
        "status_pending": "Pending",
        "status_paid": "Paid",
        "status_overdue": "Overdue",
        "status_cancelled": "Cancelled",
        "confirm_pay": "Confirm payment for this invoice?",
        "yes_pay": "Confirm Payment",
        "cancel": "Cancel",
    },
}


def get_headers():
    return {
        "Authorization": f"Bearer {token}",
        "parent-id": str(parent_id),
        "Content-Type": "application/json",
    }


def to_float(value, default=0.0):
    try:
        if value is None or value == "":
            return default
        return float(value)
    except Exception:
        return default


def format_money(value):
    return f"{to_float(value):,.0f} VNĐ"


def format_datetime(value):
    if not value:
        return "---"

    value = str(value)

    try:
        dt = datetime.fromisoformat(value.replace("Z", ""))
        return dt.strftime("%d/%m/%Y %H:%M")
    except Exception:
        return value


def status_label(status):
    labels = TUITION_LABELS[lang]

    mapping = {
        "pending": labels["status_pending"],
        "paid": labels["status_paid"],
        "overdue": labels["status_overdue"],
        "cancelled": labels["status_cancelled"],
    }

    return mapping.get(status, status or "---")


def status_color(status):
    if status == "paid":
        return "green"
    if status == "overdue":
        return "red"
    if status == "cancelled":
        return "gray"
    return "orange"


def get_child_name(child):
    return (
        child.get("full_name")
        or child.get("name")
        or f"Bé {str(child.get('id', ''))[-4:]}"
    )


@st.cache_data(ttl=20)
def get_profile_cached(api_tv3, auth_token, pid):
    try:
        headers = {
            "Authorization": f"Bearer {auth_token}",
            "parent-id": str(pid),
        }
        res = requests.get(f"{api_tv3}/gamification/profile/{pid}", headers=headers, timeout=15)
        return res.json() if res.status_code == 200 else {}
    except Exception:
        return {}


@st.cache_data(ttl=20)
def get_children_cached(api_tv3, auth_token, pid):
    try:
        headers = {
            "Authorization": f"Bearer {auth_token}",
            "parent-id": str(pid),
        }
        res = requests.get(f"{api_tv3}/parent/my-children", headers=headers, timeout=15)
        return res.json() if res.status_code == 200 else []
    except Exception:
        return []


@st.cache_data(ttl=20)
def get_summary_cached(api_tuition, auth_token, pid):
    try:
        headers = {
            "Authorization": f"Bearer {auth_token}",
            "parent-id": str(pid),
        }
        res = requests.get(f"{api_tuition}/parent/{pid}/summary", headers=headers, timeout=20)

        if res.status_code == 200:
            data = res.json()
            return data.get("data", data)

        return {}
    except Exception:
        return {}


@st.cache_data(ttl=20)
def get_invoices_cached(api_tuition, auth_token, pid, status=None):
    try:
        headers = {
            "Authorization": f"Bearer {auth_token}",
            "parent-id": str(pid),
        }

        params = {}
        if status:
            params["status"] = status

        res = requests.get(
            f"{api_tuition}/parent/{pid}/invoices",
            headers=headers,
            params=params,
            timeout=20,
        )

        if res.status_code == 200:
            data = res.json()
            return data.get("items", data if isinstance(data, list) else [])

        return []
    except Exception:
        return []


@st.cache_data(ttl=20)
def get_payments_cached(api_tuition, auth_token, pid):
    try:
        headers = {
            "Authorization": f"Bearer {auth_token}",
            "parent-id": str(pid),
        }

        res = requests.get(
            f"{api_tuition}/parent/{pid}/payments",
            headers=headers,
            timeout=20,
        )

        if res.status_code == 200:
            data = res.json()
            return data.get("items", data if isinstance(data, list) else [])

        return []
    except Exception:
        return []


def pay_invoice(invoice_id):
    payload = {
        "invoice_id": str(invoice_id),
        "parent_id": str(parent_id),
    }

    res = requests.post(
        f"{API_TUITION}/invoices/pay",
        json=payload,
        headers=get_headers(),
        timeout=30,
    )

    return res


def render_invoice_card(invoice, balance):
    labels = TUITION_LABELS[lang]

    invoice_id = invoice.get("id") or invoice.get("_id")
    amount = to_float(invoice.get("amount", 0))
    status = invoice.get("status", "pending")

    with st.container(border=True):
        top1, top2, top3 = st.columns([3, 1, 1])

        with top1:
            st.markdown(f"#### {invoice.get('period_label', labels['invoice'])}")
            st.write(f"**{labels['class']}:** {invoice.get('class_name', '---')}")
            st.write(f"**{labels['student']}:** {invoice.get('student_name', invoice.get('student_id', '---'))}")
            st.caption(f"{labels['due_date']}: {invoice.get('due_date', '---')}")

        with top2:
            st.metric(labels["amount"], format_money(amount))

        with top3:
            color = status_color(status)
            st.markdown(f":{color}[**{status_label(status)}**]")

        if status in ["pending", "overdue"]:
            if balance < amount:
                st.warning(labels["warn_low_balance"])
                st.caption(labels["hint_topup"])

            btn_disabled = balance < amount

            if st.button(
                labels["btn_pay"],
                key=f"pay_{invoice_id}",
                type="primary",
                use_container_width=True,
                disabled=btn_disabled,
            ):
                with st.spinner(labels["btn_pay"] + "..."):
                    res = pay_invoice(invoice_id)

                if res.status_code == 200:
                    st.success(labels["msg_paid_success"])
                    st.balloons()
                    st.cache_data.clear()
                    time.sleep(1)
                    st.rerun()
                else:
                    try:
                        detail = res.json().get("detail", res.text)
                    except Exception:
                        detail = res.text

                    st.error(f"{labels['msg_pay_failed']} {detail}")


def render_invoice_list(invoices, balance, child_filter=None):
    labels = TUITION_LABELS[lang]

    filtered = invoices

    if child_filter and child_filter != "__all__":
        filtered = [
            inv for inv in invoices
            if str(inv.get("student_id")) == str(child_filter)
        ]

    if not filtered:
        st.info(labels["info_no_invoice"])
        return

    for invoice in filtered:
        render_invoice_card(invoice, balance)


def render_paid_table(invoices):
    labels = TUITION_LABELS[lang]

    if not invoices:
        st.info(labels["info_no_invoice"])
        return

    rows = []

    for inv in invoices:
        rows.append({
            labels["invoice"]: inv.get("period_label", "---"),
            labels["student"]: inv.get("student_name", inv.get("student_id", "---")),
            labels["class"]: inv.get("class_name", "---"),
            labels["amount"]: format_money(inv.get("amount", 0)),
            labels["status"]: status_label(inv.get("status")),
            labels["paid_at"]: format_datetime(inv.get("paid_at")),
        })

    st.dataframe(rows, use_container_width=True, hide_index=True)


def render_payment_history(payments):
    labels = TUITION_LABELS[lang]

    if not payments:
        st.info(labels["info_no_payment"])
        return

    rows = []

    for p in payments:
        rows.append({
            labels["student"]: p.get("student_id", "---"),
            labels["amount"]: format_money(p.get("amount", 0)),
            labels["payment_method"]: p.get("payment_method", "wallet"),
            labels["balance_after"]: format_money(p.get("balance_after", 0)),
            labels["paid_at"]: format_datetime(p.get("created_at")),
        })

    st.dataframe(rows, use_container_width=True, hide_index=True)


st.title(TUITION_LABELS[lang]["title"])
st.caption(TUITION_LABELS[lang]["subtitle"])

if not parent_id or not token:
    st.error(TUITION_LABELS[lang]["err_login"])
    st.stop()

if st.button(TUITION_LABELS[lang]["btn_refresh"]):
    st.cache_data.clear()
    st.rerun()

profile = get_profile_cached(API_TV3, token, parent_id)
balance = to_float(profile.get("balance", 0))

children = get_children_cached(API_TV3, token, parent_id)
summary = get_summary_cached(API_TUITION, token, parent_id)

pending_invoices = get_invoices_cached(API_TUITION, token, parent_id, status="pending")
overdue_invoices = get_invoices_cached(API_TUITION, token, parent_id, status="overdue")
paid_invoices = get_invoices_cached(API_TUITION, token, parent_id, status="paid")
all_invoices = get_invoices_cached(API_TUITION, token, parent_id)
payments = get_payments_cached(API_TUITION, token, parent_id)

total_pending = to_float(summary.get("total_pending", sum(to_float(i.get("amount")) for i in pending_invoices)))
total_overdue = to_float(summary.get("total_overdue", sum(to_float(i.get("amount")) for i in overdue_invoices)))
total_paid = to_float(summary.get("total_paid", sum(to_float(i.get("amount")) for i in paid_invoices)))

m1, m2, m3, m4 = st.columns(4)
m1.metric(TUITION_LABELS[lang]["wallet"], format_money(balance))
m2.metric(TUITION_LABELS[lang]["pending_amount"], format_money(total_pending))
m3.metric(TUITION_LABELS[lang]["overdue_amount"], format_money(total_overdue))
m4.metric(TUITION_LABELS[lang]["paid_amount"], format_money(total_paid))

st.divider()

child_options = {"__all__": TUITION_LABELS[lang]["all"]}

for child in children:
    if child.get("id"):
        child_options[str(child["id"])] = get_child_name(child)

selected_child = st.selectbox(
    TUITION_LABELS[lang]["filter_child"],
    options=list(child_options.keys()),
    format_func=lambda x: child_options[x],
)

tab_unpaid, tab_paid, tab_history, tab_all = st.tabs([
    TUITION_LABELS[lang]["tab_unpaid"],
    TUITION_LABELS[lang]["tab_paid"],
    TUITION_LABELS[lang]["tab_history"],
    TUITION_LABELS[lang]["tab_all"],
])

with tab_unpaid:
    unpaid = overdue_invoices + pending_invoices

    unpaid = sorted(
        unpaid,
        key=lambda x: (
            0 if x.get("status") == "overdue" else 1,
            str(x.get("due_date", "")),
        ),
    )

    render_invoice_list(unpaid, balance, selected_child)

with tab_paid:
    filtered_paid = paid_invoices

    if selected_child != "__all__":
        filtered_paid = [
            inv for inv in paid_invoices
            if str(inv.get("student_id")) == str(selected_child)
        ]

    render_paid_table(filtered_paid)

with tab_history:
    filtered_payments = payments

    if selected_child != "__all__":
        filtered_payments = [
            p for p in payments
            if str(p.get("student_id")) == str(selected_child)
        ]

    render_payment_history(filtered_payments)

with tab_all:
    status_filter = st.selectbox(
        TUITION_LABELS[lang]["filter_status"],
        options=["__all__", "pending", "overdue", "paid", "cancelled"],
        format_func=lambda x: TUITION_LABELS[lang]["all"] if x == "__all__" else status_label(x),
    )

    filtered_all = all_invoices

    if selected_child != "__all__":
        filtered_all = [
            inv for inv in filtered_all
            if str(inv.get("student_id")) == str(selected_child)
        ]

    if status_filter != "__all__":
        filtered_all = [
            inv for inv in filtered_all
            if inv.get("status") == status_filter
        ]

    render_invoice_list(filtered_all, balance, None)