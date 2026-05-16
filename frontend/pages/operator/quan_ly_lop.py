import streamlit as st
import pandas as pd
import requests
import os

st.set_page_config(page_title="Quản Lý Lớp Học", page_icon="🏫", layout="wide")

# ================= HÀM ĐỌC FILE CSS (SỬA LỖI ĐƯỜNG DẪN) =================
def load_css(file_name):
    """Tự động tìm file CSS trong thư mục frontend/CSS/"""
    current_dir = os.path.dirname(os.path.abspath(__file__)) # pages/operator
    css_root = os.path.abspath(os.path.join(current_dir, "../../CSS"))
    full_path = os.path.join(css_root, file_name)

    if os.path.exists(full_path):
        with open(full_path, "r", encoding="utf-8") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    else:
        st.warning(f"⚠️ Không tìm thấy file CSS tại: {full_path}")

# Tải CSS làm đẹp
load_css("operator/quan_ly_lop.css")

API_URL = "http://localhost:8000"

st.title(" Quản Lý Lớp Học & Học Viên")
st.write("Tại đây, nhân viên vận hành có thể tạo lớp học mới, xem danh sách và chỉnh sửa/xóa các lớp hiện có.")

# ================= HÀM LẤY DỮ LIỆU =================
@st.cache_data(ttl=60)
def get_teachers():
    try:
        res = requests.get(f"{API_URL}/teachers", timeout=10)
        return res.json() if res.status_code == 200 else []
    except: return []

def get_classes():
    try:
        res_classes = requests.get(f"{API_URL}/classes", timeout=10)
        if res_classes.status_code == 200:
            data = res_classes.json()
            return [c for c in data if isinstance(c, dict)]
        return []
    except: return []

teachers_data = get_teachers()
teacher_options = {}
if isinstance(teachers_data, list):
    for t in teachers_data:
        t_id = str(t.get("id", t.get("_id", "unknown")))
        t_name = t.get("name", "Không rõ tên")
        label = f"{t_name} ({t.get('email', '')})" if t.get('email') else t_name
        teacher_options[label] = {"id": t_id, "name": t_name}

tab_tao_lop, tab_danh_sach = st.tabs([" Tạo Lớp Học Mới", " Quản Lý & Danh Sách Lớp"])

# --- TAB 1: TẠO LỚP HỌC MỚI ---
with tab_tao_lop:
    with st.container(border=True):
        st.subheader("Nhập thông tin lớp học")
        with st.form("tao_lop_form", clear_on_submit=True):
            c1, c2 = st.columns(2)
            with c1:
                class_name = st.text_input("Tên lớp học (*)", placeholder="Ví dụ: Lớp Toán Tư Duy T7")
                subject = st.text_input("Môn học (*)")
            with c2:
                if not teacher_options:
                    st.warning("⚠️ Chưa có giáo viên. Hãy thêm nhân sự trước.")
                    selected_teacher_label = None
                else:
                    selected_teacher_label = st.selectbox("Giáo viên phụ trách (*)", options=list(teacher_options.keys()))
                
            is_public = st.checkbox("Mở lớp (Công khai cho phụ huynh đăng ký)", value=True)
            description = st.text_area("Ghi chú nội bộ")
            
            if st.form_submit_button("Tạo Lớp Học Mới", type="primary", use_container_width=True):
                if not class_name or not subject or not selected_teacher_label:
                    st.error("⚠️ Vui lòng điền đầy đủ các trường (*)")
                else:
                    selected_teacher = teacher_options[selected_teacher_label]
                    payload = {
                        "class_name": class_name, "subject": subject,
                        "teacher_id": selected_teacher["id"], "teacher_name": selected_teacher["name"],
                        "student_ids": [], "is_public": is_public,
                        "description": description, "status": "active"
                    }
                    try:
                        res = requests.post(f"{API_URL}/classes/create", json=payload)
                        if res.status_code == 200:
                            st.success(f"Đã tạo lớp '{class_name}' thành công!")
                            st.balloons(); st.rerun()
                    except: st.error("❌ Lỗi kết nối Backend")

