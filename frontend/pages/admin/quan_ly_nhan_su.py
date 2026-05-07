import streamlit as st
import requests
import pandas as pd

st.set_page_config(page_title="Quản lý nhân sự - iKids", layout="wide")

API_URL = "http://127.0.0.1:8000"

def fetch_staff():
    try:
        res = requests.get(f"{API_URL}/staff")
        return res.json() if res.status_code == 200 else []
    except: return []

# --- GIAO DIỆN CHÍNH ---
st.title("👥 Quản lý nhân sự Hệ thống")
st.markdown("Quản lý danh sách Giáo viên, Nhân viên vận hành và trạng thái làm việc.")

# Chia layout: Bên trái là danh sách, bên phải là Form thêm mới
col_list, col_add = st.columns([2, 1])

with col_add:
    st.subheader("➕ Thêm nhân sự mới")
    with st.container(border=True):
        new_name = st.text_input("Họ và tên")
        new_role = st.selectbox("Vai trò", ["Giáo viên", "Nhân viên vận hành", "Quản lý"])
        new_email = st.text_input("Email")
        new_phone = st.text_input("Số điện thoại")
        
        if st.button("Lưu nhân sự", type="primary", use_container_width=True):
            if new_name and new_email:
                payload = {
                    "name": new_name,
                    "role": new_role,
                    "email": new_email,
                    "phone": new_phone,
                    "status": "Đang làm việc"
                }
                res = requests.post(f"{API_URL}/staff/add", json=payload)
                if res.status_code == 200:
                    st.success(f"Đã thêm {new_name} vào hệ thống!")
                    st.rerun()
            else:
                st.error("Vui lòng điền tên và email!")

with col_list:
    st.subheader("📂 Danh sách nhân sự hiện tại")
    all_staff = fetch_staff()
    
    if not all_staff:
        st.info("Chưa có nhân sự nào trong hệ thống.")
    else:
        # Chuyển dữ liệu sang DataFrame để hiển thị bảng đẹp
        df_staff = pd.DataFrame(all_staff)
        
        # Định dạng lại bảng cho chuyên nghiệp
        st.dataframe(
            df_staff[['name', 'role', 'email', 'phone', 'status']],
            column_config={
                "name": "Họ và tên",
                "role": "Vai trò",
                "email": "Email",
                "phone": "Số điện thoại",
                "status": st.column_config.SelectboxColumn(
                    "Trạng thái",
                    options=["Đang làm việc", "Nghỉ phép", "Đã nghỉ việc"],
                )
            },
            use_container_width=True,
            hide_index=True
        )

# --- PHẦN PHÂN TÍCH NHÂN SỰ GỌN GÀNG ---
st.write("---")
st.subheader("📊 Thống kê nhanh")
c1, c2, c3 = st.columns(3)
with c1:
    st.metric("Tổng số nhân sự", len(all_staff))
with c2:
    teachers = [s for s in all_staff if s['role'] == "Giáo viên"]
    st.metric("Giáo viên", len(teachers))
with c3:
    staffs = [s for s in all_staff if s['role'] == "Nhân viên vận hành"]
    st.metric("Vận hành", len(staffs))