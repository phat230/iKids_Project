import streamlit as st
import requests
import pandas as pd

st.set_page_config(
    page_title="Hệ thống Nhân sự & Tài khoản - iKids",
    layout="wide"
)

API_URL = "http://127.0.0.1:8000"

# =========================
# KIỂM TRA QUYỀN ADMIN
# =========================
if st.session_state.get("user_info", {}).get("role") != "admin":
    st.error("❌ Chỉ Admin mới có quyền quản lý tài khoản")
    st.stop()

# =========================
# JWT TOKEN
# =========================
headers = {
    "Authorization": f"Bearer {st.session_state.get('access_token')}"
}

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

# =========================
# FETCH STAFF
# =========================
def fetch_staff():

    try:
        res = requests.get(
            f"{API_URL}/staff",
            headers=headers
        )

        if res.status_code == 200:
            return res.json()

        return []

    except:
        return []


# =========================
# GIAO DIỆN CHÍNH
# =========================
st.title("👥 Quản lý Nhân sự & Phân quyền RBAC")

st.markdown("""
Hệ thống hỗ trợ quản lý tài khoản và phân quyền:

- 👑 Admin: toàn quyền quản lý tài khoản
- ⚙️ Operator: chỉ vận hành hệ thống
- 👨‍🏫 Teacher: quản lý học tập
- 👨‍👩‍👧 Parent: theo dõi học sinh
- 🎓 Student: tham gia học tập
""")

col_list, col_add = st.columns([1.8, 1])

# =====================================================
# THÊM TÀI KHOẢN
# =====================================================
with col_add:

    st.subheader("🔑 Cấp tài khoản mới")

    with st.container(border=True):

        new_name = st.text_input("Họ và tên nhân sự")

        selected_role_label = st.selectbox(
            "Vai trò hệ thống (Role)",
            list(role_map.keys())
        )

        new_role = role_map[selected_role_label]

        new_email = st.text_input("Gmail đăng nhập (Bắt buộc)")

        new_password = st.text_input(
            "Mật khẩu tạm thời (Bắt buộc)",
            type="password"
        )

        new_phone = st.text_input("Số điện thoại liên lạc")

        st.info(f"💡 Tài khoản này sẽ có quyền: **{new_role.upper()}**")

        if st.button(
            "Xác nhận tạo tài khoản",
            type="primary",
            use_container_width=True
        ):

            if new_name and new_email and new_password:

                payload = {
                    "name": new_name,
                    "role": new_role,
                    "email": new_email,
                    "password": new_password,
                    "phone": new_phone,
                    "status": "Đang làm việc"
                }

                res = requests.post(
                    f"{API_URL}/staff/add",
                    json=payload,
                    headers=headers
                )

                if res.status_code == 200:

                    st.success(
                        f"Đã cấp quyền {new_role} cho {new_email}"
                    )

                    st.rerun()

                else:
                    st.error(
                        res.json().get("detail", "Lỗi hệ thống")
                    )

            else:
                st.warning(
                    "Vui lòng điền đầy đủ Họ tên, Gmail và Mật khẩu."
                )

# =====================================================
# DANH SÁCH TÀI KHOẢN
# =====================================================
with col_list:

    st.subheader("📋 Danh sách tài khoản hệ thống")

    all_staff = fetch_staff()

    if not all_staff:

        st.info(
            "Hệ thống chưa có nhân sự. Vui lòng thêm tài khoản ở bên phải."
        )

    else:

        for staff in all_staff:

            staff['phone'] = staff.get('phone', 'Chưa cập nhật')

            staff['status'] = staff.get(
                'status',
                'Đang làm việc'
            )

        df_staff = pd.DataFrame(all_staff)

        # HIỂN THỊ ROLE TIẾNG VIỆT
        df_staff['role_display'] = df_staff['role'].map(
            inverse_role_map
        ).fillna("Chưa xác định")

        c_search, c_filter = st.columns([2, 1])

        with c_search:

            search_query = st.text_input(
                "🔍 Tìm kiếm theo tên",
                placeholder="Nhập tên cần tìm..."
            )

        with c_filter:

            unique_roles = ["Tất cả"] + \
                df_staff['role_display'].unique().tolist()

            selected_filter_role = st.selectbox(
                "Lọc theo Quyền (Role)",
                unique_roles
            )

        filtered_df = df_staff.copy()

        if search_query:

            filtered_df = filtered_df[
                filtered_df['name'].str.contains(
                    search_query,
                    case=False,
                    na=False
                )
            ]

        if selected_filter_role != "Tất cả":

            filtered_df = filtered_df[
                filtered_df['role_display'] == selected_filter_role
            ]

        if filtered_df.empty:

            st.warning("Không tìm thấy kết quả nào phù hợp!")

        else:

            st.dataframe(
                filtered_df[
                    [
                        'name',
                        'role_display',
                        'email',
                        'phone',
                        'status'
                    ]
                ],
                column_config={
                    "name": "Họ và tên",
                    "role_display":
                        st.column_config.TextColumn("Quyền"),
                    "email": "Email",
                    "phone": "Số điện thoại",
                    "status": "Trạng thái"
                },
                use_container_width=True,
                hide_index=True
            )

# =====================================================
# THAO TÁC USER
# =====================================================
st.write("---")

