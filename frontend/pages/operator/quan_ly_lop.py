import streamlit as st
import pandas as pd
import requests
import os
import time
from datetime import datetime

# ================= CRITICAL: CẤU HÌNH TRANG LUÔN ĐỂ ĐẦU FILE =================
st.set_page_config(page_title="Quản Lý Lớp Học", page_icon=None, layout="wide")

# ================= HÀM ĐỌC FILE CSS =================
def load_css(file_name):
    current_dir = os.path.dirname(os.path.abspath(__file__)) 
    css_root = os.path.abspath(os.path.join(current_dir, "../../CSS"))
    full_path = os.path.join(css_root, file_name)

    if os.path.exists(full_path):
        with open(full_path, "r", encoding="utf-8") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    else:
        st.warning(f"⚠️ Canh bao: Khong tim thay file CSS tai: {full_path}")

load_css("operator/operator_global.css")

API_URL = "http://localhost:8000"

# Lấy mã ngôn ngữ hiện hành từ session_state (Mặc định là "vi")
lang = st.session_state.get("lang", "vi")

# ==========================================
# BỘ TỪ ĐIỂN SONG NGỮ CHI TIẾT CHO QUAN_LY_LOP
# ==========================================
CLASS_LABELS = {
    "vi": {
        "title": "🏫 Quản Lý Lớp Học & Học Viên",
        "subtitle": "Tại đây, nhân viên vận hành có thể tạo lớp học mới, xếp học viên vào lớp, xem danh sách và chỉnh sửa/xóa các lớp hiện có.",
        "tab_create": "➕ Tạo Lớp Học Mới",
        "tab_manage": "⚙️ Quản Lý & Danh Sách Lớp",
        
        # Form Tạo Lớp
        "form_create_header": "Nhập thông tin lớp học",
        "input_name": "Tên lớp học (*)",
        "input_name_placeholder": "Ví dụ: Lớp Toán Tư Duy T7",
        "input_desc": "Ghi chú nội bộ",
        "input_teacher": "Giáo viên phụ trách (*)",
        "warn_no_teacher": "⚠️ Chưa có giáo viên hợp lệ. Hãy kiểm tra lại danh sách nhân sự.",
        "btn_create_submit": "🚀 Tạo Lớp Học Mới",
        "err_fields": "❌ Vui lòng điền đầy đủ các trường (*)",
        "success_created": "🎉 Đã tạo lớp thành công!",
        "err_backend": "Backend từ chối tạo lớp. Chi tiết lỗi:",
        "err_connection": "❌ Lỗi kết nối Backend:",
        
        # Quản lý lớp
        "select_class": "Chọn lớp để quản lý:",
        "header_manage": "Quản Lý Lớp:",
        "subtab_students": "👤 Danh Sách Học Viên",
        "subtab_edit": "✏️ Sửa Thông Tin Lớp",
        "subtab_delete": "🗑️ Xóa Lớp",
        
        # Danh sách học viên
        "lbl_teacher_assigned": "Giáo viên phụ trách:",
        "info_no_students": "Lớp học này hiện tại chưa có học sinh nào nhập học.",
        "btn_export": "📥 Tải Báo Cáo Học Viên (CSV)",
        "sub_remove_student": "#### Xóa học viên khỏi lớp này",
        "select_student_remove": "Chọn học sinh cần xóa:",
        "btn_remove_student": "Xác nhận xóa học sinh khỏi lớp",
        "success_removed_student": "✅ Đã rút học viên ra khỏi lớp thành công!",
        
        # Sửa & Xóa lớp
        "edit_name": "Tên lớp",
        "edit_desc": "Ghi chú",
        "edit_teacher": "Đổi Giáo viên",
        "btn_save_changes": "💾 Lưu Thay Đổi",
        "success_updated_class": "✅ Đã cập nhật thông tin lớp học!",
        "err_updated_class": "❌ Cập nhật thất bại. Vui lòng kiểm tra lại Backend.",
        "warn_delete": "⚠️ Hành động xóa lớp học là vĩnh viễn và không thể khôi phục dữ liệu!",
        "btn_delete_class": "💥 Xác nhận Xóa lớp học",
        "success_deleted_class": "🗑️ Đã xóa lớp học thành công khỏi hệ thống!"
    },
    "en": {
        "title": "🏫 Class & Student Management",
        "subtitle": "Operators can provision new classes, enroll students, view directories, and update or delete existing class registries.",
        "tab_create": "➕ Create New Class",
        "tab_manage": "⚙️ Manage & Class Directories",
        
        # Class Creation Form
        "form_create_header": "Enter Class Specifications",
        "input_name": "Class Name (*)",
        "input_name_placeholder": "e.g., Critical Thinking Math Sat",
        "input_desc": "Internal Staff Notes",
        "input_teacher": "Assigned Teacher (*)",
        "warn_no_teacher": "⚠️ No valid teachers found. Please verify the staff database registries.",
        "btn_create_submit": "🚀 Create New Class",
        "err_fields": "❌ Please fill in all required fields (*)",
        "success_created": "🎉 Class created successfully!",
        "err_backend": "Backend rejected class creation. Error log details:",
        "err_connection": "❌ Backend connection error occurred:",
        
        # Class Management Layout
        "select_class": "Select class to manage:",
        "header_manage": "Managing Class:",
        "subtab_students": "👤 Enrolled Students",
        "subtab_edit": "✏️ Modify Class Profile",
        "subtab_delete": "🗑️ Terminate Class",
        
        # Student Directory
        "lbl_teacher_assigned": "Instructor in charge:",
        "info_no_students": "There are currently no students enrolled in this class.",
        "btn_export": "📥 Export Student Directory (CSV)",
        "sub_remove_student": "#### Remove Student From Registry",
        "select_student_remove": "Select student to remove:",
        "btn_remove_student": "Confirm Student Removal",
        "success_removed_student": "✅ Student successfully un-enrolled from this class!",
        
        # Modify & Delete Class
        "edit_name": "Class Title",
        "edit_desc": "Notes / Metadata",
        "edit_teacher": "Reassign Teacher",
        "btn_save_changes": "💾 Save Profile Changes",
        "success_updated_class": "✅ Class specifications updated successfully!",
        "err_updated_class": "❌ Update failed. Please check the Backend system logs.",
        "warn_delete": "⚠️ Class deletion is permanent and all associated records will be un-recoverable!",
        "btn_delete_class": "💥 Confirm Class Termination",
        "success_deleted_class": "🗑️ Class successfully removed from the active system!"
    }
}

