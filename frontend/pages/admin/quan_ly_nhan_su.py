import streamlit as st
import requests
import pandas as pd
import os

# ================= CRITICAL: CẤU HÌNH TRANG LUÔN ĐỂ ĐẦU FILE =================
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
    current_dir = os.path.dirname(os.path.abspath(__file__))
    css_root = os.path.abspath(os.path.join(current_dir, "../../CSS"))
    full_path = os.path.join(css_root, file_name)

    if os.path.exists(full_path):
        with open(full_path, "r", encoding="utf-8") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    else:
        st.warning(f"⚠️ Không tìm thấy file CSS tại: {full_path}")

# Tải CSS làm đẹp
load_css("admin/quan_ly_nhan_su.css")

API_URL = "http://127.0.0.1:8000"

# Lấy cấu hình ngôn ngữ hiện hành từ session_state (Mặc định là "vi")
lang = st.session_state.get("lang", "vi")

# ==========================================
# BỘ TỪ ĐIỂN SONG NGỮ CHI TIẾT CHO QUAN_LY_NHAN_SU
# ==========================================
HR_LABELS = {
    "vi": {
        "access_denied": "❌ Chỉ Admin mới có quyền quản lý tài khoản",
        "title": "Quản lý Nhân sự & Phân quyền RBAC",
        "system_desc": """
        Hệ thống hỗ trợ quản lý tài khoản và phân quyền:
        - **Admin**: toàn quyền quản lý tài khoản
        - **Operator**: chỉ vận hành hệ thống
        - **Teacher**: quản lý học tập
        - **Parent**: theo dõi học sinh
        - **Student**: tham gia học tập
        """,
        "sub_create": "👤 Cấp Tài Khoản Mới",
        "field_name": "Họ và tên nhân sự (*)",
        "field_role": "Vai trò hệ thống (Role)",
        "field_email": "Gmail đăng nhập (Bắt buộc) (*)",
        "field_password": "Mật khẩu tạm thời (Bắt buộc) (*)",
        "field_phone": "Số điện thoại liên lạc",
        "role_info": "ℹ️ Tài khoản này sẽ có quyền",
        "btn_create": "Xác nhận tạo tài khoản",
        "warn_empty": "⚠️ Vui lòng điền đầy đủ Họ tên, Gmail và Mật khẩu.",
        "success_created": "🎉 Đã cấp quyền thành công cho",
        
        "sub_list": "📋 Danh Sách Tài Khoản Hệ Thống",
        "no_staff": "Hệ thống chưa có nhân sự.",
        "search_label": "🔍 Tìm kiếm theo tên",
        "search_place": "Nhập tên cần tìm...",
        "filter_role": "Lọc theo Quyền (Role)",
        "all_option": "Tất cả",
        "search_empty": "⚠️ Không tìm thấy kết quả phù hợp!",
        
        "col_name": "Họ và tên",
        "col_role": "Quyền",
        "col_email": "Email",
        "col_phone": "Số điện thoại",
        "col_status": "Trạng thái",
        
        "sub_action": "⚡ Thao Tác Trực Tiếp",
        "action_info": "💡 Hãy tìm kiếm hoặc lọc Role để thao tác tài khoản.",
        "action_empty": "Không có dữ liệu phù hợp.",
        
        "tab_edit": "✏️ Chỉnh Sửa",
        "tab_pwd": "🔑 Đổi Mật Khẩu",
        "tab_delete": "🔒 Khóa / Xóa",
        
        "btn_save_changes": "💾 Lưu thay đổi",
        "btn_save_pwd": "💾 Lưu mật khẩu",
        "success_update": "✅ Đã cập nhật thành công!",
        "success_pwd": "✅ Đã đổi mật khẩu thành công!",
        
        "btn_disable": "🚫 Vô Hiệu Hóa",
        "btn_enable": "🔓 Mở Khóa",
        "btn_delete_forever": "🗑️ Xóa Vĩnh Viễn",
        
        "sub_stats": "📊 Phân Bổ Nhân Sự",
        "role_teacher": "Giáo viên",
        "role_operator": "Vận hành",
        "role_parent": "Phụ huynh",
        "role_admin": "Quản trị viên",
        "unknown_role": "Chưa xác định"
    },
    "en": {
        "access_denied": "❌ Only System Administrators have access to account management.",
        "title": "Staff Management & RBAC Permissions",
        "system_desc": """
        Account Management and Role-Based Access Control (RBAC):
        - **Admin**: Full system management privileges
        - **Operator**: System operations and workflow management
        - **Teacher**: Academic management and student tracking
        - **Parent**: Student progress and wallet monitoring
        - **Student**: Learning dashboard access
        """,
        "sub_create": "👤 Provision New Account",
        "field_name": "Full Name (*)",
        "field_role": "System Role",
        "field_email": "Login Email Address (Required) (*)",
        "field_password": "Temporary Password (Required) (*)",
        "field_phone": "Contact Phone Number",
        "role_info": "ℹ️ This account will be granted permissions for",
        "btn_create": "Confirm & Create Account",
        "warn_empty": "⚠️ Please fill in Full Name, Email, and Password fields.",
        "success_created": "🎉 Permissions successfully granted to",
        
        "sub_list": "📋 System Accounts List",
        "no_staff": "No staff members registered in the system.",
        "search_label": "🔍 Search by Name",
        "search_place": "Enter name to look up...",
        "filter_role": "Filter by Role",
        "all_option": "All Roles",
        "search_empty": "⚠️ No matching records found!",
        
        "col_name": "Full Name",
        "col_role": "Role",
        "col_email": "Email Address",
        "col_phone": "Phone Number",
        "col_status": "Status",
        
        "sub_action": "⚡ Direct Actions",
        "action_info": "💡 Search or filter by Role to manage a specific account.",
        "action_empty": "No applicable data found.",
        
        "tab_edit": "✏️ Edit Profile",
        "tab_pwd": "🔑 Change Password",
        "tab_delete": "🔒 Block / Delete",
        
        "btn_save_changes": "💾 Save Changes",
        "btn_save_pwd": "💾 Save Password",
        "success_update": "✅ Updated successfully!",
        "success_pwd": "✅ Password changed successfully!",
        
        "btn_disable": "🚫 Deactivate Account",
        "btn_enable": "🔓 Reactivate Account",
        "btn_delete_forever": "🗑️ Delete Permanently",
        
        "sub_stats": "📊 Staff Allocation Metrics",
        "role_teacher": "Teachers",
        "role_operator": "Operators",
        "role_parent": "Parents",
        "role_admin": "Administrators",
        "unknown_role": "Unknown"
    }
}

