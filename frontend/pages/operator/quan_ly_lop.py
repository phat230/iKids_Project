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
        st.warning(f"Cảnh báo: Không tìm thấy file CSS tại: {full_path}")


load_css("operator/operator_global.css")

API_URL = st.session_state.get("api_url", "http://localhost:8000")
TV1_API = f"{API_URL}/api/tv1"
API_AUTH = f"{API_URL}/api/auth"

lang = st.session_state.get("lang", "vi")
token = st.session_state.get("token") or st.session_state.get("access_token") or ""


# ==========================================
# BỘ TỪ ĐIỂN SONG NGỮ
# ==========================================
CLASS_LABELS = {
    "vi": {
        "title": "Quản Lý Lớp Học & Học Viên",
        "subtitle": "Tạo lớp học, cấu hình học phí, quản lý học viên và chỉnh sửa/xóa lớp.",
        "tab_create": "Tạo Lớp Học Mới",
        "tab_manage": "Quản Lý & Danh Sách Lớp",

        "form_create_header": "Nhập thông tin lớp học",
        "section_basic": "Thông tin cơ bản",
        "section_tuition": "Cấu hình học phí",
        "input_name": "Tên lớp học (*)",
        "input_name_placeholder": "Ví dụ: Lớp Toán Tư Duy T7",
        "input_subject": "Môn học (*)",
        "input_subject_placeholder": "Ví dụ: Toán tư duy",
        "input_desc": "Ghi chú nội bộ",
        "input_teacher": "Giáo viên phụ trách (*)",
        "input_public": "Cho phép phụ huynh nhìn thấy và đăng ký lớp này",
        "input_status": "Trạng thái lớp",
        "input_tuition_enabled": "Bật học phí cho lớp này",
        "registration_fee": "Phí đăng ký / ghi danh",
        "monthly_fee": "Học phí theo tháng",
        "cycle_fee": "Học phí theo chu kỳ",
        "cycle_months": "Số tháng / chu kỳ",
        "yearly_fee": "Học phí cả năm",
        "billing_day": "Ngày đến hạn đóng tiền hằng tháng",
        "grace_days": "Số ngày cho phép trễ hạn",
        "allow_registration_fee": "Cho phép thu phí đăng ký",
        "allow_monthly": "Cho phép đóng theo tháng",
        "allow_cycle": "Cho phép đóng theo chu kỳ",
        "allow_yearly": "Cho phép đóng cả năm",
        "tuition_note": "Ghi chú học phí",
        "warn_no_teacher": "Chưa có giáo viên hợp lệ. Hãy kiểm tra lại danh sách nhân sự.",
        "btn_create_submit": "Tạo Lớp Học Mới",
        "err_fields": "Vui lòng điền đầy đủ các trường (*)",
        "success_created": "Đã tạo lớp thành công!",
        "err_backend": "Backend từ chối tạo lớp. Chi tiết lỗi:",
        "err_connection": "Lỗi kết nối Backend:",

        "select_class": "Chọn lớp để quản lý:",
        "header_manage": "Quản Lý Lớp:",
        "subtab_students": "Danh Sách Học Viên",
        "subtab_edit": "Sửa Thông Tin Lớp",
        "subtab_delete": "Xóa Lớp",

        "lbl_teacher_assigned": "Giáo viên phụ trách:",
        "lbl_subject": "Môn học:",
        "lbl_public": "Công khai:",
        "lbl_status": "Trạng thái:",
        "lbl_tuition": "Học phí:",
        "info_no_students": "Lớp học này hiện tại chưa có học sinh nào nhập học.",
        "btn_export": "Tải Báo Cáo Học Viên (CSV)",
        "sub_remove_student": "#### Xóa học viên khỏi lớp này",
        "select_student_remove": "Chọn học sinh cần xóa:",
        "btn_remove_student": "Xác nhận xóa học sinh khỏi lớp",
        "success_removed_student": "Đã rút học viên ra khỏi lớp thành công!",

        "edit_name": "Tên lớp",
        "edit_subject": "Môn học",
        "edit_desc": "Ghi chú",
        "edit_teacher": "Đổi Giáo viên",
        "btn_save_changes": "Lưu Thay Đổi",
        "success_updated_class": "Đã cập nhật thông tin lớp học!",
        "err_updated_class": "Cập nhật thất bại. Vui lòng kiểm tra lại Backend.",
        "warn_delete": "Hành động xóa lớp học là vĩnh viễn và không thể khôi phục dữ liệu!",
        "btn_delete_class": "Xác nhận Xóa lớp học",
        "success_deleted_class": "Đã xóa lớp học thành công khỏi hệ thống!",
        "yes": "Có",
        "no": "Không",
    },
    "en": {
        "title": "Class & Student Management",
        "subtitle": "Create classes, configure tuition, manage students, and update/delete class registries.",
        "tab_create": "Create New Class",
        "tab_manage": "Manage & Class Directories",

        "form_create_header": "Enter Class Specifications",
        "section_basic": "Basic Information",
        "section_tuition": "Tuition Configuration",
        "input_name": "Class Name (*)",
        "input_name_placeholder": "e.g., Critical Thinking Math Sat",
        "input_subject": "Subject (*)",
        "input_subject_placeholder": "e.g., Critical Thinking Math",
        "input_desc": "Internal Staff Notes",
        "input_teacher": "Assigned Teacher (*)",
        "input_public": "Allow parents to see and register this class",
        "input_status": "Class Status",
        "input_tuition_enabled": "Enable tuition for this class",
        "registration_fee": "Registration Fee",
        "monthly_fee": "Monthly Tuition",
        "cycle_fee": "Cycle Tuition",
        "cycle_months": "Months / Cycle",
        "yearly_fee": "Yearly Tuition",
        "billing_day": "Monthly Due Day",
        "grace_days": "Grace Days",
        "allow_registration_fee": "Allow registration fee",
        "allow_monthly": "Allow monthly payment",
        "allow_cycle": "Allow cycle payment",
        "allow_yearly": "Allow yearly payment",
        "tuition_note": "Tuition Note",
        "warn_no_teacher": "No valid teachers found. Please verify the staff database.",
        "btn_create_submit": "Create New Class",
        "err_fields": "Please fill in all required fields (*)",
        "success_created": "Class created successfully!",
        "err_backend": "Backend rejected class creation. Error details:",
        "err_connection": "Backend connection error occurred:",

        "select_class": "Select class to manage:",
        "header_manage": "Managing Class:",
        "subtab_students": "Enrolled Students",
        "subtab_edit": "Modify Class Profile",
        "subtab_delete": "Terminate Class",

        "lbl_teacher_assigned": "Instructor in charge:",
        "lbl_subject": "Subject:",
        "lbl_public": "Public:",
        "lbl_status": "Status:",
        "lbl_tuition": "Tuition:",
        "info_no_students": "There are currently no students enrolled in this class.",
        "btn_export": "Export Student Directory (CSV)",
        "sub_remove_student": "#### Remove Student From Registry",
        "select_student_remove": "Select student to remove:",
        "btn_remove_student": "Confirm Student Removal",
        "success_removed_student": "Student successfully un-enrolled from this class!",

        "edit_name": "Class Title",
        "edit_subject": "Subject",
        "edit_desc": "Notes / Metadata",
        "edit_teacher": "Reassign Teacher",
        "btn_save_changes": "Save Profile Changes",
        "success_updated_class": "Class specifications updated successfully!",
        "err_updated_class": "Update failed. Please check Backend logs.",
        "warn_delete": "Class deletion is permanent and all associated records will be unrecoverable!",
        "btn_delete_class": "Confirm Class Termination",
        "success_deleted_class": "Class successfully removed from the active system!",
        "yes": "Yes",
        "no": "No",
    },
}