st.title(CLASS_LABELS[lang]["title"])
st.write(CLASS_LABELS[lang]["subtitle"])

# ================= HÀM LẤY DỮ LIỆU TỪ BACKEND =================
def get_teachers():
    try:
        headers = {"Authorization": f"Bearer {st.session_state.get('token', '')}"}
        res = requests.get(f"{API_URL}/api/auth/users", headers=headers, timeout=10)
        
        if res.status_code == 200:
            raw_data = res.json()
            valid_teachers = []
            
            for user in raw_data:
                role = str(user.get("role", user.get("quyen", ""))).lower()
                
                if "teacher" in role or "giáo viên" in role or "giao vien" in role:
                    status = str(user.get("status", user.get("trang_thai", "Đang làm việc")))
                    is_active = user.get("is_active", True)
                    
                    if status not in ["Nghỉ việc", "Vô hiệu hóa", "Nghi viec", "Vo hieu hoa"] and is_active is not False:
                        valid_teachers.append(user)
            
            return valid_teachers
        return []
    except: 
        return []

def get_classes():
    try:
        res_classes = requests.get(f"{API_URL}/classes", timeout=10)
        if res_classes.status_code == 200:
            data = res_classes.json()
            return [c for c in data if isinstance(c, dict)]
        return []
    except: return []

def get_all_students_from_db():
    try:
        res = requests.get(f"{API_URL}/api/auth/users", timeout=10) 
        if res.status_code == 200:
            return [s for s in res.json() if str(s.get("role")).lower() == "student"]
    except: pass
    return []

# ================= HIỂN THỊ LÊN GIAO DIỆN =================
teachers_data = get_teachers()
teacher_options = {}
if isinstance(teachers_data, list):
    for t in teachers_data:
        t_id = str(t.get("id", t.get("_id", "unknown")))
        t_name = t.get("name", t.get("full_name", "Không rõ tên" if lang == "vi" else "Unknown"))
        label = f"{t_name} ({t.get('email', '')})" if t.get('email') else t_name
        teacher_options[label] = {"id": t_id, "name": t_name}

tab_tao_lop, tab_danh_sach = st.tabs([CLASS_LABELS[lang]["tab_create"], CLASS_LABELS[lang]["tab_manage"]])