# =========================
# KIỂM TRA QUYỀN ADMIN
# =========================
if st.session_state.get("user_info", {}).get("role") != "admin":
    st.error(HR_LABELS[lang]["access_denied"])
    st.stop()

headers = {"Authorization": f"Bearer {st.session_state.get('access_token')}"}

# Cấu hình map phân loại Role theo đa ngôn ngữ
role_display_map = {
    HR_LABELS[lang]["role_teacher"]: "teacher",
    HR_LABELS[lang]["role_operator"]: "operator",
    HR_LABELS[lang]["role_parent"]: "parent",
    HR_LABELS[lang]["role_admin"]: "admin",
    "Học sinh" if lang == "vi" else "Student": "student"
}
inverse_role_display_map = {v: k for k, v in role_display_map.items()}

def fetch_staff():
    try:
        res = requests.get(f"{API_URL}/staff", headers=headers)
        return res.json() if res.status_code == 200 else []
    except: return []

# =========================
# GIAO DIỆN CHÍNH
# =========================
st.title(HR_LABELS[lang]["title"])
st.markdown(HR_LABELS[lang]["system_desc"])

col_list, col_add = st.columns([1.8, 1])

# --- THÊM TÀI KHOẢN MỚI ---
with col_add:
    st.subheader(HR_LABELS[lang]["sub_create"])
    with st.container(border=True):
        new_name = st.text_input(HR_LABELS[lang]["field_name"])
        selected_role_label = st.selectbox(HR_LABELS[lang]["field_role"], list(role_display_map.keys()))
        new_role = role_display_map[selected_role_label]
        new_email = st.text_input(HR_LABELS[lang]["field_email"])
        new_password = st.text_input(HR_LABELS[lang]["field_password"], type="password")
        new_phone = st.text_input(HR_LABELS[lang]["field_phone"])

        st.info(f"{HR_LABELS[lang]['role_info']}: **{new_role.upper()}**")

        if st.button(HR_LABELS[lang]["btn_create"], type="primary", use_container_width=True):
            if new_name.strip() and new_email.strip() and new_password:
                payload = {
                    "name": new_name.strip(), "role": new_role, "email": new_email.strip().lower(),
                    "password": new_password, "phone": new_phone.strip(), 
                    "status": "Đang làm việc" if lang == "vi" else "Active"
                }
                res = requests.post(f"{API_URL}/staff/add", json=payload, headers=headers)
                if res.status_code == 200:
                    st.success(f"{HR_LABELS[lang]['success_created']} {new_email}")
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error(res.json().get("detail", "Error occurred"))
            else:
                st.warning(HR_LABELS[lang]["warn_empty"])