# ================= HÀM TIỆN ÍCH =================
def get_headers():
    return {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }


def to_float(value, default=0.0):
    try:
        if value is None:
            return default
        return float(value)
    except Exception:
        return default


def to_int(value, default=0):
    try:
        if value is None:
            return default
        return int(value)
    except Exception:
        return default


def format_money(value):
    try:
        return f"{float(value):,.0f} VNĐ"
    except Exception:
        return "0 VNĐ"


def bool_text(value):
    return CLASS_LABELS[lang]["yes"] if value else CLASS_LABELS[lang]["no"]


# ================= HÀM LẤY DỮ LIỆU BACKEND =================
def get_teachers():
    headers = get_headers()

    try:
        res = requests.get(f"{TV1_API}/teachers", headers=headers, timeout=10)
        if res.status_code == 200:
            data = res.json()
            if isinstance(data, list):
                return data
    except Exception:
        pass

    try:
        res = requests.get(f"{API_AUTH}/users", headers=headers, timeout=10)
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
    except Exception:
        pass

    return []


def get_classes():
    try:
        res_classes = requests.get(
            f"{TV1_API}/classes",
            headers=get_headers(),
            timeout=10,
        )

        if res_classes.status_code == 200:
            data = res_classes.json()
            return [c for c in data if isinstance(c, dict)]

        return []
    except Exception:
        return []


