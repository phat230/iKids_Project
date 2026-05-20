import streamlit as st
import pandas as pd
import requests
from io import BytesIO
import altair as alt

API_BASE = "http://127.0.0.1:8000/api/finance"


def get_headers():
    token = st.session_state.get("access_token")
    return {"Authorization": f"Bearer {token}"} if token else {}


def check_permission():
    user = st.session_state.get("user_info", {})
    role = user.get("role")

    if role not in ["admin", "operator"]:
        st.error("Bạn không có quyền truy cập trang này.")
        st.stop()


def export_excel(df, file_name):
    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Bao_cao")
    st.download_button(
        "📥 Xuất Excel",
        data=output.getvalue(),
        file_name=file_name,
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )


def load_wallet_transactions():
    res = requests.get(f"{API_BASE}/wallet-transactions", headers=get_headers())
    if res.status_code == 200:
        return res.json()
    st.error(res.text)
    return []


def load_purchase_transactions():
    res = requests.get(f"{API_BASE}/purchase-transactions", headers=get_headers())
    if res.status_code == 200:
        return res.json()
    st.error(res.text)
    return []


def update_transaction(transaction_id, payload):
    res = requests.put(
        f"{API_BASE}/transactions/{transaction_id}",
        json=payload,
        headers=get_headers()
    )
    return res.status_code == 200


def delete_transaction(transaction_id):
    res = requests.delete(
        f"{API_BASE}/transactions/{transaction_id}",
        headers=get_headers()
    )
    return res.status_code == 200


st.set_page_config(page_title="Quản lý giao dịch tiền", layout="wide")
check_permission()

st.title("💰 Quản lý giao dịch tiền & mua dụng cụ")

tab1, tab2, tab3 = st.tabs([
    "💳 Giao dịch ví phụ huynh",
    "🛒 Mua dụng cụ học tập",
    "📊 Sơ đồ dòng tiền"
])

# ================= TAB 1 =================
with tab1:
    st.subheader("💳 Lịch sử nạp / chuyển / rút tiền")

    data = load_wallet_transactions()
    df = pd.DataFrame(data)

    if not df.empty:
        st.dataframe(df, use_container_width=True)
        export_excel(df, "lich_su_giao_dich_vi.xlsx")

        st.divider()
        st.subheader("✏️ Chỉnh sửa giao dịch")

        selected_id = st.selectbox("Chọn mã giao dịch", df["id"].tolist())

        row = df[df["id"] == selected_id].iloc[0]

        col1, col2, col3 = st.columns(3)

        with col1:
            amount = st.number_input("Số tiền", value=float(row.get("amount", 0)))
        with col2:
            transaction_type = st.selectbox(
                "Loại giao dịch",
                ["nap_tien", "chuyen_cho_con", "rut_tu_con"],
                index=["nap_tien", "chuyen_cho_con", "rut_tu_con"].index(row.get("type", "nap_tien"))
            )
        with col3:
            status = st.selectbox(
                "Trạng thái",
                ["success", "pending", "failed"],
                index=["success", "pending", "failed"].index(row.get("status", "success"))
            )

        note = st.text_area("Ghi chú", value=row.get("note", ""))

        c1, c2 = st.columns(2)

        with c1:
            if st.button("💾 Lưu chỉnh sửa", use_container_width=True):
                ok = update_transaction(selected_id, {
                    "amount": amount,
                    "type": transaction_type,
                    "status": status,
                    "note": note
                })
                if ok:
                    st.success("Đã cập nhật giao dịch.")
                    st.rerun()
                else:
                    st.error("Cập nhật thất bại.")

        with c2:
            if st.button("🗑️ Xóa giao dịch", use_container_width=True):
                ok = delete_transaction(selected_id)
                if ok:
                    st.success("Đã xóa giao dịch.")
                    st.rerun()
                else:
                    st.error("Xóa thất bại.")
    else:
        st.info("Chưa có dữ liệu giao dịch ví.")


# ================= TAB 2 =================
with tab2:
    st.subheader("🛒 Lịch sử mua dụng cụ học tập")

    data = load_purchase_transactions()
    df_buy = pd.DataFrame(data)

    if not df_buy.empty:
        st.dataframe(df_buy, use_container_width=True)
        export_excel(df_buy, "lich_su_mua_dung_cu.xlsx")

        st.divider()
        st.subheader("✏️ Chỉnh sửa đơn mua")

        selected_id = st.selectbox("Chọn mã đơn mua", df_buy["id"].tolist(), key="buy_id")

        row = df_buy[df_buy["id"] == selected_id].iloc[0]

        col1, col2, col3 = st.columns(3)

        with col1:
            item_name = st.text_input("Tên dụng cụ", value=row.get("item_name", ""))
        with col2:
            quantity = st.number_input("Số lượng", value=int(row.get("quantity", 1)), min_value=1)
        with col3:
            total_amount = st.number_input("Tổng tiền", value=float(row.get("total_amount", 0)))

        status = st.selectbox(
            "Trạng thái",
            ["success", "pending", "cancelled"],
            index=["success", "pending", "cancelled"].index(row.get("status", "success")),
            key="buy_status"
        )

        if st.button("💾 Cập nhật đơn mua"):
            ok = update_transaction(selected_id, {
                "item_name": item_name,
                "quantity": quantity,
                "total_amount": total_amount,
                "status": status
            })
            if ok:
                st.success("Đã cập nhật đơn mua.")
                st.rerun()
            else:
                st.error("Cập nhật thất bại.")
    else:
        st.info("Chưa có dữ liệu mua dụng cụ.")


# ================= TAB 3 =================
with tab3:
    st.subheader("📊 Sơ đồ dòng tiền")

    wallet_df = pd.DataFrame(load_wallet_transactions())
    buy_df = pd.DataFrame(load_purchase_transactions())

    col1, col2, col3 = st.columns(3)

    total_wallet = wallet_df["amount"].sum() if not wallet_df.empty and "amount" in wallet_df else 0
    total_buy = buy_df["total_amount"].sum() if not buy_df.empty and "total_amount" in buy_df else 0
    total_all = total_wallet + total_buy

    col1.metric("Tổng giao dịch ví", f"{total_wallet:,.0f} VNĐ")
    col2.metric("Tổng mua dụng cụ", f"{total_buy:,.0f} VNĐ")
    col3.metric("Tổng dòng tiền", f"{total_all:,.0f} VNĐ")

    st.divider()

    chart_data = pd.DataFrame({
        "Nhóm": ["Giao dịch ví", "Mua dụng cụ"],
        "Số tiền": [total_wallet, total_buy]
    })

    chart = alt.Chart(chart_data).mark_bar().encode(
        x="Nhóm",
        y="Số tiền",
        tooltip=["Nhóm", "Số tiền"]
    )

    st.altair_chart(chart, use_container_width=True)

    st.markdown("### 🔁 Luồng giao dịch")
    st.code("""
Phụ huynh
   ├── Nạp tiền vào ví
   ├── Chuyển tiền cho con
   ├── Rút tiền từ tài khoản con
   └── Mua dụng cụ học tập

Học sinh
   └── Mua dụng cụ học tập

Operator/Admin
   ├── Xem lịch sử
   ├── Sửa giao dịch
   ├── Xóa giao dịch
   └── Xuất báo cáo Excel
""")