# --- TAB 1: TẠO LỚP HỌC MỚI ---
with tab_tao_lop:
    with st.container(border=True):
        st.subheader(CLASS_LABELS[lang]["form_create_header"])
        with st.form("tao_lop_form", clear_on_submit=True):
            c1, c2 = st.columns(2)
            with c1:
                class_name = st.text_input(CLASS_LABELS[lang]["input_name"], placeholder=CLASS_LABELS[lang]["input_name_placeholder"])
                description = st.text_area(CLASS_LABELS[lang]["input_desc"])
            with c2:
                if not teacher_options:
                    st.warning(CLASS_LABELS[lang]["warn_no_teacher"])
                    selected_teacher_label = None
                else:
                    selected_teacher_label = st.selectbox(CLASS_LABELS[lang]["input_teacher"], options=list(teacher_options.keys()))
            
            if st.form_submit_button(CLASS_LABELS[lang]["btn_create_submit"], type="primary", use_container_width=True):
                if not class_name or not selected_teacher_label:
                    st.error(CLASS_LABELS[lang]["err_fields"])
                else:
                    selected_teacher = teacher_options[selected_teacher_label]
                    payload = {
                        "class_name": class_name.strip(),
                        "subject": "Chưa xác định" if lang == "vi" else "Unassigned",
                        "teacher_id": selected_teacher["id"], 
                        "teacher_name": selected_teacher["name"],
                        "student_ids": [],
                        "is_public": False,
                        "description": description.strip(), 
                        "status": "active"
                    }
                    try:
                        res = requests.post(f"{API_URL}/classes/create", json=payload)
                        if res.status_code == 200:
                            st.success(f"{CLASS_LABELS[lang]['success_created']} '{class_name}'")
                            time.sleep(0.5); st.rerun()
                        else:
                            st.error(f"{CLASS_LABELS[lang]['err_backend']} {res.text}")
                    except Exception as e: 
                        st.error(f"{CLASS_LABELS[lang]['err_connection']} {e}")

