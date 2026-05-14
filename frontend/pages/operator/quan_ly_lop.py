import streamlit as st
import pandas as pd
import requests

st.set_page_config(page_title="Quản Lý Lớp Học", page_icon="🏫", layout="wide")

API_URL = "http://localhost:8000"

st.title("🏫 Quản Lý Lớp Học & Học Viên")
st.write("Tại đây, nhân viên vận hành có thể tạo lớp học mới, xem danh sách và chỉnh sửa/xóa các lớp hiện có.")

# ================= HÀM LẤY DỮ LIỆU =================
@st.cache_data(ttl=60)
def get_teachers():
    try:
        res = requests.get(f"{API_URL}/teachers", timeout=10)
        return res.json() if res.status_code == 200 else []
    except:
        return []

def get_classes():
    try:
        res_classes = requests.get(f"{API_URL}/classes", timeout=10)
        if res_classes.status_code == 200:
            data = res_classes.json()
            return [c for c in data if isinstance(c, dict)]
        return []
    except:
        return []

# Lấy dữ liệu chung cho toàn trang
teachers_data = get_teachers()
teacher_options = {}
if isinstance(teachers_data, list):
    for t in teachers_data:
        t_id = str(t.get("id", t.get("_id", "unknown")))
        t_name = t.get("name", "Không rõ tên")
        label = f"{t_name} ({t.get('email', '')})" if t.get('email') else t_name
        teacher_options[label] = {"id": t_id, "name": t_name}

tab_tao_lop, tab_danh_sach = st.tabs(["➕ Tạo lớp học mới", "📋 Quản lý & Danh sách lớp"])

# ================= TAB 1: TẠO LỚP HỌC MỚI =================
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
                
            is_public = st.checkbox("Mở lớp (Cho phép phụ huynh thấy và đăng ký trên hệ thống)", value=True)
            description = st.text_area("Ghi chú nội bộ")
            
            if st.form_submit_button("Tạo Lớp Học Mới", type="primary"):
                if not class_name or not subject or not selected_teacher_label:
                    st.error("⚠️ Vui lòng điền đầy đủ các trường có dấu (*)")
                else:
                    selected_teacher = teacher_options[selected_teacher_label]
                    payload = {
                        "class_name": class_name,
                        "subject": subject,
                        "teacher_id": selected_teacher["id"],
                        "teacher_name": selected_teacher["name"],
                        "student_ids": [],
                        "is_public": is_public,
                        "description": description,
                        "status": "active"
                    }
                    try:
                        res = requests.post(f"{API_URL}/classes/create", json=payload)
                        if res.status_code == 200:
                            st.success(f"✅ Đã tạo lớp '{class_name}' thành công!")
                            st.balloons()
                            st.rerun()
                        else:
                            st.error(f"❌ Lỗi từ Backend: {res.text}")
                    except Exception as e:
                        st.error(f"❌ Lỗi kết nối Backend: {e}")

