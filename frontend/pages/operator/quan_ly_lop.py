import streamlit as st
import pandas as pd
import requests
import os
import time
from datetime import datetime

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
        st.warning(f"Canh bao: Khong tim thay file CSS tai: {full_path}")

load_css("operator/quan_ly_lop.css")

API_URL = "http://localhost:8000"

st.title("Quản Lý Lớp Học & Học Viên")
st.write("Tại đây, nhân viên vận hành có thể tạo lớp học mới, xếp học viên vào lớp, xem danh sách và chỉnh sửa/xóa các lớp hiện có.")

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
        t_name = t.get("name", t.get("full_name", "Không rõ tên"))
        label = f"{t_name} ({t.get('email', '')})" if t.get('email') else t_name
        teacher_options[label] = {"id": t_id, "name": t_name}

tab_tao_lop, tab_danh_sach = st.tabs(["Tạo Lớp Học Mới", "Quản Lý & Danh Sách Lớp"])

# --- TAB 1: TẠO LỚP HỌC MỚI ---
with tab_tao_lop:
    with st.container(border=True):
        st.subheader("Nhập thông tin lớp học")
        with st.form("tao_lop_form", clear_on_submit=True):
            c1, c2 = st.columns(2)
            with c1:
                class_name = st.text_input("Tên lớp học (*)", placeholder="Ví dụ: Lớp Toán Tư Duy T7")
                description = st.text_area("Ghi chú nội bộ")
            with c2:
                if not teacher_options:
                    st.warning("Chưa có giáo viên hợp lệ. Hãy kiểm tra lại danh sách nhân sự.")
                    selected_teacher_label = None
                else:
                    selected_teacher_label = st.selectbox("Giáo viên phụ trách (*)", options=list(teacher_options.keys()))
            
            if st.form_submit_button("Tạo Lớp Học Mới", type="primary", use_container_width=True):
                if not class_name or not selected_teacher_label:
                    st.error("Vui lòng điền đầy đủ các trường (*)")
                else:
                    selected_teacher = teacher_options[selected_teacher_label]
                    payload = {
                        "class_name": class_name,
                        "subject": "Chưa xác định", # Fix lỗi 422: Gửi kèm để thỏa mãn Backend
                        "teacher_id": selected_teacher["id"], 
                        "teacher_name": selected_teacher["name"],
                        "student_ids": [],
                        "is_public": False, # Fix lỗi 422: Gửi kèm để thỏa mãn Backend
                        "description": description, 
                        "status": "active"
                    }
                    try:
                        res = requests.post(f"{API_URL}/classes/create", json=payload)
                        if res.status_code == 200:
                            st.success(f"Đã tạo lớp '{class_name}' thành công!")
                            time.sleep(0.5); st.rerun()
                        else:
                            st.error(f"Backend từ chối tạo lớp. Chi tiết lỗi: {res.text}")
                    except Exception as e: 
                        st.error(f"Lỗi kết nối Backend: {e}")