st.subheader("⚙️ Thao tác trực tiếp")

if all_staff:

    if not search_query and selected_filter_role == "Tất cả":

        st.info(
            "👈 Hãy tìm kiếm hoặc lọc Role để thao tác tài khoản."
        )

    elif filtered_df.empty:

        st.warning("Không có dữ liệu phù hợp.")

    else:

        st.success(
            f"Đã tìm thấy {len(filtered_df)} nhân sự."
        )

        DISPLAY_LIMIT = 10

        for idx, row in filtered_df.head(DISPLAY_LIMIT).iterrows():

            staff_id = row['id']

            current_status = row['status']

            with st.expander(
                f"🛠️ {row['name']} "
                f"({row['email']}) "
                f"- {row['role_display']}"
            ):

                tab1, tab2, tab3 = st.tabs([
                    "📝 Chỉnh sửa",
                    "🔑 Đổi mật khẩu",
                    "⚠️ Khóa / Xóa"
                ])

                # ====================================
                # CHỈNH SỬA
                # ====================================
                with tab1:

                    with st.form(
                        key=f"edit_form_{staff_id}"
                    ):

                        edit_name = st.text_input(
                            "Họ và tên",
                            value=row.get('name', '')
                        )

                        current_role_vn = inverse_role_map.get(
                            row.get('role'),
                            "Giáo viên"
                        )

                        edit_role_vn = st.selectbox(
                            "Vai trò",
                            list(role_map.keys()),
                            index=list(role_map.keys()).index(
                                current_role_vn
                            )
                        )

                        edit_email = st.text_input(
                            "Email",
                            value=row.get('email', '')
                        )

                        edit_phone = st.text_input(
                            "Số điện thoại",
                            value=row.get('phone', '')
                        )

                        status_opts = [
                            "Đang làm việc",
                            "Nghỉ phép",
                            "Đã nghỉ việc",
                            "Vô hiệu hóa"
                        ]

                        if current_status not in status_opts:
                            status_opts.append(current_status)

                        edit_status = st.selectbox(
                            "Trạng thái",
                            status_opts,
                            index=status_opts.index(current_status)
                        )

                        if st.form_submit_button(
                            "💾 Lưu thay đổi",
                            type="primary"
                        ):

                            update_payload = {
                                "name": edit_name,
                                "role": role_map[edit_role_vn],
                                "email": edit_email,
                                "phone": edit_phone,
                                "status": edit_status
                            }

                            res = requests.put(
                                f"{API_URL}/staff/{staff_id}",
                                json=update_payload,
                                headers=headers
                            )

                            if res.status_code == 200:

                                st.success(
                                    "Đã cập nhật thông tin!"
                                )

                                st.rerun()

                            else:
                                st.error("Cập nhật thất bại!")

                # ====================================
                # ĐỔI PASSWORD
                # ====================================
                with tab2:

                    new_pwd = st.text_input(
                        "Nhập mật khẩu mới",
                        type="password",
                        key=f"pwd_{staff_id}"
                    )

                    if st.button(
                        "🔄 Lưu mật khẩu",
                        key=f"btn_pwd_{staff_id}"
                    ):

                        if new_pwd:

                            res = requests.put(
                                f"{API_URL}/staff/{staff_id}/password",
                                json={"password": new_pwd},
                                headers=headers
                            )

                            if res.status_code == 200:

                                st.success(
                                    "Đã đổi mật khẩu!"
                                )

                            else:
                                st.error(
                                    "Đổi mật khẩu thất bại!"
                                )

                        else:
                            st.warning("Vui lòng nhập mật khẩu!")

                # ====================================
                # KHÓA / XÓA
                # ====================================
                with tab3:

                    c_btn1, c_btn2 = st.columns(2)

                    # KHÓA
                    if current_status != "Vô hiệu hóa":

                        if c_btn1.button(
                            "🛑 Vô hiệu hóa",
                            use_container_width=True,
                            key=f"disable_{staff_id}"
                        ):

                            requests.put(
                                f"{API_URL}/staff/{staff_id}/disable",
                                headers=headers
                            )

                            st.rerun()

                    # MỞ KHÓA
                    else:

                        if c_btn1.button(
                            "✅ Mở khóa",
                            type="primary",
                            use_container_width=True,
                            key=f"enable_{staff_id}"
                        ):

                            requests.put(
                                f"{API_URL}/staff/{staff_id}/enable",
                                headers=headers
                            )

                            st.rerun()

                    # XÓA
                    if c_btn2.button(
                        "🗑️ Xóa vĩnh viễn",
                        use_container_width=True,
                        key=f"delete_{staff_id}"
                    ):

                        requests.delete(
                            f"{API_URL}/staff/{staff_id}",
                            headers=headers
                        )

                        st.rerun()

# =====================================================
# THỐNG KÊ
# =====================================================
st.write("---")

if all_staff:

    st.subheader("📊 Phân bổ nhân sự")

    c1, c2, c3, c4 = st.columns(4)

    def count_role(role_name):

        return len([
            s for s in all_staff
            if s.get('role') == role_name
        ])

    c1.metric("Giáo viên", count_role("teacher"))

    c2.metric("Vận hành", count_role("operator"))

    c3.metric("Phụ huynh", count_role("parent"))

    c4.metric("Quản trị viên", count_role("admin"))