def build_class_payload(
    class_name,
    subject,
    teacher_id,
    teacher_name,
    description,
    is_public,
    status,
    tuition_enabled,
    registration_fee,
    monthly_fee,
    cycle_fee,
    cycle_months,
    yearly_fee,
    billing_day,
    grace_days,
    allow_registration_fee,
    allow_monthly_payment,
    allow_cycle_payment,
    allow_yearly_payment,
    tuition_note,
):
    return {
        "class_name": class_name.strip(),
        "subject": subject.strip(),
        "teacher_id": teacher_id,
        "teacher_name": teacher_name,
        "student_ids": [],
        "is_public": bool(is_public),
        "description": description.strip(),
        "status": status,
        "tuition_enabled": bool(tuition_enabled),
        "registration_fee": float(registration_fee or 0),
        "monthly_fee": float(monthly_fee or 0),
        "cycle_fee": float(cycle_fee or 0),
        "cycle_months": int(cycle_months or 3),
        "yearly_fee": float(yearly_fee or 0),
        "allow_registration_fee": bool(allow_registration_fee),
        "allow_monthly_payment": bool(allow_monthly_payment),
        "allow_cycle_payment": bool(allow_cycle_payment),
        "allow_yearly_payment": bool(allow_yearly_payment),
        "billing_day": int(billing_day or 5),
        "grace_days": int(grace_days or 3),
        "reminder_days_before": [7, 3, 0, -1],
        "currency": "VND",
        "tuition_note": tuition_note.strip(),
    }


# ================= HEADER =================
st.title(CLASS_LABELS[lang]["title"])
st.caption(CLASS_LABELS[lang]["subtitle"])

teachers_data = get_teachers()
teacher_options = {}

if isinstance(teachers_data, list):
    for t in teachers_data:
        t_id = str(t.get("id", t.get("_id", "unknown")))
        t_name = t.get("name", t.get("full_name", "Không rõ tên" if lang == "vi" else "Unknown"))
        label = f"{t_name} ({t.get('email', '')})" if t.get("email") else t_name
        teacher_options[label] = {
            "id": t_id,
            "name": t_name,
        }


tab_tao_lop, tab_danh_sach = st.tabs([
    CLASS_LABELS[lang]["tab_create"],
    CLASS_LABELS[lang]["tab_manage"],
])


