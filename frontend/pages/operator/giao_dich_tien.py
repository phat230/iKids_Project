import streamlit as st
import pandas as pd
import requests
from io import BytesIO
import altair as alt

# ================= CRITICAL: CẤU HÌNH TRANG LUÔN ĐỂ ĐẦU FILE =================
st.set_page_config(page_title="Quản lý giao dịch tiền", layout="wide")

# ĐÃ SỬA: Lấy BACKEND_URL chung từ session_state thay vì ghi chết 127.0.0.1
BACKEND_URL = st.session_state.get("api_url", "http://localhost:8000")
API_BASE = f"{BACKEND_URL}/api/finance"

def get_headers():
    token = st.session_state.get("access_token") or st.session_state.get("token")
    return {"Authorization": f"Bearer {token}"} if token else {}

def check_permission():
    user = st.session_state.get("user_info", {})
    role = user.get("role") or st.session_state.get("role", "")

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
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True
    )

def load_all_history():
    res = requests.get(f"{API_BASE}/admin/all-history", headers=get_headers())

    if res.status_code == 200:
        return res.json()

    st.error("Không lấy được dữ liệu giao dịch.")
    st.write(res.text)
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

def get_money_value(row):
    for col in ["amount", "price", "total_amount"]:
        if col in row and pd.notna(row[col]):
            try:
                return float(row[col])
            except:
                return 0
    return 0

# Kiểm tra quyền truy cập
check_permission()

st.title("💰 Quản lý giao dịch tiền & mua dụng cụ")

all_data = load_all_history()
df_all = pd.DataFrame(all_data)

tab1, tab2, tab3 = st.tabs([
    "💳 Nạp / chuyển / rút tiền",
    "🛒 Mua đồ phụ huynh & học sinh",
    "📊 Biểu đồ & xuất Excel"
])

# ================= TAB 1 =================
with tab1:
    st.subheader("💳 Lịch sử nạp / chuyển / rút tiền")

    if df_all.empty:
        st.info("Chưa có dữ liệu giao dịch.")
    elif "group" not in df_all.columns:
        st.warning("Dữ liệu chưa có cột group để phân loại.")
        st.dataframe(df_all, use_container_width=True)
    else:
        df_wallet = df_all[df_all["group"] == "Ví tiền"].copy()

        if df_wallet.empty:
            st.info("Chưa có dữ liệu nạp / chuyển / rút tiền.")
        else:
            st.dataframe(df_wallet, use_container_width=True)
            export_excel(df_wallet, "lich_su_giao_dich_vi.xlsx")

            st.divider()
            st.subheader("✏️ Chỉnh sửa giao dịch ví")

            selected_id = st.selectbox(
                "Chọn mã giao dịch",
                df_wallet["id"].tolist(),
                key="wallet_selected_id"
            )

            row = df_wallet[df_wallet["id"] == selected_id].iloc[0]

            col1, col2, col3 = st.columns(3)

            with col1:
                amount = st.number_input(
                    "Số tiền",
                    value=float(row.get("amount", 0) or 0),
                    key="wallet_amount"
                )

            with col2:
                type_options = ["nap_tien", "chuyen_cho_con", "rut_tu_con", "deposit", "withdraw", "transfer"]
                old_type = row.get("type", "nap_tien")
                if old_type not in type_options:
                    old_type = "nap_tien"

                transaction_type = st.selectbox(
                    "Loại giao dịch",
                    type_options,
                    index=type_options.index(old_type),
                    key="wallet_type"
                )

            with col3:
                status_options = ["success", "pending", "failed"]
                old_status = row.get("status", "success")
                if old_status not in status_options:
                    old_status = "success"

                status = st.selectbox(
                    "Trạng thái",
                    status_options,
                    index=status_options.index(old_status),
                    key="wallet_status"
                )

            note = st.text_area("Ghi chú", value=row.get("note", ""), key="wallet_note")

            c1, c2 = st.columns(2)

            with c1:
                if st.button("💾 Lưu chỉnh sửa", use_container_width=True, key="wallet_save"):
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
                if st.button("🗑️ Xóa giao dịch", use_container_width=True, key="wallet_delete"):
                    ok = delete_transaction(selected_id)

                    if ok:
                        st.success("Đã xóa giao dịch.")
                        st.rerun()
                    else:
                        st.error("Xóa thất bại.")


