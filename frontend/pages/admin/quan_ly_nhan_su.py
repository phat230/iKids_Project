import streamlit as st
import requests
import pandas as pd

st.set_page_config(page_title="Hệ thống Nhân sự & Tài khoản - iKids", layout="wide")

API_URL = "http://127.0.0.1:8000"

# Biến map role dùng chung cho toàn bộ trang
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
        res = requests.get(f"{API_URL}/staff")
        return res.json() if res.status_code == 200 else []
    except: return []

# --- GIAO DIỆN CHÍNH ---
st.title("👥 Quản lý Nhân sự & Cấp quyền Hệ thống")
st.markdown("Thêm nhân sự mới sẽ tự động khởi tạo tài khoản đăng nhập dựa trên Email và Vai trò.")

col_list, col_add = st.columns([1.8, 1])

with col_add:
    st.subheader("🔑 Cấp tài khoản mới")
    with st.container(border=True):
        new_name = st.text_input("Họ và tên nhân sự")
        selected_role_label = st.selectbox("Vai trò hệ thống (Role)", list(role_map.keys()))
        new_role = role_map[selected_role_label]
        
        new_email = st.text_input("Gmail đăng nhập (Bắt buộc)")
        new_password = st.text_input("Mật khẩu tạm thời (Bắt buộc)", type="password")
        new_phone = st.text_input("Số điện thoại liên lạc")
        
        st.info(f"💡 Tài khoản này sẽ có quyền: **{new_role.upper()}**")
        
        if st.button("Xác nhận tạo tài khoản", type="primary", use_container_width=True):
            if new_name and new_email and new_password:
                payload = {
                    "name": new_name,
                    "role": new_role,
                    "email": new_email,
                    "password": new_password,
                    "phone": new_phone,
                    "status": "Đang làm việc"
                }
                res = requests.post(f"{API_URL}/staff/add", json=payload)
                if res.status_code == 200:
                    st.success(f"Đã cấp quyền {new_role} cho {new_email}")
                    st.rerun()
                else:
                    st.error(res.json().get("detail", "Lỗi hệ thống"))
            else:
                st.warning("Vui lòng điền đầy đủ Họ tên, Gmail và Mật khẩu.")

with col_list:
    st.subheader("📋 Danh sách tài khoản hệ thống")
    all_staff = fetch_staff()
    
    if not all_staff:
        st.info("Hệ thống chưa có nhân sự. Vui lòng thêm tài khoản ở bên phải.")
    else:
        for staff in all_staff:
            staff['phone'] = staff.get('phone', 'Chưa cập nhật')
            staff['status'] = staff.get('status', 'Đang làm việc')
            
        df_staff = pd.DataFrame(all_staff)
        
        # --- LOGIC MỚI: Dịch Role sang Tiếng Việt để hiển thị đẹp mắt ---
        df_staff['role_display'] = df_staff['role'].map(inverse_role_map).fillna("Chưa xác định")
        
        c_search, c_filter = st.columns([2, 1])
        with c_search:
            search_query = st.text_input("🔍 Tìm kiếm theo tên", placeholder="Nhập tên cần tìm...")
        with c_filter:
            # Lọc theo Role Tiếng Việt
            unique_roles = ["Tất cả"] + df_staff['role_display'].unique().tolist()
            selected_filter_role = st.selectbox("Lọc theo Quyền (Role)", unique_roles)
        
        filtered_df = df_staff.copy()
        
        if search_query:
            filtered_df = filtered_df[filtered_df['name'].str.contains(search_query, case=False, na=False)]
            
        if selected_filter_role != "Tất cả":
            filtered_df = filtered_df[filtered_df['role_display'] == selected_filter_role]
        
        if filtered_df.empty:
            st.warning("Không tìm thấy kết quả nào phù hợp!")
        else:
            # Bảng hiển thị cột 'role_display' thay vì cột 'role' gốc
            st.dataframe(
                filtered_df[['name', 'role_display', 'email', 'phone', 'status']],
                column_config={
                    "name": "Họ và tên",
                    "role_display": st.column_config.TextColumn("Quyền (Role)"),
                    "email": "Gmail đăng nhập",
                    "phone": "Số điện thoại",
                    "status": "Trạng thái"
                },
                use_container_width=True,
                hide_index=True
            )

# --- THAO TÁC: SỬA / XÓA / ĐỔI MẬT KHẨU ---
st.write("---")
st.subheader("⚙️ Thao tác trực tiếp")