# =========================================================
# TAB 1: TẠO LỚP HỌC MỚI
# =========================================================
with tab_tao_lop:
    with st.container(border=True):
        st.subheader(CLASS_LABELS[lang]["form_create_header"])

        with st.form("tao_lop_form", clear_on_submit=True):
            st.markdown(f"### {CLASS_LABELS[lang]['section_basic']}")

            c1, c2 = st.columns(2)

            with c1:
                class_name = st.text_input(
                    CLASS_LABELS[lang]["input_name"],
                    placeholder=CLASS_LABELS[lang]["input_name_placeholder"],
                )

                subject = st.text_input(
                    CLASS_LABELS[lang]["input_subject"],
                    placeholder=CLASS_LABELS[lang]["input_subject_placeholder"],
                )

                description = st.text_area(CLASS_LABELS[lang]["input_desc"])

            with c2:
                if not teacher_options:
                    st.warning(CLASS_LABELS[lang]["warn_no_teacher"])
                    selected_teacher_label = None
                else:
                    selected_teacher_label = st.selectbox(
                        CLASS_LABELS[lang]["input_teacher"],
                        options=list(teacher_options.keys()),
                    )

                is_public = st.checkbox(
                    CLASS_LABELS[lang]["input_public"],
                    value=True,
                )

                status = st.selectbox(
                    CLASS_LABELS[lang]["input_status"],
                    options=["active", "closed"],
                    index=0,
                )

            st.divider()
            st.markdown(f"### {CLASS_LABELS[lang]['section_tuition']}")

            tuition_enabled = st.checkbox(
                CLASS_LABELS[lang]["input_tuition_enabled"],
                value=True,
            )

            t1, t2, t3, t4 = st.columns(4)

            with t1:
                registration_fee = st.number_input(
                    CLASS_LABELS[lang]["registration_fee"],
                    min_value=0,
                    step=100000,
                    value=0,
                )

            with t2:
                monthly_fee = st.number_input(
                    CLASS_LABELS[lang]["monthly_fee"],
                    min_value=0,
                    step=100000,
                    value=0,
                )

            with t3:
                cycle_months = st.number_input(
                    CLASS_LABELS[lang]["cycle_months"],
                    min_value=1,
                    max_value=12,
                    step=1,
                    value=3,
                )

                cycle_fee = st.number_input(
                    CLASS_LABELS[lang]["cycle_fee"],
                    min_value=0,
                    step=100000,
                    value=0,
                    help="Nếu để 0, hệ thống có thể tính theo học phí tháng x số tháng/chu kỳ.",
                )

            with t4:
                yearly_fee = st.number_input(
                    CLASS_LABELS[lang]["yearly_fee"],
                    min_value=0,
                    step=100000,
                    value=0,
                    help="Nếu để 0, hệ thống có thể tính theo học phí tháng x 12.",
                )

            p1, p2, p3, p4 = st.columns(4)

            with p1:
                billing_day = st.number_input(
                    CLASS_LABELS[lang]["billing_day"],
                    min_value=1,
                    max_value=28,
                    step=1,
                    value=5,
                )

            with p2:
                grace_days = st.number_input(
                    CLASS_LABELS[lang]["grace_days"],
                    min_value=0,
                    max_value=30,
                    step=1,
                    value=3,
                )

            with p3:
                allow_registration_fee = st.checkbox(
                    CLASS_LABELS[lang]["allow_registration_fee"],
                    value=True,
                )
                allow_monthly_payment = st.checkbox(
                    CLASS_LABELS[lang]["allow_monthly"],
                    value=True,
                )

            with p4:
                allow_cycle_payment = st.checkbox(
                    CLASS_LABELS[lang]["allow_cycle"],
                    value=True,
                )
                allow_yearly_payment = st.checkbox(
                    CLASS_LABELS[lang]["allow_yearly"],
                    value=True,
                )

            tuition_note = st.text_area(CLASS_LABELS[lang]["tuition_note"])

            if st.form_submit_button(
                CLASS_LABELS[lang]["btn_create_submit"],
                type="primary",
                use_container_width=True,
            ):
                if not class_name or not subject or not selected_teacher_label:
                    st.error(CLASS_LABELS[lang]["err_fields"])
                else:
                    selected_teacher = teacher_options[selected_teacher_label]

                    payload = build_class_payload(
                        class_name=class_name,
                        subject=subject,
                        teacher_id=selected_teacher["id"],
                        teacher_name=selected_teacher["name"],
                        description=description,
                        is_public=is_public,
                        status=status,
                        tuition_enabled=tuition_enabled,
                        registration_fee=registration_fee,
                        monthly_fee=monthly_fee,
                        cycle_fee=cycle_fee,
                        cycle_months=cycle_months,
                        yearly_fee=yearly_fee,
                        billing_day=billing_day,
                        grace_days=grace_days,
                        allow_registration_fee=allow_registration_fee,
                        allow_monthly_payment=allow_monthly_payment,
                        allow_cycle_payment=allow_cycle_payment,
                        allow_yearly_payment=allow_yearly_payment,
                        tuition_note=tuition_note,
                    )

                    try:
                        res = requests.post(
                            f"{TV1_API}/classes/create",
                            json=payload,
                            headers=get_headers(),
                            timeout=20,
                        )

                        if res.status_code == 200:
                            st.success(f"{CLASS_LABELS[lang]['success_created']} '{class_name}'")
                            time.sleep(0.5)
                            st.rerun()
                        else:
                            st.error(f"{CLASS_LABELS[lang]['err_backend']} {res.text}")

                    except Exception as e:
                        st.error(f"{CLASS_LABELS[lang]['err_connection']} {e}")