# ================= TAB 2 =================
with tab2:
    st.subheader("🛒 Lịch sử mua đồ phụ huynh & học sinh")

    if df_all.empty:
        st.info("Chưa có dữ liệu mua đồ.")
    elif "group" not in df_all.columns:
        st.warning("Dữ liệu chưa có cột group để phân loại.")
        st.dataframe(df_all, use_container_width=True)
    else:
        df_buy = df_all[df_all["group"].isin(["Mua đồ", "Con tự mua", "Đơn hàng"])].copy()

        if df_buy.empty:
            st.info("Chưa có dữ liệu mua đồ.")
        else:
            st.dataframe(df_buy, use_container_width=True)
            export_excel(df_buy, "lich_su_mua_do.xlsx")

            st.divider()
            st.subheader("✏️ Chỉnh sửa đơn mua")

            selected_id = st.selectbox(
                "Chọn mã đơn mua",
                df_buy["id"].tolist(),
                key="buy_selected_id"
            )

            row = df_buy[df_buy["id"] == selected_id].iloc[0]

            col1, col2, col3 = st.columns(3)

            with col1:
                item_name = st.text_input(
                    "Tên dụng cụ",
                    value=row.get("item_name") or row.get("product_name") or row.get("name") or "",
                    key="buy_item_name"
                )

            with col2:
                quantity = st.number_input(
                    "Số lượng",
                    value=int(row.get("quantity", 1) or 1),
                    min_value=1,
                    key="buy_quantity"
                )

            with col3:
                total_amount = st.number_input(
                    "Tổng tiền",
                    value=float(row.get("total_amount") or row.get("price") or row.get("amount") or 0),
                    key="buy_total_amount"
                )

            status_options = ["success", "pending", "cancelled", "approved", "rejected"]
            old_status = row.get("status", "success")
            if old_status not in status_options:
                old_status = "success"

            status = st.selectbox(
                "Trạng thái",
                status_options,
                index=status_options.index(old_status),
                key="buy_status"
            )

            c1, c2 = st.columns(2)

            with c1:
                if st.button("💾 Cập nhật đơn mua", use_container_width=True, key="buy_save"):
                    ok = update_transaction(selected_id, {
                        "item_name": item_name,
                        "product_name": item_name,
                        "quantity": quantity,
                        "total_amount": total_amount,
                        "price": total_amount,
                        "status": status
                    })

                    if ok:
                        st.success("Đã cập nhật đơn mua.")
                        st.rerun()
                    else:
                        st.error("Cập nhật thất bại.")

            with c2:
                if st.button("🗑️ Xóa đơn mua", use_container_width=True, key="buy_delete"):
                    ok = delete_transaction(selected_id)

                    if ok:
                        st.success("Đã xóa đơn mua.")
                        st.rerun()
                    else:
                        st.error("Xóa thất bại.")


# ================= TAB 3 =================
with tab3:
    st.subheader("📊 Biểu đồ & danh sách toàn bộ giao dịch")

    if df_all.empty:
        st.info("Chưa có dữ liệu để thống kê.")
    else:
        st.dataframe(df_all, use_container_width=True)
        export_excel(df_all, "tat_ca_lich_su_giao_dich.xlsx")

        st.divider()

        df_calc = df_all.copy()

        if "amount" in df_calc.columns:
            df_calc["amount"] = pd.to_numeric(df_calc["amount"], errors="coerce").fillna(0)

        if "price" in df_calc.columns:
            df_calc["price"] = pd.to_numeric(df_calc["price"], errors="coerce").fillna(0)

        if "total_amount" in df_calc.columns:
            df_calc["total_amount"] = pd.to_numeric(df_calc["total_amount"], errors="coerce").fillna(0)

        total_amount = 0

        for col in ["amount", "price", "total_amount"]:
            if col in df_calc.columns:
                total_amount += df_calc[col].sum()

        col1, col2, col3 = st.columns(3)

        col1.metric("Tổng số giao dịch", len(df_calc))
        col2.metric("Tổng giá trị", f"{total_amount:,.0f} VNĐ")

        if "parent_name" in df_calc.columns:
            col3.metric("Số phụ huynh", df_calc["parent_name"].nunique())
        elif "group" in df_calc.columns:
            col3.metric("Số nhóm", df_calc["group"].nunique())
        else:
            col3.metric("Số nhóm", 0)

        st.divider()

        if "group" in df_calc.columns:
            col_chart1, col_chart2 = st.columns(2)
            
            with col_chart1:
                st.subheader("📌 Tỷ trọng giao dịch theo nhóm")
                chart_count = df_calc.groupby("group").size().reset_index(name="Số lượng")
                
                chart1 = alt.Chart(chart_count).mark_arc(innerRadius=60).encode(
                    theta=alt.Theta(field="Số lượng", type="quantitative"),
                    color=alt.Color(field="group", type="nominal", legend=alt.Legend(title="Nhóm", orient="bottom")),
                    tooltip=[alt.Tooltip("group", title="Nhóm"), alt.Tooltip("Số lượng", title="Số giao dịch")]
                ).properties(height=350)
                
                st.altair_chart(chart1, use_container_width=True)

            with col_chart2:
                st.subheader("💰 Tổng tiền theo nhóm")

                def row_money(row):
                    for col in ["amount", "price", "total_amount"]:
                        if col in row and pd.notna(row[col]):
                            value = float(row[col])
                            if value != 0:
                                return value
                    return 0

                df_calc["money_value"] = df_calc.apply(row_money, axis=1)
                chart_money = df_calc.groupby("group")["money_value"].sum().reset_index()

                chart2 = alt.Chart(chart_money).mark_bar(cornerRadiusTopRight=4, cornerRadiusBottomRight=4).encode(
                    x=alt.X("money_value:Q", title="Tổng tiền (VNĐ)"),
                    y=alt.Y("group:N", sort='-x', title="Nhóm giao dịch"),
                    color=alt.Color("group:N", legend=None),
                    tooltip=[alt.Tooltip("group", title="Nhóm"), alt.Tooltip("money_value:Q", title="Tổng tiền (VNĐ)", format=",.0f")]
                ).properties(height=350)

                st.altair_chart(chart2, use_container_width=True)