if all_staff:
    if not search_query and selected_filter_role == "Tất cả":
        st.info("👈 Vui lòng nhập Tên vào ô tìm kiếm hoặc chọn Quyền (Role) ở bảng trên để hiển thị công cụ Sửa/Xóa. Việc này giúp tránh tải hàng ngàn dữ liệu cùng lúc.")
    elif filtered_df.empty:
        st.warning("Không có nhân sự nào khớp với điều kiện để thao tác.")
    else:
        st.success(f"Đã tìm thấy {len(filtered_df)} nhân sự. Vui lòng click vào tên bên dưới để thao tác:")
        
        DISPLAY_LIMIT = 10
        
        for idx, row in filtered_df.head(DISPLAY_LIMIT).iterrows():
            staff_id = row['id']
            current_status = row['status']
            
            # Tiêu đề Expander hiện thị chức danh bằng Tiếng Việt
            with st.expander(f"🛠️ Cập nhật: {row['name']} ({row['email']}) - Vai trò: {row['role_display']}"):
                tab1, tab2, tab3 = st.tabs(["📝 Chỉnh sửa", "🔑 Đổi mật khẩu", "⚠️ Khóa / Xóa"])
                
                with tab1:
                    with st.form(key=f"edit_form_{staff_id}"):
                        edit_name = st.text_input("Họ và tên", value=row.get('name', ''))
                        
                        # Vẫn xử lý logic Edit dựa trên mã gốc
                        current_role_vn = inverse_role_map.get(row.get('role'), "Giáo viên")
                        edit_role_vn = st.selectbox("Vai trò", list(role_map.keys()), index=list(role_map.keys()).index(current_role_vn))
                        
                        edit_email = st.text_input("Email", value=row.get('email', ''))
                        edit_phone = st.text_input("Số điện thoại", value=row.get('phone', ''))
                        
                        status_opts = ["Đang làm việc", "Nghỉ phép", "Đã nghỉ việc", "Vô hiệu hóa"]
                        if current_status not in status_opts: status_opts.append(current_status)
                        edit_status = st.selectbox("Trạng thái", status_opts, index=status_opts.index(current_status))
                        
                        if st.form_submit_button("💾 Lưu thay đổi", type="primary"):
                            update_payload = {
                                "name": edit_name,
                                "role": role_map[edit_role_vn],
                                "email": edit_email,
                                "phone": edit_phone,
                                "status": edit_status
                            }
                            res = requests.put(f"{API_URL}/staff/{staff_id}", json=update_payload)
                            if res.status_code == 200:
                                st.success("Đã cập nhật thông tin thành công!")
                                st.rerun()
                            else:
                                st.error("Cập nhật thất bại!")
                                
                with tab2:
                    new_pwd = st.text_input("Nhập mật khẩu mới", type="password", key=f"pwd_{staff_id}")
                    if st.button("🔄 Lưu mật khẩu", key=f"btn_pwd_{staff_id}"):
                        if new_pwd:
                            res = requests.put(f"{API_URL}/staff/{staff_id}/password", json={"password": new_pwd})
                            if res.status_code == 200:
                                st.success("Đã đổi mật khẩu thành công!")
                            else:
                                st.error("Đổi mật khẩu thất bại!")
                        else:
                            st.warning("Vui lòng nhập mật khẩu!")
                            
                with tab3:
                    c_btn1, c_btn2 = st.columns(2)
                    if current_status != "Vô hiệu hóa":
                        if c_btn1.button("🛑 Vô hiệu hóa", use_container_width=True, key=f"disable_{staff_id}"):
                            requests.put(f"{API_URL}/staff/{staff_id}", json={"status": "Vô hiệu hóa"})
                            st.rerun()
                    else:
                        if c_btn1.button("✅ Mở khóa", type="primary", use_container_width=True, key=f"enable_{staff_id}"):
                            requests.put(f"{API_URL}/staff/{staff_id}", json={"status": "Đang làm việc"})
                            st.rerun()

                    if c_btn2.button("🗑️ Xóa vĩnh viễn", use_container_width=True, key=f"delete_{staff_id}"):
                        requests.delete(f"{API_URL}/staff/{staff_id}")
                        st.rerun()
        
        if len(filtered_df) > DISPLAY_LIMIT:
            st.caption(f"⚠️ Đang ẩn **{len(filtered_df) - DISPLAY_LIMIT}** kết quả khác để tránh quá tải. Hãy nhập tên chi tiết hơn để tìm chính xác người cần sửa.")

# --- THỐNG KÊ CHI TIẾT THEO ROLE ---
st.write("---")
if all_staff:
    st.subheader("📊 Phân bổ nhân sự")
    c1, c2, c3, c4 = st.columns(4)
    
    def count_role(role_name):
        return len([s for s in all_staff if s.get('role') == role_name])

    c1.metric("Giáo viên", count_role("teacher"))
    c2.metric("Vận hành", count_role("operator"))
    c3.metric("Phụ huynh", count_role("parent"))
    c4.metric("Quản trị viên", count_role("admin"))