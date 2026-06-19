# frontend/pages/admin/quan_ly_nhan_su.py
import streamlit as st
import requests
import pandas as pd
import os
import time

# ================= CRITICAL: CẤU HÌNH TRANG LUÔN ĐỂ ĐẦU FILE =================
st.set_page_config(page_title="Hệ thống Nhân sự & Tài khoản - iKids", layout="wide", page_icon="👥")

# ================= HÀM ĐỌC FILE CSS TOÀN CỤC =================
def load_css(file_name):
    current_dir = os.path.dirname(os.path.abspath(__file__))
    css_root = os.path.abspath(os.path.join(current_dir, "../../CSS"))
    full_path = os.path.join(css_root, file_name)
    if os.path.exists(full_path):
        with open(full_path, "r", encoding="utf-8") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    else:
        st.warning(f"Cảnh báo: Không tìm thấy file CSS tại: {full_path}")

load_css("admin/admin_global.css")

BACKEND_URL = st.session_state.get("api_url", "http://localhost:8000")
API_AUTH = f"{BACKEND_URL}/api/auth"

lang = st.session_state.get("lang", "vi")

# ==========================================
# BỘ TỪ ĐIỂN SONG NGỮ CHI TIẾT
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
        "field_role": "Vai trò hệ thống (Role) (*)",
        "select_parent": "🔗 Liên kết Phụ huynh cho Học sinh",
        "warn_no_parent": "⚠️ Hệ thống chưa có Phụ huynh nào. Hãy tạo Phụ huynh mới!",
        "err_missing_parent": "❌ Bắt buộc phải chọn Phụ huynh liên kết cho Học sinh!",
        "field_email": "Gmail đăng nhập (Bắt buộc) (*)",
        "field_password": "Mật khẩu tạm thời (Bắt buộc) (*)",
        "field_phone": "Số điện thoại liên lạc",
        "role_info": " Tài khoản này sẽ có quyền",
        "btn_create": "Xác nhận tạo tài khoản",
        "warn_empty": "⚠ Vui lòng điền đầy đủ Họ tên, Gmail và Mật khẩu.",
        "success_created": "🎉 Đã cấp quyền thành công cho",
        "sub_list": " Danh Sách Tài Khoản Hệ Thống",
        "no_staff": "Hệ thống chưa có nhân sự.",
        "search_label": "🔍 Tìm kiếm theo tên",
        "search_place": "Nhập tên cần tìm...",
        "filter_role": "Lọc theo Quyền (Role)",
        "all_option": "Tất cả",
        "search_empty": "⚠ Không tìm thấy kết quả phù hợp!",
        "col_name": "Họ và tên",
        "col_role": "Quyền",
        "col_email": "Email",
        "col_phone": "Số điện thoại",
        "col_status": "Trạng thái",
        "sub_action": " Thao Tác Trực Tiếp",
        "action_info": "💡 Hãy tìm kiếm hoặc lọc Role để thao tác tài khoản.",
        "action_empty": "Không có dữ liệu phù hợp.",
        "tab_edit": "✏ Chỉnh Sửa",
        "tab_pwd": "🔑 Đổi Mật Khẩu",
        "tab_delete": "🔒 Khóa / Xóa",
        "btn_save_changes": "Lưu thay đổi",
        "btn_save_pwd": " Lưu mật khẩu",
        "success_update": "✅ Đã cập nhật thành công!",
        "success_pwd": "✅ Đã đổi mật khẩu thành công!",
        "btn_disable": "🚫 Vô Hiệu Hóa",
        "btn_enable": " Mở Khóa",
        "btn_delete_forever": "🗑 Xóa Vĩnh Viễn",
        "sub_stats": " Phân Bổ Nhân Sự",
        "role_teacher": "Giáo viên",
        "role_operator": "Vận hành",
        "role_parent": "Phụ huynh",
        "role_admin": "Quản trị viên",
        "unknown_role": "Chưa xác định",
        
        "link_mode": "Tùy chọn liên kết Phụ huynh",
        "link_existing": "Chọn Phụ huynh đã có",
        "link_new": "Tạo Phụ huynh mới",
        "p_name": "Họ và tên Phụ huynh (*)",
        "p_email": "Email Phụ huynh (*)",
        "p_pwd": "Mật khẩu Phụ huynh (*)",
        "p_phone": "SĐT Phụ huynh",
        "err_parent_create": "Lỗi khi tạo tài khoản Phụ huynh!",
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
        "field_role": "System Role (*)",
        "select_parent": "🔗 Link Parent to Student",
        "warn_no_parent": "⚠️ No Parent accounts found. Please create a new Parent!",
        "err_missing_parent": "❌ A linked Parent is required for Student accounts!",
        "field_email": "Login Email Address (Required) (*)",
        "field_password": "Temporary Password (Required) (*)",
        "field_phone": "Contact Phone Number",
        "role_info": "This account will be granted permissions for",
        "btn_create": "Confirm & Create Account",
        "warn_empty": "⚠ Please fill in Full Name, Email, and Password fields.",
        "success_created": " Permissions successfully granted to",
        "sub_list": " System Accounts List",
        "no_staff": "No staff members registered in the system.",
        "search_label": "🔍 Search by Name",
        "search_place": "Enter name to look up...",
        "filter_role": "Filter by Role",
        "all_option": "All Roles",
        "search_empty": "⚠ No matching records found!",
        "col_name": "Full Name",
        "col_role": "Role",
        "col_email": "Email Address",
        "col_phone": "Phone Number",
        "col_status": "Status",
        "sub_action": " Direct Actions",
        "action_info": "💡 Search or filter by Role to manage a specific account.",
        "action_empty": "No applicable data found.",
        "tab_edit": "✏ Edit Profile",
        "tab_pwd": "🔑 Change Password",
        "tab_delete": " Block / Delete",
        "btn_save_changes": "💾Save Changes",
        "btn_save_pwd": " Save Password",
        "success_update": "✅ Updated successfully!",
        "success_pwd": "✅ Password changed successfully!",
        "btn_disable": "🚫 Deactivate Account",
        "btn_enable": " Reactivate Account",
        "btn_delete_forever": "🗑 Delete Permanently",
        "sub_stats": " Staff Allocation Metrics",
        "role_teacher": "Teachers",
        "role_operator": "Operators",
        "role_parent": "Parents",
        "role_admin": "Administrators",
        "unknown_role": "Unknown",
        
        "link_mode": "Parent Linking Options",
        "link_existing": "Select Existing Parent",
        "link_new": "Create New Parent Account",
        "p_name": "Parent's Full Name (*)",
        "p_email": "Parent's Email (*)",
        "p_pwd": "Parent's Password (*)",
        "p_phone": "Parent's Phone",
        "err_parent_create": "Error creating Parent account!",
    }
}

