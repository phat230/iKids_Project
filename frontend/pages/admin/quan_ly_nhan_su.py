import streamlit as st
import requests
import pandas as pd
import os

st.set_page_config(
    page_title="Hệ thống Nhân sự & Tài khoản - iKids",
    layout="wide",
    page_icon="👥"
)

# ================= HÀM ĐỌC FILE CSS (SỬA LỖI ĐƯỜNG DẪN TUYỆT ĐỐI) =================
def load_css(file_name):
    """
    Tự động tìm file CSS trong thư mục frontend/CSS/
    file_name: tên file kèm thư mục con, ví dụ 'admin/quan_ly_nhan_su.css'
    """
    # Lấy đường dẫn tuyệt đối đến thư mục chứa file hiện tại (frontend/pages/admin)
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Tìm đường dẫn đến thư mục CSS (lùi 2 cấp rồi vào CSS/)
    css_root = os.path.abspath(os.path.join(current_dir, "../../CSS"))
    full_path = os.path.join(css_root, file_name)

    if os.path.exists(full_path):
        with open(full_path, "r", encoding="utf-8") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    else:
        st.warning(f"⚠️ Không tìm thấy file CSS tại: {full_path}")

# Tải CSS làm đẹp (Chỉ truyền phần sau thư mục CSS/)
load_css("admin/quan_ly_nhan_su.css")

API_URL = "http://127.0.0.1:8000"

# =========================
# KIỂM TRA QUYỀN ADMIN
# =========================
if st.session_state.get("user_info", {}).get("role") != "admin":
    st.error("❌ Chỉ Admin mới có quyền quản lý tài khoản")
    st.stop()

headers = {"Authorization": f"Bearer {st.session_state.get('access_token')}"}

# =========================
# ROLE MAP
# =========================
role_map = {
    "Giáo viên": "teacher",
    "Nhân viên vận hành": "operator",
    "Phụ huynh": "parent",
    "Giám đốc": "admin",
    "Học sinh": "student"
}

inverse_role_map = {v: k for k, v in role_map.items()}

def fetch_staff():
    try:
        res = requests.get(f"{API_URL}/staff", headers=headers)
        return res.json() if res.status_code == 200 else []
    except: return []

# =========================
# GIAO DIỆN CHÍNH
# =========================
st.title("👥 Quản lý Nhân sự & Phân quyền RBAC")

st.markdown("""
Hệ thống hỗ trợ quản lý tài khoản và phân quyền:
- 👑 **Admin**: toàn quyền quản lý tài khoản
- ⚙️ **Operator**: chỉ vận hành hệ thống
- 👨‍🏫 **Teacher**: quản lý học tập
- 👨‍👩‍👦 **Parent**: theo dõi học sinh
- 🎓 **Student**: tham gia học tập
""")

col_list, col_add = st.columns([1.8, 1])

# --- THÊM TÀI KHOẢN ---
with col_add:
    st.subheader("➕ Cấp tài khoản mới")
    with st.container(border=True):
        new_name = st.text_input("Họ và tên nhân sự")
        selected_role_label = st.selectbox("Vai trò hệ thống (Role)", list(role_map.keys()))
        new_role = role_map[selected_role_label]
        new_email = st.text_input("Gmail đăng nhập (Bắt buộc)")
        new_password = st.text_input("Mật khẩu tạm thời (Bắt buộc)", type="password")
        new_phone = st.text_input("Số điện thoại liên lạc")

        st.info(f"ℹ️ Tài khoản này sẽ có quyền: **{new_role.upper()}**")

        if st.button("Xác nhận tạo tài khoản", type="primary", use_container_width=True):
            if new_name and new_email and new_password:
                payload = {
                    "name": new_name, "role": new_role, "email": new_email,
                    "password": new_password, "phone": new_phone, "status": "Đang làm việc"
                }
                res = requests.post(f"{API_URL}/staff/add", json=payload, headers=headers)
                if res.status_code == 200:
                    st.success(f"Đã cấp quyền {new_role} cho {new_email}")
                    st.rerun()
                else:
                    st.error(res.json().get("detail", "Lỗi hệ thống"))
            else:
                st.warning("Vui lòng điền đầy đủ Họ tên, Gmail và Mật khẩu.")