# ================= TAB 2: QUẢN LÝ LỚP HỌC (SỬA/XÓA/XEM) =================
with tab_danh_sach:
    classes = get_classes()

    if not classes:
        st.info("💡 Hiện tại chưa có lớp học nào trong hệ thống.")
    else:
        # Tạo danh sách chọn lớp
        class_options_dict = {
            c.get("id", c.get("_id")): f"{c.get('class_name', 'Lớp chưa rõ tên')} - {c.get('subject', '')}"
            for c in classes
        }
        
        selected_class_id = st.selectbox(
            "🔎 Chọn lớp học để quản lý:", 
            options=list(class_options_dict.keys()), 
            format_func=lambda x: class_options_dict[x]
        )
        
        if selected_class_id:
            selected_class_data = next((c for c in classes if c.get("id", c.get("_id")) == selected_class_id), None)
            
            if selected_class_data:
                st.markdown(f"### 🏫 Quản lý: `{selected_class_data.get('class_name')}`")
                
                # CHIA LÀM 3 TAB CON: THÔNG TIN - SỬA - XÓA
                sub_tab_info, sub_tab_edit, sub_tab_del = st.tabs(["📋 Danh sách Học viên", "✏️ Chỉnh sửa thông tin", "🗑️ Xóa lớp"])
                
                # --- SUB TAB 1: THÔNG TIN HỌC VIÊN ---
                with sub_tab_info:
                    st.write(f"**Môn học:** {selected_class_data.get('subject')} | **Giáo viên:** {selected_class_data.get('teacher_name')}")
                    student_count = len(selected_class_data.get("student_ids", []))
                    st.caption(f"Sĩ số lớp hiện tại: {student_count} học sinh")
                    
                    # 1. GỌI API LẤY DỮ LIỆU THỰC TỪ BACKEND
                    try:
                        res_students = requests.get(f"{API_URL}/classes/{selected_class_id}/students/details")
                        if res_students.status_code == 200 and res_students.json():
                            real_student_data = res_students.json()
                        else:
                            real_student_data = []
                    except:
                        real_student_data = []

                    # 2. HIỂN THỊ LÊN BẢNG EXCEL VÀ CHỨC NĂNG XÓA
                    if not real_student_data:
                        st.info("💡 Lớp học này hiện tại chưa có học sinh nào đăng ký.")
                        df = pd.DataFrame(columns=["Mã HS", "Tên Học Sinh", "Tên Phụ Huynh", "SĐT Liên Hệ", "Tình trạng"])
                        st.dataframe(df, use_container_width=True)
                    else:
                        df = pd.DataFrame(real_student_data)
                        st.dataframe(df, use_container_width=True)
                        
                        st.download_button(
                            label="📥 Xuất danh sách Excel (CSV)",
                            data=df.to_csv(index=False).encode('utf-8-sig'),
                            file_name=f"danh_sach_lop_{selected_class_data.get('class_name')}.csv",
                            mime="text/csv"
                        )
                        
                        st.markdown("---")
                        st.write("#### 🛠️ Quản lý & Xóa học viên")
                        
                        # Tạo danh sách chọn học sinh để xóa
                        student_dict = {row["Mã HS"]: f"Mã: {row['Mã HS']} - Tên: {row['Tên Học Sinh']}" for row in real_student_data}
                        selected_student_to_remove = st.selectbox(
                            "Chọn học sinh cần xóa khỏi lớp:", 
                            options=list(student_dict.keys()), 
                            format_func=lambda x: student_dict[x]
                        )
                        
                        if st.button("🗑️ Xóa học sinh này", type="primary"):
                            try:
                                res_remove = requests.delete(f"{API_URL}/classes/{selected_class_id}/students/{selected_student_to_remove}")
                                if res_remove.status_code == 200:
                                    st.success("✅ Đã xóa học sinh khỏi lớp thành công!")
                                    st.rerun()
                                else:
                                    st.error("❌ Không thể xóa học sinh. Vui lòng thử lại.")
                            except Exception as e:
                                st.error(f"❌ Lỗi kết nối Backend: {e}")

                # --- SUB TAB 2: CHỈNH SỬA LỚP ---
                with sub_tab_edit:
                    with st.form(f"edit_form_{selected_class_id}"):
                        st.info("Cập nhật lại thông tin của lớp học này.")
                        e1, e2 = st.columns(2)
                        with e1:
                            new_class_name = st.text_input("Tên lớp", value=selected_class_data.get("class_name", ""))
                            new_subject = st.text_input("Môn học", value=selected_class_data.get("subject", ""))
                        with e2:
                            current_teacher_id = selected_class_data.get("teacher_id")
                            default_index = 0
                            teacher_labels = list(teacher_options.keys())
                            for i, label in enumerate(teacher_labels):
                                if teacher_options[label]["id"] == current_teacher_id:
                                    default_index = i
                                    break
                            
                            new_teacher_label = st.selectbox("Đổi Giáo viên", options=teacher_labels, index=default_index)
                            
                        new_is_public = st.checkbox("Mở đăng ký công khai", value=selected_class_data.get("is_public", True))
                        new_desc = st.text_area("Ghi chú", value=selected_class_data.get("description", ""))

                        if st.form_submit_button("💾 Lưu Thay Đổi", type="primary"):
                            selected_teacher = teacher_options[new_teacher_label]
                            update_payload = {
                                "class_name": new_class_name,
                                "subject": new_subject,
                                "teacher_id": selected_teacher["id"],
                                "teacher_name": selected_teacher["name"],
                                "is_public": new_is_public,
                                "description": new_desc
                            }
                            res_update = requests.put(f"{API_URL}/classes/{selected_class_id}", json=update_payload)
                            if res_update.status_code == 200:
                                st.success("Cập nhật thành công!")
                                st.rerun()
                            else:
                                st.error("Có lỗi xảy ra khi cập nhật.")

                # --- SUB TAB 3: XÓA LỚP ---
                with sub_tab_del:
                    st.warning("⚠️ Hành động này sẽ xóa vĩnh viễn lớp học này khỏi hệ thống. Nếu lớp đã có lịch học hoặc học sinh, vui lòng cân nhắc kỹ trước khi xóa.")
                    if st.button("🗑️ Xác nhận Xóa lớp học này", type="primary"):
                        res_del = requests.delete(f"{API_URL}/classes/{selected_class_id}")
                        if res_del.status_code == 200:
                            st.success("Đã xóa lớp học thành công!")
                            st.rerun()
                        else:
                            st.error("Không thể xóa lớp học này.")