# =========================
# KIỂM TRA QUYỀN ADMIN CAO CẤP
# =========================
current_role = st.session_state.get("role") or st.session_state.get("user_info", {}).get("role", "")
if current_role.lower() != "admin":
    st.error(HR_LABELS[lang]["access_denied"])
    st.stop()

auth_token = st.session_state.get('access_token') or st.session_state.get('token', '')
headers = {"Authorization": f"Bearer {auth_token}"}

role_display_map = {
    HR_LABELS[lang]["role_teacher"]: "teacher",
    HR_LABELS[lang]["role_operator"]: "operator",
    HR_LABELS[lang]["role_admin"]: "admin",
    HR_LABELS[lang]["role_parent"]: "parent",
    ("Học sinh" if lang == "vi" else "Student"): "student"
}
inverse_role_display_map = {v: k for k, v in role_display_map.items()}

def fetch_staff():
    try:
        res = requests.get(f"{API_AUTH}/users", headers=headers)
        return res.json() if res.status_code == 200 else []
    except: return []

# Lấy trước toàn bộ dữ liệu nhân sự/tài khoản
all_staff = fetch_staff()

# =========================
# GIAO DIỆN CHÍNH (MAIN INTERFACE)
# =========================
st.title(HR_LABELS[lang]["title"])
st.markdown(HR_LABELS[lang]["system_desc"])

col_list, col_add = st.columns([1.8, 1])