# --- TAB 2: QUẢN LÝ LỚP HỌC ---
with tab_danh_sach:
    classes = get_classes()
    if not classes:
        st.info("Hiện tại chưa có lớp học nào được tạo.")
    else:
        class_options_dict = {c.get("id", c.get("_id")): f"{c.get('class_name')}" for c in classes}
        selected_class_id = st.selectbox("Chọn lớp để quản lý:", options=list(class_options_dict.keys()), format_func=lambda x: class_options_dict[x])
        
        if selected_class_id:
            sel = next((c for c in classes if c.get("id", c.get("_id")) == selected_class_id), None)
            if sel:
                st.markdown(f"### Quản Lý Lớp: `{sel.get('class_name')}`")
                
                sub_info, sub_edit, sub_del = st.tabs(["Danh Sách Học Viên", "Sửa Thông Tin Lớp", "Xóa Lớp"])
                
                # --- SUB TAB 1: DANH SÁCH HỌC VIÊN CỦA LỚP ---
                with sub_info:
                    st.write(f"**Giáo viên phụ trách:** {sel.get('teacher_name')}")
                    try:
                        res_st = requests.get(f"{API_URL}/classes/{selected_class_id}/students/details")
                        real_st = res_st.json() if res_st.status_code == 200 else []
                    except: real_st = []

                    if not real_st:
                        st.info("Lớp học này hiện tại chưa có học sinh nào nhập học.")
                    else:
                        df = pd.DataFrame(real_st)
                        if "STT" not in df.columns:
                            df.insert(0, 'STT', range(1, 1 + len(df)))
                            
                        rename_dict = {
                            "Mã HS": "Mã Học Viên", "Tên Học Sinh": "Họ & Tên Học Sinh",
                            "Tên Phụ Huynh": "Tên Phụ Huynh", "SĐT Liên Hệ": "SĐT Liên Hệ Phụ Huynh",
                            "Tình trạng": "Trạng Thái"
                        }
                        df_display = df.rename(columns={k: v for k, v in rename_dict.items() if k in df.columns})
                        st.dataframe(df_display, use_container_width=True, hide_index=True)
                        
                        current_date_str = datetime.now().strftime("%d%m%Y")
                        file_export_name = f"Danh_Sach_Lop_{sel.get('class_name').replace(' ', '_')}_{current_date_str}.csv"
                        st.download_button("Tải Báo Cáo Học Viên (CSV)", data=df.to_csv(index=False).encode('utf-8-sig'), file_name=file_export_name, mime="text/csv", type="secondary")
                        
                        st.divider()
                        st.write("#### Xóa học viên khỏi lớp này")
                        name_key = "Tên Học Sinh" if "Tên Học Sinh" in df.columns else df.columns[2] if len(df.columns) > 2 else "name"
                        id_key = "Mã HS" if "Mã HS" in df.columns else df.columns[1] if len(df.columns) > 1 else "id"
                        
                        st_dict = {r[id_key]: f"{r[id_key]} - {r[name_key]}" for r in real_st}
                        st_to_del = st.selectbox("Chọn học sinh cần xóa:", options=list(st_dict.keys()), format_func=lambda x: st_dict[x], key="sb_del_st")
                        
                        if st.button("Xác nhận xóa học sinh khỏi lớp", type="primary"):
                            if requests.delete(f"{API_URL}/classes/{selected_class_id}/students/{st_to_del}").status_code == 200:
                                st.success("Đã rút học viên ra khỏi lớp thành công!")
                                time.sleep(0.5); st.rerun()

                # --- SUB TAB 2: SỬA THÔNG TIN LỚP ---
                with sub_edit:
                    with st.form(f"edit_{selected_class_id}"):
                        e1, e2 = st.columns(2)
                        with e1:
                            n_name = st.text_input("Tên lớp", value=sel.get("class_name", ""))
                            n_desc = st.text_area("Ghi chú", value=sel.get("description", ""))
                        with e2:
                            t_labels = list(teacher_options.keys())
                            cur_t_id = sel.get("teacher_id")
                            def_idx = next((i for i, l in enumerate(t_labels) if teacher_options[l]["id"] == cur_t_id), 0) if t_labels else 0
                            n_t_label = st.selectbox("Đổi Giáo viên", options=t_labels, index=def_idx) if t_labels else None

                        if st.form_submit_button("Lưu Thay Đổi", type="primary", use_container_width=True):
                            if n_t_label:
                                sel_t = teacher_options[n_t_label]
                                upd = {
                                    "class_name": n_name,
                                    "teacher_id": sel_t["id"], 
                                    "teacher_name": sel_t["name"],
                                    "description": n_desc
                                }
                                if requests.put(f"{API_URL}/classes/{selected_class_id}", json=upd).status_code == 200:
                                    st.success("Đã cập nhật thông tin lớp học!")
                                    time.sleep(0.5); st.rerun()
                                else:
                                    st.error("Cập nhật thất bại. Vui lòng kiểm tra lại Backend.")

                # --- SUB TAB 3: XÓA LỚP ---
                with sub_del:
                    st.warning("Hành động xóa lớp học là vĩnh viễn và không thể khôi phục dữ liệu!")
                    if st.button("Xác nhận Xóa lớp học", type="primary", use_container_width=True):
                        if requests.delete(f"{API_URL}/classes/{selected_class_id}").status_code == 200:
                            st.success("Đã xóa lớp học thành công khỏi hệ thống!")
                            time.sleep(0.5); st.rerun()