# --- DANH SÁCH TÀI KHOẢN ---
with col_list:
    st.subheader(HR_LABELS[lang]["sub_list"])
    all_staff = fetch_staff()
    if not all_staff:
        st.info(HR_LABELS[lang]["no_staff"])
    else:
        df_staff = pd.DataFrame(all_staff)
        df_staff['role_display'] = df_staff['role'].map(inverse_role_display_map).fillna(HR_LABELS[lang]["unknown_role"])

        c_search, c_filter = st.columns([2, 1])
        with c_search:
            search_query = st.text_input(HR_LABELS[lang]["search_label"], placeholder=HR_LABELS[lang]["search_place"])
        with c_filter:
            unique_roles = [HR_LABELS[lang]["all_option"]] + df_staff['role_display'].unique().tolist()
            selected_filter_role = st.selectbox(HR_LABELS[lang]["filter_role"], unique_roles)

        filtered_df = df_staff.copy()
        if search_query:
            filtered_df = filtered_df[filtered_df['name'].str.contains(search_query, case=False, na=False)]
        if selected_filter_role != HR_LABELS[lang]["all_option"]:
            filtered_df = filtered_df[filtered_df['role_display'] == selected_filter_role]

        if filtered_df.empty:
            st.warning(HR_LABELS[lang]["search_empty"])
        else:
            # Map tên cột dataframe động theo cấu hình ngôn ngữ
            st.dataframe(
                filtered_df[['name', 'role_display', 'email', 'phone', 'status']],
                column_config={
                    "name": HR_LABELS[lang]["col_name"], 
                    "role_display": HR_LABELS[lang]["col_role"],
                    "email": HR_LABELS[lang]["col_email"], 
                    "phone": HR_LABELS[lang]["col_phone"], 
                    "status": HR_LABELS[lang]["col_status"]
                },
                use_container_width=True, hide_index=True
            )