# --- TAB 2: QUẢN LÝ LỚP HỌC ---
with tab_danh_sach:
    classes = get_classes()
    if not classes:
        st.info("💡 Hiện tại chưa có lớp học nào.")
    else:
        class_options_dict = {c.get("id", c.get("_id")): f"{c.get('class_name')} - {c.get('subject')}" for c in classes}
        selected_class_id = st.selectbox("Chọn lớp để quản lý:", options=list(class_options_dict.keys()), format_func=lambda x: class_options_dict[x])
        
        if selected_class_id:
            sel = next((c for c in classes if c.get("id", c.get("_id")) == selected_class_id), None)
            if sel:
                st.markdown(f"###  Quản Lý: `{sel.get('class_name')}`")
                sub_info, sub_edit, sub_del = st.tabs([" Học Viên", " Sửa Lớp", " Xóa Lớp"])
                
                with sub_info:
                    st.write(f"**Môn:** {sel.get('subject')} | **GV:** {sel.get('teacher_name')}")
                    try:
                        res_st = requests.get(f"{API_URL}/classes/{selected_class_id}/students/details")
                        real_st = res_st.json() if res_st.status_code == 200 else []
                    except: real_st = []

                    if not real_st:
                        st.info(" Lớp chưa có học sinh.")
                    else:
                        df = pd.DataFrame(real_st)
                        st.dataframe(df, use_container_width=True, hide_index=True)
                        st.download_button(" Tải Excel (CSV)", data=df.to_csv(index=False).encode('utf-8-sig'), file_name=f"lop_{sel.get('class_name')}.csv", mime="text/csv")
                        
                        st.divider()
                        st.write("####  Xóa học viên khỏi lớp")
                        st_dict = {r["Mã HS"]: f"{r['Mã HS']} - {r['Tên Học Sinh']}" for r in real_st}
                        st_to_del = st.selectbox("Chọn học sinh:", options=list(st_dict.keys()), format_func=lambda x: st_dict[x])
                        if st.button(" Xóa học sinh này", type="primary"):
                            if requests.delete(f"{API_URL}/classes/{selected_class_id}/students/{st_to_del}").status_code == 200:
                                st.success("Đã xóa học sinh!"); st.rerun()

                with sub_edit:
                    with st.form(f"edit_{selected_class_id}"):
                        e1, e2 = st.columns(2)
                        with e1:
                            n_name = st.text_input("Tên lớp", value=sel.get("class_name", ""))
                            n_sub = st.text_input("Môn học", value=sel.get("subject", ""))
                        with e2:
                            t_labels = list(teacher_options.keys())
                            cur_t_id = sel.get("teacher_id")
                            def_idx = next((i for i, l in enumerate(t_labels) if teacher_options[l]["id"] == cur_t_id), 0)
                            n_t_label = st.selectbox("Đổi Giáo viên", options=t_labels, index=def_idx)
                        
                        n_pub = st.checkbox("Mở đăng ký", value=sel.get("is_public", True))
                        n_desc = st.text_area("Ghi chú", value=sel.get("description", ""))

                        if st.form_submit_button(" Lưu Thay Đổi", type="primary", use_container_width=True):
                            sel_t = teacher_options[n_t_label]
                            upd = {"class_name": n_name, "subject": n_sub, "teacher_id": sel_t["id"], "teacher_name": sel_t["name"], "is_public": n_pub, "description": n_desc}
                            if requests.put(f"{API_URL}/classes/{selected_class_id}", json=upd).status_code == 200:
                                st.success("Đã cập nhật!"); st.rerun()

                with sub_del:
                    st.warning("⚠️ Hành động xóa lớp học là vĩnh viễn!")
                    if st.button(" Xác nhận Xóa lớp học", type="primary", use_container_width=True):
                        if requests.delete(f"{API_URL}/classes/{selected_class_id}").status_code == 200:
                            st.success("Đã xóa lớp!"); st.rerun()