# =========================================================
# TAB 2: QUẢN LÝ LỚP HỌC
# =========================================================
with tab_danh_sach:
    classes = get_classes()

    if not classes:
        st.info("Hiện tại chưa có lớp học nào được tạo." if lang == "vi" else "No classes available.")
    else:
        class_options_dict = {
            c.get("id", c.get("_id")): f"{c.get('class_name')} - {c.get('subject', '')}"
            for c in classes
        }

        selected_class_id = st.selectbox(
            CLASS_LABELS[lang]["select_class"],
            options=list(class_options_dict.keys()),
            format_func=lambda x: class_options_dict[x],
        )

        if selected_class_id:
            sel = next(
                (c for c in classes if c.get("id", c.get("_id")) == selected_class_id),
                None,
            )

            if sel:
                st.markdown(f"### {CLASS_LABELS[lang]['header_manage']} `{sel.get('class_name')}`")

                info_cols = st.columns(4)
                info_cols[0].metric(CLASS_LABELS[lang]["lbl_subject"], sel.get("subject", "---"))
                info_cols[1].metric(CLASS_LABELS[lang]["lbl_status"], sel.get("status", "---"))
                info_cols[2].metric(CLASS_LABELS[lang]["lbl_public"], bool_text(sel.get("is_public")))
                info_cols[3].metric(CLASS_LABELS[lang]["lbl_tuition"], format_money(sel.get("monthly_fee", 0)))

                st.caption(
                    f"{CLASS_LABELS[lang]['lbl_teacher_assigned']} {sel.get('teacher_name', '---')} | "
                    f"{CLASS_LABELS[lang]['registration_fee']}: {format_money(sel.get('registration_fee', 0))} | "
                    f"{CLASS_LABELS[lang]['cycle_fee']}: {format_money(sel.get('cycle_fee', 0))} / {sel.get('cycle_months', 3)} tháng | "
                    f"{CLASS_LABELS[lang]['yearly_fee']}: {format_money(sel.get('yearly_fee', 0))}"
                )

                sub_info, sub_edit, sub_del = st.tabs([
                    CLASS_LABELS[lang]["subtab_students"],
                    CLASS_LABELS[lang]["subtab_edit"],
                    CLASS_LABELS[lang]["subtab_delete"],
                ])

                # =========================================================
                # SUB TAB 1: DANH SÁCH HỌC VIÊN
                # =========================================================
                with sub_info:
                    st.write(f"**{CLASS_LABELS[lang]['lbl_teacher_assigned']}** {sel.get('teacher_name')}")

                    try:
                        res_st = requests.get(
                            f"{TV1_API}/classes/{selected_class_id}/students/details",
                            headers=get_headers(),
                            timeout=15,
                        )
                        real_st = res_st.json() if res_st.status_code == 200 else []
                    except Exception:
                        real_st = []

                    if not real_st:
                        st.info(CLASS_LABELS[lang]["info_no_students"])
                    else:
                        df = pd.DataFrame(real_st)

                        if "STT" not in df.columns:
                            df.insert(0, "STT", range(1, 1 + len(df)))

                        rename_dict = {
                            "STT": "No.",
                            "Mã HS": "Mã Học Viên" if lang == "vi" else "Student ID",
                            "Tên Học Sinh": "Họ & Tên Học Sinh" if lang == "vi" else "Student Full Name",
                            "Tên Phụ Huynh": "Tên Phụ Huynh" if lang == "vi" else "Parent Name",
                            "SĐT Liên Hệ": "SĐT Liên Hệ Phụ Huynh" if lang == "vi" else "Parent Phone Number",
                            "Tình trạng": "Trạng Thái" if lang == "vi" else "Status",
                        }

                        df_display = df.rename(
                            columns={k: v for k, v in rename_dict.items() if k in df.columns}
                        )

                        cols_to_show = [v for v in rename_dict.values() if v in df_display.columns]

                        if not cols_to_show:
                            cols_to_show = df_display.columns.tolist()

                        st.dataframe(
                            df_display[cols_to_show],
                            use_container_width=True,
                            hide_index=True,
                        )

                        current_date_str = datetime.now().strftime("%d%m%Y")
                        safe_class_name = str(sel.get("class_name", "lop")).replace(" ", "_")
                        file_export_name = f"Danh_Sach_Lop_{safe_class_name}_{current_date_str}.csv"

                        st.download_button(
                            CLASS_LABELS[lang]["btn_export"],
                            data=df.to_csv(index=False).encode("utf-8-sig"),
                            file_name=file_export_name,
                            mime="text/csv",
                            type="secondary",
                        )

                        st.divider()
                        st.write(CLASS_LABELS[lang]["sub_remove_student"])

                        name_key = "Tên Học Sinh" if "Tên Học Sinh" in df.columns else (
                            df.columns[2] if len(df.columns) > 2 else "name"
                        )
                        id_key = "Mã HS" if "Mã HS" in df.columns else (
                            df.columns[1] if len(df.columns) > 1 else "id"
                        )

                        st_dict = {
                            r[id_key]: f"{r[id_key]} - {r[name_key]}"
                            for r in real_st
                            if id_key in r
                        }

                        if st_dict:
                            st_to_del = st.selectbox(
                                CLASS_LABELS[lang]["select_student_remove"],
                                options=list(st_dict.keys()),
                                format_func=lambda x: st_dict[x],
                                key="sb_del_st",
                            )

                            if st.button(CLASS_LABELS[lang]["btn_remove_student"], type="primary"):
                                res = requests.delete(
                                    f"{TV1_API}/classes/{selected_class_id}/students/{st_to_del}",
                                    headers=get_headers(),
                                    timeout=15,
                                )

                                if res.status_code == 200:
                                    st.success(CLASS_LABELS[lang]["success_removed_student"])
                                    time.sleep(0.5)
                                    st.rerun()
                                else:
                                    st.error(res.text)

                # =========================================================
                # SUB TAB 2: SỬA THÔNG TIN LỚP
                # =========================================================
                with sub_edit:
                    with st.form(f"edit_{selected_class_id}"):
                        st.markdown(f"### {CLASS_LABELS[lang]['section_basic']}")

                        e1, e2 = st.columns(2)

                        with e1:
                            n_name = st.text_input(
                                CLASS_LABELS[lang]["edit_name"],
                                value=sel.get("class_name", ""),
                            )

                            n_subject = st.text_input(
                                CLASS_LABELS[lang]["edit_subject"],
                                value=sel.get("subject", ""),
                            )

                            n_desc = st.text_area(
                                CLASS_LABELS[lang]["edit_desc"],
                                value=sel.get("description", ""),
                            )

                        with e2:
                            t_labels = list(teacher_options.keys())
                            cur_t_id = sel.get("teacher_id")

                            def_idx = next(
                                (
                                    i for i, l in enumerate(t_labels)
                                    if teacher_options[l]["id"] == cur_t_id
                                ),
                                0,
                            ) if t_labels else 0

                            n_t_label = st.selectbox(
                                CLASS_LABELS[lang]["edit_teacher"],
                                options=t_labels,
                                index=def_idx,
                            ) if t_labels else None

                            n_public = st.checkbox(
                                CLASS_LABELS[lang]["input_public"],
                                value=bool(sel.get("is_public", True)),
                            )

                            n_status = st.selectbox(
                                CLASS_LABELS[lang]["input_status"],
                                options=["active", "closed"],
                                index=0 if sel.get("status", "active") == "active" else 1,
                            )

                        st.divider()
                        st.markdown(f"### {CLASS_LABELS[lang]['section_tuition']}")

                        n_tuition_enabled = st.checkbox(
                            CLASS_LABELS[lang]["input_tuition_enabled"],
                            value=bool(sel.get("tuition_enabled", True)),
                        )

                        u1, u2, u3, u4 = st.columns(4)

                        with u1:
                            n_registration_fee = st.number_input(
                                CLASS_LABELS[lang]["registration_fee"],
                                min_value=0,
                                step=100000,
                                value=int(to_float(sel.get("registration_fee", 0))),
                                key=f"registration_{selected_class_id}",
                            )

                        with u2:
                            n_monthly_fee = st.number_input(
                                CLASS_LABELS[lang]["monthly_fee"],
                                min_value=0,
                                step=100000,
                                value=int(to_float(sel.get("monthly_fee", 0))),
                                key=f"monthly_{selected_class_id}",
                            )

                        with u3:
                            n_cycle_months = st.number_input(
                                CLASS_LABELS[lang]["cycle_months"],
                                min_value=1,
                                max_value=12,
                                step=1,
                                value=int(to_int(sel.get("cycle_months", 3), 3)),
                                key=f"cycle_months_{selected_class_id}",
                            )

                            n_cycle_fee = st.number_input(
                                CLASS_LABELS[lang]["cycle_fee"],
                                min_value=0,
                                step=100000,
                                value=int(to_float(sel.get("cycle_fee", 0))),
                                key=f"cycle_fee_{selected_class_id}",
                            )

                        with u4:
                            n_yearly_fee = st.number_input(
                                CLASS_LABELS[lang]["yearly_fee"],
                                min_value=0,
                                step=100000,
                                value=int(to_float(sel.get("yearly_fee", 0))),
                                key=f"yearly_{selected_class_id}",
                            )

                        b1, b2, b3, b4 = st.columns(4)

                        with b1:
                            n_billing_day = st.number_input(
                                CLASS_LABELS[lang]["billing_day"],
                                min_value=1,
                                max_value=28,
                                step=1,
                                value=int(to_int(sel.get("billing_day", 5), 5)),
                                key=f"billing_{selected_class_id}",
                            )

                        with b2:
                            n_grace_days = st.number_input(
                                CLASS_LABELS[lang]["grace_days"],
                                min_value=0,
                                max_value=30,
                                step=1,
                                value=int(to_int(sel.get("grace_days", 3), 3)),
                                key=f"grace_{selected_class_id}",
                            )

                        with b3:
                            n_allow_registration_fee = st.checkbox(
                                CLASS_LABELS[lang]["allow_registration_fee"],
                                value=bool(sel.get("allow_registration_fee", True)),
                                key=f"allow_reg_{selected_class_id}",
                            )
                            n_allow_monthly_payment = st.checkbox(
                                CLASS_LABELS[lang]["allow_monthly"],
                                value=bool(sel.get("allow_monthly_payment", True)),
                                key=f"allow_monthly_{selected_class_id}",
                            )

                        with b4:
                            n_allow_cycle_payment = st.checkbox(
                                CLASS_LABELS[lang]["allow_cycle"],
                                value=bool(sel.get("allow_cycle_payment", True)),
                                key=f"allow_cycle_{selected_class_id}",
                            )
                            n_allow_yearly_payment = st.checkbox(
                                CLASS_LABELS[lang]["allow_yearly"],
                                value=bool(sel.get("allow_yearly_payment", True)),
                                key=f"allow_yearly_{selected_class_id}",
                            )

                        n_tuition_note = st.text_area(
                            CLASS_LABELS[lang]["tuition_note"],
                            value=sel.get("tuition_note", ""),
                        )

                        if st.form_submit_button(
                            CLASS_LABELS[lang]["btn_save_changes"],
                            type="primary",
                            use_container_width=True,
                        ):
                            if not n_name or not n_subject:
                                st.error(CLASS_LABELS[lang]["err_fields"])
                            else:
                                if n_t_label:
                                    sel_t = teacher_options[n_t_label]
                                    teacher_id = sel_t["id"]
                                    teacher_name = sel_t["name"]
                                else:
                                    teacher_id = sel.get("teacher_id")
                                    teacher_name = sel.get("teacher_name")

                                upd = build_class_payload(
                                    class_name=n_name,
                                    subject=n_subject,
                                    teacher_id=teacher_id,
                                    teacher_name=teacher_name,
                                    description=n_desc,
                                    is_public=n_public,
                                    status=n_status,
                                    tuition_enabled=n_tuition_enabled,
                                    registration_fee=n_registration_fee,
                                    monthly_fee=n_monthly_fee,
                                    cycle_fee=n_cycle_fee,
                                    cycle_months=n_cycle_months,
                                    yearly_fee=n_yearly_fee,
                                    billing_day=n_billing_day,
                                    grace_days=n_grace_days,
                                    allow_registration_fee=n_allow_registration_fee,
                                    allow_monthly_payment=n_allow_monthly_payment,
                                    allow_cycle_payment=n_allow_cycle_payment,
                                    allow_yearly_payment=n_allow_yearly_payment,
                                    tuition_note=n_tuition_note,
                                )

                                upd["student_ids"] = sel.get("student_ids", [])

                                try:
                                    resp = requests.put(
                                        f"{TV1_API}/classes/{selected_class_id}",
                                        json=upd,
                                        headers=get_headers(),
                                        timeout=20,
                                    )

                                    if resp.status_code == 200:
                                        st.success(CLASS_LABELS[lang]["success_updated_class"])
                                        time.sleep(0.5)
                                        st.rerun()
                                    else:
                                        st.error(f"{CLASS_LABELS[lang]['err_updated_class']} {resp.text}")

                                except Exception as e:
                                    st.error(f"Lỗi hệ thống: {e}")

                # =========================================================
                # SUB TAB 3: XÓA LỚP
                # =========================================================
                with sub_del:
                    st.warning(CLASS_LABELS[lang]["warn_delete"])

                    if st.button(
                        CLASS_LABELS[lang]["btn_delete_class"],
                        type="primary",
                        use_container_width=True,
                    ):
                        res = requests.delete(
                            f"{TV1_API}/classes/{selected_class_id}",
                            headers=get_headers(),
                            timeout=20,
                        )

                        if res.status_code == 200:
                            st.success(CLASS_LABELS[lang]["success_deleted_class"])
                            time.sleep(0.5)
                            st.rerun()
                        else:
                            st.error(res.text)