with col_add:
    st.subheader(HR_LABELS[lang]["sub_create"])
    with st.container(border=True):
        
        new_name = st.text_input(HR_LABELS[lang]["field_name"], key="s_name")
        selected_role_label = st.selectbox(HR_LABELS[lang]["field_role"], list(role_display_map.keys()))
        new_role = role_display_map[selected_role_label]
        new_email = st.text_input(HR_LABELS[lang]["field_email"], key="s_email")
        new_password = st.text_input(HR_LABELS[lang]["field_password"], type="password", key="s_pwd")
        new_phone = st.text_input(HR_LABELS[lang]["field_phone"], key="s_phone")
        
        selected_parent_id = None
        link_mode = None
        p_name = p_email = p_pwd = p_phone = ""

        if new_role == "student":
            st.markdown("---")
            st.markdown(f"**{HR_LABELS[lang]['select_parent']}**")
            
            link_mode = st.radio(
                HR_LABELS[lang]["link_mode"], 
                [HR_LABELS[lang]["link_existing"], HR_LABELS[lang]["link_new"]], 
                horizontal=True, 
                label_visibility="collapsed"
            )
            
            if link_mode == HR_LABELS[lang]["link_existing"]:
                parent_list = [p for p in all_staff if str(p.get('role', '')).lower() == 'parent']
                if parent_list:
                    parent_options = {p.get('id', p.get('_id')): f"{p.get('name', p.get('full_name', 'Unknown'))} ({p.get('email', '')})" for p in parent_list}
                    selected_parent_id = st.selectbox(
                        "Chọn từ danh sách:", 
                        options=list(parent_options.keys()), 
                        format_func=lambda x: parent_options[x]
                    )
                else:
                    st.warning(HR_LABELS[lang]["warn_no_parent"])
            else:
                st.info(" Điền thông tin bên dưới để tạo luôn tài khoản cho Phụ huynh.")
                p_name = st.text_input(HR_LABELS[lang]["p_name"], key="p_name")
                p_email = st.text_input(HR_LABELS[lang]["p_email"], key="p_email")
                p_pwd = st.text_input(HR_LABELS[lang]["p_pwd"], type="password", key="p_pwd")
                p_phone = st.text_input(HR_LABELS[lang]["p_phone"], key="p_phone")

        st.markdown("---")
        st.info(f"{HR_LABELS[lang]['role_info']}: **{new_role.upper()}**")
        
        # 3. NÚT XÁC NHẬN VÀ GỬI API TẠO TÀI KHOẢN KÉP
        if st.button(HR_LABELS[lang]["btn_create"], type="primary", use_container_width=True):
            if not new_name.strip() or not new_email.strip() or not new_password:
                st.warning(HR_LABELS[lang]["warn_empty"])
            else:
                if new_role == "student":
                    if link_mode == HR_LABELS[lang]["link_existing"]:
                        if not selected_parent_id:
                            st.error(HR_LABELS[lang]["err_missing_parent"])
                            st.stop()
                    
                    elif link_mode == HR_LABELS[lang]["link_new"]:
                        if not p_name.strip() or not p_email.strip() or not p_pwd:
                            st.error(HR_LABELS[lang]["warn_empty"])
                            st.stop()
                        
                        p_payload = {
                            "name": p_name.strip(), 
                            "role": "parent", 
                            "email": p_email.strip().lower(), 
                            "password": p_pwd, 
                            "phone": p_phone.strip(), 
                            "status": "Đang làm việc" if lang == "vi" else "Active"
                        }
                        res_p = requests.post(f"{API_AUTH}/register", json=p_payload, headers=headers)
                        
                        if res_p.status_code in [200, 201]:
                            updated_staff = fetch_staff()
                            new_parent = next((p for p in updated_staff if p.get("email") == p_email.strip().lower()), None)
                            if new_parent:
                                selected_parent_id = new_parent.get("id", new_parent.get("_id"))
                            else:
                                st.error(HR_LABELS[lang]["err_parent_create"])
                                st.stop()
                        else:
                            st.error(res_p.json().get("detail", HR_LABELS[lang]["err_parent_create"]))
                            st.stop()

                payload = {
                    "name": new_name.strip(), 
                    "role": new_role, 
                    "email": new_email.strip().lower(),
                    "password": new_password, 
                    "phone": new_phone.strip(),
                    "status": "Đang làm việc" if lang == "vi" else "Active"
                }
                
                if new_role == "student" and selected_parent_id:
                    payload["parent_id"] = selected_parent_id
                    
                res = requests.post(f"{API_AUTH}/register", json=payload, headers=headers)
                if res.status_code in [200, 201]:
                    msg = f"{HR_LABELS[lang]['success_created']} {new_email}"
                    if new_role == "student" and link_mode == HR_LABELS[lang]["link_new"]:
                        msg += f"\n(Kèm tài khoản Phụ huynh: {p_email})"
                    
                    st.success(msg)
                    st.balloons()
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error(res.json().get("detail", "Lỗi tạo tài khoản!"))