# --- THAO TÁC USER ---
st.write("---")
st.subheader(HR_LABELS[lang]["sub_action"])
if all_staff:
    if not search_query and selected_filter_role == HR_LABELS[lang]["all_option"]:
        st.info(HR_LABELS[lang]["action_info"])
    elif filtered_df.empty:
        st.warning(HR_LABELS[lang]["action_empty"])
    else:
        DISPLAY_LIMIT = 10
        for idx, row in filtered_df.head(DISPLAY_LIMIT).iterrows():
            staff_id = row['id']
            current_status = row.get('status', 'Đang làm việc')

            with st.expander(f"👤 {row['name']} ({row['email']}) - {row['role_display']}"):
                tab1, tab2, tab3 = st.tabs([HR_LABELS[lang]["tab_edit"], HR_LABELS[lang]["tab_pwd"], HR_LABELS[lang]["tab_delete"]])

                with tab1:
                    with st.form(key=f"edit_form_{staff_id}"):
                        edit_name = st.text_input(HR_LABELS[lang]["col_name"], value=row.get('name', ''))
                        edit_email = st.text_input(HR_LABELS[lang]["col_email"], value=row.get('email', ''))
                        edit_phone = st.text_input(HR_LABELS[lang]["col_phone"], value=row.get('phone', ''))
                        
                        # Cấu hình động bộ chọn trạng thái nhân sự
                        status_opts = ["Đang làm việc", "Nghỉ phép", "Đã nghỉ việc", "Vô hiệu hóa"] if lang == "vi" else ["Active", "On Leave", "Resigned", "Disabled"]
                        # Bản đồ đồng bộ trạng thái gốc gửi lên Backend
                        if current_status not in status_opts:
                            status_index = 0
                        else:
                            status_index = status_opts.index(current_status)
                            
                        edit_status = st.selectbox(HR_LABELS[lang]["col_status"], status_opts, index=status_index)

                        if st.form_submit_button(HR_LABELS[lang]["btn_save_changes"]):
                            update_payload = {"name": edit_name.strip(), "email": edit_email.strip().lower(), "phone": edit_phone.strip(), "status": edit_status}
                            res = requests.put(f"{API_URL}/staff/{staff_id}", json=update_payload, headers=headers)
                            if res.status_code == 200:
                                st.success(HR_LABELS[lang]["success_update"])
                                time.sleep(0.5)
                                st.rerun()

                with tab2:
                    new_pwd = st.text_input(HR_LABELS[lang]["field_password"], type="password", key=f"pwd_{staff_id}")
                    if st.button(HR_LABELS[lang]["btn_save_pwd"], key=f"btn_pwd_{staff_id}"):
                        if new_pwd:
                            res = requests.put(f"{API_URL}/staff/{staff_id}/password", json={"password": new_pwd}, headers=headers)
                            if res.status_code == 200: 
                                st.success(HR_LABELS[lang]["success_pwd"])
                
                with tab3:
                    c_btn1, c_btn2 = st.columns(2)
                    is_disabled = current_status in ["Vô hiệu hóa", "Disabled"]
                    
                    if not is_disabled:
                        if c_btn1.button(HR_LABELS[lang]["btn_disable"], use_container_width=True, key=f"disable_{staff_id}"):
                            requests.put(f"{API_URL}/staff/{staff_id}/disable", headers=headers)
                            st.rerun()
                    else:
                        if c_btn1.button(HR_LABELS[lang]["btn_enable"], type="primary", use_container_width=True, key=f"enable_{staff_id}"):
                            requests.put(f"{API_URL}/staff/{staff_id}/enable", headers=headers)
                            st.rerun()
                            
                    if c_btn2.button(HR_LABELS[lang]["btn_delete_forever"], use_container_width=True, key=f"delete_{staff_id}"):
                        requests.delete(f"{API_URL}/staff/{staff_id}", headers=headers)
                        st.rerun()

# --- THỐNG KÊ BIỂU ĐỒ (METRICS) ---
st.write("---")
if all_staff:
    st.subheader(HR_LABELS[lang]["sub_stats"])
    c1, c2, c3, c4 = st.columns(4)
    def count_role(role_name): 
        return len([s for s in all_staff if s.get('role') == role_name])
        
    c1.metric(HR_LABELS[lang]["role_teacher"], count_role("teacher"))
    c2.metric(HR_LABELS[lang]["role_operator"], count_role("operator"))
    c3.metric(HR_LABELS[lang]["role_parent"], count_role("parent"))
    c4.metric(HR_LABELS[lang]["role_admin"], count_role("admin"))