# --- DANH SÁCH TÀI KHOẢN ---
with col_list:
    st.subheader("📋 Danh sách tài khoản hệ thống")
    all_staff = fetch_staff()
    if not all_staff:
        st.info("Hệ thống chưa có nhân sự.")
    else:
        df_staff = pd.DataFrame(all_staff)
        df_staff['role_display'] = df_staff['role'].map(inverse_role_map).fillna("Chưa xác định")

        c_search, c_filter = st.columns([2, 1])
        with c_search:
            search_query = st.text_input("🔍 Tìm kiếm theo tên", placeholder="Nhập tên cần tìm...")
        with c_filter:
            unique_roles = ["Tất cả"] + df_staff['role_display'].unique().tolist()
            selected_filter_role = st.selectbox("Lọc theo Quyền (Role)", unique_roles)

        filtered_df = df_staff.copy()
        if search_query:
            filtered_df = filtered_df[filtered_df['name'].str.contains(search_query, case=False, na=False)]
        if selected_filter_role != "Tất cả":
            filtered_df = filtered_df[filtered_df['role_display'] == selected_filter_role]

        if filtered_df.empty:
            st.warning("Không tìm thấy kết quả!")
        else:
            st.dataframe(
                filtered_df[['name', 'role_display', 'email', 'phone', 'status']],
                column_config={
                    "name": "Họ và tên", "role_display": "Quyền",
                    "email": "Email", "phone": "Số điện thoại", "status": "Trạng thái"
                },
                use_container_width=True, hide_index=True
            )

# --- THAO TÁC USER ---
st.write("---")
st.subheader("⚙️ Thao tác trực tiếp")
if all_staff:
    if not search_query and selected_filter_role == "Tất cả":
        st.info("💡 Hãy tìm kiếm hoặc lọc Role để thao tác tài khoản.")
    elif filtered_df.empty:
        st.warning("Không có dữ liệu phù hợp.")
    else:
        DISPLAY_LIMIT = 10
        for idx, row in filtered_df.head(DISPLAY_LIMIT).iterrows():
            staff_id = row['id']
            current_status = row.get('status', 'Đang làm việc')

            with st.expander(f"👤 {row['name']} ({row['email']}) - {row['role_display']}"):
                tab1, tab2, tab3 = st.tabs(["✏️ Chỉnh sửa", "🔑 Đổi mật khẩu", "⚠️ Khóa / Xóa"])

                with tab1:
                    with st.form(key=f"edit_form_{staff_id}"):
                        edit_name = st.text_input("Họ và tên", value=row.get('name', ''))
                        edit_email = st.text_input("Email", value=row.get('email', ''))
                        edit_phone = st.text_input("Số điện thoại", value=row.get('phone', ''))
                        status_opts = ["Đang làm việc", "Nghỉ phép", "Đã nghỉ việc", "Vô hiệu hóa"]
                        edit_status = st.selectbox("Trạng thái", status_opts, index=status_opts.index(current_status) if current_status in status_opts else 0)

                        if st.form_submit_button("💾 Lưu thay đổi", type="primary"):
                            update_payload = {"name": edit_name, "email": edit_email, "phone": edit_phone, "status": edit_status}
                            res = requests.put(f"{API_URL}/staff/{staff_id}", json=update_payload, headers=headers)
                            if res.status_code == 200:
                                st.success("Đã cập nhật!"); st.rerun()

                with tab2:
                    new_pwd = st.text_input("Mật khẩu mới", type="password", key=f"pwd_{staff_id}")
                    if st.button("💾 Lưu mật khẩu", key=f"btn_pwd_{staff_id}"):
                        if new_pwd:
                            res = requests.put(f"{API_URL}/staff/{staff_id}/password", json={"password": new_pwd}, headers=headers)
                            if res.status_code == 200: st.success("Đã đổi mật khẩu!")
                
                with tab3:
                    c_btn1, c_btn2 = st.columns(2)
                    if current_status != "Vô hiệu hóa":
                        if c_btn1.button("🚫 Vô hiệu hóa", use_container_width=True, key=f"disable_{staff_id}"):
                            requests.put(f"{API_URL}/staff/{staff_id}/disable", headers=headers); st.rerun()
                    else:
                        if c_btn1.button("✅ Mở khóa", type="primary", use_container_width=True, key=f"enable_{staff_id}"):
                            requests.put(f"{API_URL}/staff/{staff_id}/enable", headers=headers); st.rerun()
                    if c_btn2.button("🗑️ Xóa vĩnh viễn", use_container_width=True, key=f"delete_{staff_id}"):
                        requests.delete(f"{API_URL}/staff/{staff_id}", headers=headers); st.rerun()

# --- THỐNG KÊ ---
st.write("---")
if all_staff:
    st.subheader("📊 Phân bổ nhân sự")
    c1, c2, c3, c4 = st.columns(4)
    def count_role(role_name): return len([s for s in all_staff if s.get('role') == role_name])
    c1.metric("Giáo viên", count_role("teacher"))
    c2.metric("Vận hành", count_role("operator"))
    c3.metric("Phụ huynh", count_role("parent"))
    c4.metric("Quản trị viên", count_role("admin"))