# --- TAB 2: QUẢN LÝ LỚP HỌC ---
with tab_danh_sach:
    classes = get_classes()
    if not classes:
        st.info(CLASS_LABELS[lang]["no_products"])
    else:
        class_options_dict = {c.get("id", c.get("_id")): f"{c.get('class_name')}" for c in classes}
        selected_class_id = st.selectbox(CLASS_LABELS[lang]["select_class"], options=list(class_options_dict.keys()), format_func=lambda x: class_options_dict[x])
        
        if selected_class_id:
            sel = next((c for c in classes if c.get("id", c.get("_id")) == selected_class_id), None)
            if sel:
                st.markdown(f"### {CLASS_LABELS[lang]['header_manage']} `{sel.get('class_name')}`")
                
                sub_info, sub_edit, sub_del = st.tabs([CLASS_LABELS[lang]["subtab_students"], CLASS_LABELS[lang]["subtab_edit"], CLASS_LABELS[lang]["subtab_delete"]])
                
                # --- SUB TAB 1: DANH SÁCH HỌC VIÊN CỦA LỚP ---
                with sub_info:
                    st.write(f"**{CLASS_LABELS[lang]['lbl_teacher_assigned']}** {sel.get('teacher_name')}")
                    try:
                        res_st = requests.get(f"{API_URL}/classes/{selected_class_id}/students/details")
                        real_st = res_st.json() if res_st.status_code == 200 else []
                    except: real_st = []

                    if not real_st:
                        st.info(CLASS_LABELS[lang]["info_no_students"])
                    else:
                        df = pd.DataFrame(real_st)
                        if "STT" not in df.columns:
                            df.insert(0, 'STT', range(1, 1 + len(df)))
                            
                        # Đa ngôn ngữ nhãn tiêu đề cột của bảng danh sách
                        rename_dict = {
                            "STT": "No.",
                            "Mã HS": "Mã Học Viên" if lang == "vi" else "Student ID", 
                            "Tên Học Sinh": "Họ & Tên Học Sinh" if lang == "vi" else "Student Full Name",
                            "Tên Phụ Huynh": "Tên Phụ Huynh" if lang == "vi" else "Parent Name", 
                            "SĐT Liên Hệ": "SĐT Liên Hệ Phụ Huynh" if lang == "vi" else "Parent Phone Number",
                            "Tình trạng": "Trạng Thái" if lang == "vi" else "Status"
                        }
                        
                        # Fallback phòng hờ cấu trúc keys từ bên ngoài thâm nhập lạ
                        for col in df.columns:
                            if col not in rename_dict and col.lower() in ["id", "student_id"]: rename_dict[col] = "Mã Học Viên" if lang == "vi" else "Student ID"
                            if col not in rename_dict and col.lower() in ["name", "full_name"]: rename_dict[col] = "Họ & Tên Học Sinh" if lang == "vi" else "Student Full Name"
                            if col not in rename_dict and col.lower() in ["status"]: rename_dict[col] = "Trạng Thái" if lang == "vi" else "Status"

                        df_display = df.rename(columns={k: v for k, v in rename_dict.items() if k in df.columns})
                        
                        # Đổi tên các trường cột không cần thiết hiển thị thô ra ngoài nếu có
                        cols_to_show = [v for v in rename_dict.values() if v in df_display.columns]
                        if not cols_to_show: cols_to_show = df_display.columns.tolist()
                        
                        st.dataframe(df_display[cols_to_show], use_container_width=True, hide_index=True)
                        
                        current_date_str = datetime.now().strftime("%d%m%Y")
                        file_export_name = f"Danh_Sach_Lop_{sel.get('class_name').replace(' ', '_')}_{current_date_str}.csv"
                        st.download_button(CLASS_LABELS[lang]["btn_export"], data=df.to_csv(index=False).encode('utf-8-sig'), file_name=file_export_name, mime="text/csv", type="secondary")
                        
                        st.divider()
                        st.write(CLASS_LABELS[lang]["sub_remove_student"])
                        name_key = "Tên Học Sinh" if "Tên Học Sinh" in df.columns else (df.columns[2] if len(df.columns) > 2 else "name")
                        id_key = "Mã HS" if "Mã HS" in df.columns else (df.columns[1] if len(df.columns) > 1 else "id")
                        
                        st_dict = {r[id_key]: f"{r[id_key]} - {r[name_key]}" for r in real_st}
                        st_to_del = st.selectbox(CLASS_LABELS[lang]["select_student_remove"], options=list(st_dict.keys()), format_func=lambda x: st_dict[x], key="sb_del_st")
                        
                        if st.button(CLASS_LABELS[lang]["btn_remove_student"], type="primary"):
                            if requests.delete(f"{API_URL}/classes/{selected_class_id}/students/{st_to_del}").status_code == 200:
                                st.success(CLASS_LABELS[lang]["success_removed_student"])
                                time.sleep(0.5); st.rerun()

                # --- SUB TAB 2: SỬA THÔNG TIN LỚP ---
                with sub_edit:
                    with st.form(f"edit_{selected_class_id}"):
                        e1, e2 = st.columns(2)
                        with e1:
                            n_name = st.text_input(CLASS_LABELS[lang]["edit_name"], value=sel.get("class_name", ""))
                            n_desc = st.text_area(CLASS_LABELS[lang]["edit_desc"], value=sel.get("description", ""))
                        with e2:
                            t_labels = list(teacher_options.keys())
                            cur_t_id = sel.get("teacher_id")
                            def_idx = next((i for i, l in enumerate(t_labels) if teacher_options[l]["id"] == cur_t_id), 0) if t_labels else 0
                            n_t_label = st.selectbox(CLASS_LABELS[lang]["edit_teacher"], options=t_labels, index=def_idx) if t_labels else None

                        if st.form_submit_button(CLASS_LABELS[lang]["btn_save_changes"], type="primary", use_container_width=True):
                            if n_t_label:
                                sel_t = teacher_options[n_t_label]
                                upd = {
                                    "class_name": n_name.strip(),
                                    "teacher_id": sel_t["id"], 
                                    "teacher_name": sel_t["name"],
                                    "description": n_desc.strip()
                                }
                                if requests.put(f"{API_URL}/classes/{selected_class_id}", json=upd).status_code == 200:
                                    st.success(CLASS_LABELS[lang]["success_updated_class"])
                                    time.sleep(0.5); st.rerun()
                                else:
                                    st.error(CLASS_LABELS[lang]["err_updated_class"])

                # --- SUB TAB 3: XÓA LỚP VĨNH VIỄN ---
                with sub_del:
                    st.warning(CLASS_LABELS[lang]["warn_delete"])
                    if st.button(CLASS_LABELS[lang]["btn_delete_class"], type="primary", use_container_width=True):
                        if requests.delete(f"{API_URL}/classes/{selected_class_id}").status_code == 200:
                            st.success(CLASS_LABELS[lang]["success_deleted_class"])
                            time.sleep(0.5); st.rerun()