# --- DANH SÁCH TÀI KHOẢN ---
with col_list:
    st.subheader(HR_LABELS[lang]["sub_list"])
    if not all_staff:
        st.info(HR_LABELS[lang]["no_staff"])
    else:
        df_staff = pd.DataFrame(all_staff)
        if 'name' not in df_staff.columns and 'full_name' in df_staff.columns:
            df_staff['name'] = df_staff['full_name']
            
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

# --- KHỐI THAO TÁC TRỰC TIẾP ---
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
            staff_id = row.get('id', row.get('_id'))
            current_status = row.get('status', 'Đang làm việc')
            with st.expander(f"👤 {row['name']} ({row['email']}) - {row['role_display']}"):
                tab1, tab2, tab3 = st.tabs([HR_LABELS[lang]["tab_edit"], HR_LABELS[lang]["tab_pwd"], HR_LABELS[lang]["tab_delete"]])
                with tab1:
                    with st.form(key=f"edit_form_{staff_id}"):
                        edit_name = st.text_input(HR_LABELS[lang]["col_name"], value=row.get('name', ''))
                        edit_email = st.text_input(HR_LABELS[lang]["col_email"], value=row.get('email', ''))
                        edit_phone = st.text_input(HR_LABELS[lang]["col_phone"], value=row.get('phone', ''))
                        
                        status_opts = ["Đang làm việc", "Nghỉ phép", "Đã nghỉ việc", "Vô hiệu hóa"] if lang == "vi" else ["Active", "On Leave", "Resigned", "Disabled"]
                        status_index = status_opts.index(current_status) if current_status in status_opts else 0
                        edit_status = st.selectbox(HR_LABELS[lang]["col_status"], status_opts, index=status_index)
                        
                        if st.form_submit_button(HR_LABELS[lang]["btn_save_changes"]):
                            update_payload = {"name": edit_name.strip(), "email": edit_email.strip().lower(), "phone": edit_phone.strip(), "status": edit_status}
                            res = requests.put(f"{API_AUTH}/users/{staff_id}", json=update_payload, headers=headers)
                            if res.status_code == 200:
                                st.success(HR_LABELS[lang]["success_update"])
                                time.sleep(0.5)
                                st.rerun()
                with tab2:
                    new_pwd = st.text_input(HR_LABELS[lang]["field_password"], type="password", key=f"pwd_{staff_id}")
                    if st.button(HR_LABELS[lang]["btn_save_pwd"], key=f"btn_pwd_{staff_id}"):
                        if new_pwd:
                            res = requests.put(f"{API_AUTH}/users/{staff_id}/password", json={"password": new_pwd}, headers=headers)
                            if res.status_code == 200:
                                st.success(HR_LABELS[lang]["success_pwd"])
                with tab3:
                    c_btn1, c_btn2 = st.columns(2)
                    is_disabled = current_status in ["Vô hiệu hóa", "Disabled"]
                    if not is_disabled:
                        if c_btn1.button(HR_LABELS[lang]["btn_disable"], use_container_width=True, key=f"disable_{staff_id}"):
                            requests.put(f"{API_AUTH}/users/{staff_id}/disable", headers=headers)
                            st.rerun()
                    else:
                        if c_btn1.button(HR_LABELS[lang]["btn_enable"], type="primary", use_container_width=True, key=f"enable_{staff_id}"):
                            requests.put(f"{API_AUTH}/users/{staff_id}/enable", headers=headers)
                            st.rerun()
                    if c_btn2.button(HR_LABELS[lang]["btn_delete_forever"], use_container_width=True, key=f"delete_{staff_id}"):
                        requests.delete(f"{API_AUTH}/users/{staff_id}", headers=headers)
                        st.rerun()

# --- THỐNG KÊ BIỂU ĐỒ SỐ LƯỢNG NHÂN SỰ ---
st.write("---")
if all_staff:
    st.subheader(HR_LABELS[lang]["sub_stats"])
    c1, c2, c3, c4 = st.columns(4)
    def count_role(role_name):
        return len([s for s in all_staff if str(s.get('role', '')).lower() == role_name])
    c1.metric(HR_LABELS[lang]["role_teacher"], count_role("teacher"))
    c2.metric(HR_LABELS[lang]["role_operator"], count_role("operator"))
    c3.metric(HR_LABELS[lang]["role_parent"], count_role("parent"))
    c4.metric(HR_LABELS[lang]["role_admin"], count_role("admin"))