import streamlit as st
import pandas as pd
import requests
import os
import time
from datetime import date

from utils.role_guard import require_role

# ================= CRITICAL: CẤU HÌNH TRANG LUÔN ĐỂ ĐẦU FILE =================
st.set_page_config(page_title="Đăng Ký Lớp Học", page_icon=None, layout="wide")

require_role(["parent", "admin"])

BACKEND_URL = st.session_state.get("api_url", "http://localhost:8000")
API_TV1 = f"{BACKEND_URL}/api/tv1"
API_TV3 = f"{BACKEND_URL}/api/tv3"
API_TUITION = f"{BACKEND_URL}/api/tuition"


# ================= HÀM ĐỌC FILE CSS =================
def load_css(file_name):
    current_dir = os.path.dirname(os.path.abspath(__file__))
    css_root = os.path.abspath(os.path.join(current_dir, "../../CSS"))
    full_path = os.path.join(css_root, file_name)

    if os.path.exists(full_path):
        with open(full_path, "r", encoding="utf-8") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    else:
        st.warning(f"Không tìm thấy file CSS tại: {full_path}")


load_css("parent/parent_global.css")

lang = st.session_state.get("lang", "vi")
parent_id = st.session_state.get("user_id")
token = st.session_state.get("access_token") or st.session_state.get("token")


ENROLL_LABELS = {
    "vi": {
        "title": "Đăng Ký Lớp Học Cho Con",
        "subtitle": "Phụ huynh có thể chọn lớp phù hợp, chọn gói học phí và tạo hóa đơn học phí cho bé.",
        "err_login": "Vui lòng đăng nhập với tài khoản Phụ huynh để đăng ký lớp học.",
        "warn_no_child": "Bạn chưa có hồ sơ học sinh nào. Vui lòng sang trang 'Quản Lý Con Em' để tạo tài khoản cho bé trước.",
        "err_connection": "Không thể kết nối đến máy chủ Backend:",
        "expander_schedule": "Thời Khóa Biểu Hiện Tại Của Bé",
        "expander_desc": "Vui lòng kiểm tra lịch học hiện tại của các bé để tránh đăng ký lớp mới bị trùng thời gian.",
        "info_no_schedule": "Bé hiện chưa có lịch học nào.",
        "session_morning": "SÁNG",
        "session_afternoon": "CHIỀU",
        "session_evening": "TỐI",
        "session_label": "Buổi",
        "sub_enroll_section": "Danh Sách Lớp Học Đang Mở",
        "select_child_global": "Chọn học sinh để đăng ký:",
        "lbl_registering_for": "Đăng ký cho bé:",
        "info_all_enrolled": "Học sinh này đã tham gia tất cả các lớp đang mở hoặc hiện chưa có lớp mới.",
        "info_empty_classes": "Hiện tại hệ thống chưa có lớp học nào đang mở đăng ký công khai.",
        "lbl_class_unknown": "Tên lớp chưa rõ",
        "lbl_subject": "Môn học:",
        "lbl_sub_unassigned": "Chưa cập nhật",
        "lbl_teacher": "Giáo viên phụ trách:",
        "lbl_teacher_arranging": "Đang xếp",
        "lbl_description": "Mô tả:",
        "lbl_fee": "Học phí",
        "registration_fee": "Phí đăng ký",
        "monthly_fee": "Theo tháng",
        "cycle_fee": "Theo chu kỳ",
        "yearly_fee": "Cả năm",
        "billing_day": "Ngày đến hạn hằng tháng",
        "select_plan": "Chọn hình thức đóng học phí",
        "plan_monthly": "Đóng theo tháng",
        "plan_cycle": "Đóng theo chu kỳ",
        "plan_yearly": "Đóng cả năm",
        "start_date": "Ngày bắt đầu học",
        "pay_registration_now": "Đóng phí đăng ký ngay nếu có",
        "pay_first_invoice_now": "Đóng học phí kỳ đầu ngay",
        "btn_enroll": "Xác Nhận Đăng Ký Lớp",
        "success_enrolled": "Đã đăng ký thành công cho bé",
        "success_invoice": "Hóa đơn học phí đã được tạo. Bạn có thể vào trang Học phí để thanh toán.",
        "err_failed_enroll": "Đăng ký thất bại. Vui lòng kiểm tra lại thông tin.",
        "err_post_connection": "Lỗi kết nối khi gửi yêu cầu đăng ký học.",
        "no_payment_plan": "Lớp này chưa có gói học phí hợp lệ.",
        "view_tuition_hint": "Sau khi đăng ký, vào mục Học phí để xem và thanh toán hóa đơn.",
        "paid_now_hint": "Nếu chọn đóng ngay, hệ thống sẽ trừ tiền từ ví phụ huynh nếu đủ số dư.",
    },
    "en": {
        "title": "Course Enrollment for Children",
        "subtitle": "Parents can choose a class, select a tuition plan, and generate tuition invoices.",
        "err_login": "Authentication required. Please log in with a Parent account to enroll in classes.",
        "warn_no_child": "No student profiles found. Please create a child profile first.",
        "err_connection": "Unable to establish a connection to the Backend server:",
        "expander_schedule": "Children's Current Timetable",
        "expander_desc": "Please review your children's schedules to avoid conflicting classes.",
        "info_no_schedule": "This child currently has no scheduled classes.",
        "session_morning": "MORNING",
        "session_afternoon": "AFTERNOON",
        "session_evening": "EVENING",
        "session_label": "Session",
        "sub_enroll_section": "Open Classes for Registration",
        "select_child_global": "Select a child to enroll:",
        "lbl_registering_for": "Enrolling:",
        "info_all_enrolled": "This student is already enrolled in all available classes or no new classes are open.",
        "info_empty_classes": "There are currently no open classes available for public registration.",
        "lbl_class_unknown": "Unknown Class Title",
        "lbl_subject": "Subject:",
        "lbl_sub_unassigned": "Unassigned",
        "lbl_teacher": "Instructor:",
        "lbl_teacher_arranging": "TBD",
        "lbl_description": "Description:",
        "lbl_fee": "Tuition",
        "registration_fee": "Registration fee",
        "monthly_fee": "Monthly",
        "cycle_fee": "Cycle",
        "yearly_fee": "Yearly",
        "billing_day": "Monthly due day",
        "select_plan": "Select tuition plan",
        "plan_monthly": "Pay monthly",
        "plan_cycle": "Pay by cycle",
        "plan_yearly": "Pay yearly",
        "start_date": "Start date",
        "pay_registration_now": "Pay registration fee now if any",
        "pay_first_invoice_now": "Pay first invoice now",
        "btn_enroll": "Confirm Enrollment",
        "success_enrolled": "Registration successful for",
        "success_invoice": "Tuition invoice has been created. You can go to Tuition page to pay.",
        "err_failed_enroll": "Enrollment failed. Please check the information.",
        "err_post_connection": "Connection error occurred while submitting enrollment request.",
        "no_payment_plan": "This class has no valid tuition plan.",
        "view_tuition_hint": "After enrolling, open Tuition page to view and pay invoices.",
        "paid_now_hint": "If paying now, the system will deduct from the parent wallet if balance is sufficient.",
    },
}


def get_headers():
    return {
        "Authorization": f"Bearer {token}",
        "parent-id": str(parent_id),
        "Content-Type": "application/json",
    }


def to_float(value, default=0.0):
    try:
        if value is None or value == "":
            return default
        return float(value)
    except Exception:
        return default


def format_money(value):
    return f"{to_float(value):,.0f} VNĐ"


def get_child_name(child):
    return (
        child.get("full_name")
        or child.get("name")
        or f"Bé {str(child.get('id', ''))[-4:]}"
    )


def get_class_id(cls):
    return str(cls.get("id") or cls.get("_id") or "")


def get_payment_plans(cls):
    plans = []

    monthly_fee = to_float(cls.get("monthly_fee"))
    cycle_fee = to_float(cls.get("cycle_fee"))
    yearly_fee = to_float(cls.get("yearly_fee"))
    cycle_months = int(cls.get("cycle_months") or 3)

    if cls.get("allow_monthly_payment", True) and monthly_fee > 0:
        plans.append({
            "key": "monthly",
            "label": f"{ENROLL_LABELS[lang]['plan_monthly']} - {format_money(monthly_fee)}",
            "amount": monthly_fee,
        })

    if cls.get("allow_cycle_payment", True):
        calculated_cycle = cycle_fee if cycle_fee > 0 else monthly_fee * cycle_months
        if calculated_cycle > 0:
            plans.append({
                "key": "cycle",
                "label": f"{ENROLL_LABELS[lang]['plan_cycle']} ({cycle_months} tháng) - {format_money(calculated_cycle)}",
                "amount": calculated_cycle,
            })

    if cls.get("allow_yearly_payment", True):
        calculated_yearly = yearly_fee if yearly_fee > 0 else monthly_fee * 12
        if calculated_yearly > 0:
            plans.append({
                "key": "yearly",
                "label": f"{ENROLL_LABELS[lang]['plan_yearly']} - {format_money(calculated_yearly)}",
                "amount": calculated_yearly,
            })

    return plans


@st.cache_data(ttl=30)
def get_my_children_cached(api_tv3, auth_token, pid):
    try:
        headers = {
            "Authorization": f"Bearer {auth_token}",
            "parent-id": str(pid),
        }
        res = requests.get(f"{api_tv3}/parent/my-children", headers=headers, timeout=15)
        return res.json() if res.status_code == 200 else []
    except Exception:
        return []


@st.cache_data(ttl=30)
def get_tuition_classes_cached(api_tuition, api_tv1, auth_token, pid):
    headers = {
        "Authorization": f"Bearer {auth_token}",
        "parent-id": str(pid),
    }

    try:
        res = requests.get(f"{api_tuition}/classes", headers=headers, timeout=15)
        if res.status_code == 200:
            data = res.json()
            if isinstance(data, dict):
                return data.get("items", [])
            if isinstance(data, list):
                return data
    except Exception:
        pass

    try:
        res = requests.get(f"{api_tv1}/classes/public", headers=headers, timeout=15)
        return res.json() if res.status_code == 200 else []
    except Exception:
        return []


@st.cache_data(ttl=30)
def get_all_classes_cached(api_tv1, auth_token, pid):
    try:
        headers = {
            "Authorization": f"Bearer {auth_token}",
            "parent-id": str(pid),
        }
        res = requests.get(f"{api_tv1}/classes", headers=headers, timeout=15)
        return res.json() if res.status_code == 200 else []
    except Exception:
        return []


@st.cache_data(ttl=30)
def get_schedules_cached(api_tv1, auth_token, pid):
    try:
        headers = {
            "Authorization": f"Bearer {auth_token}",
            "parent-id": str(pid),
        }
        res = requests.get(f"{api_tv1}/schedule/list", headers=headers, timeout=15)
        return res.json() if res.status_code == 200 else []
    except Exception:
        return []


def render_child_timetable(child_data, all_classes, schedules):
    child_id = str(child_data["id"])

    day_names_vi = ["Thứ 2", "Thứ 3", "Thứ 4", "Thứ 5", "Thứ 6", "Thứ 7", "Chủ nhật"]
    day_names_en = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    display_days = day_names_vi if lang == "vi" else day_names_en

    sessions_vi = ["SÁNG", "CHIỀU", "TỐI"]
    sessions_en = ["MORNING", "AFTERNOON", "EVENING"]
    display_sessions = sessions_vi if lang == "vi" else sessions_en

    schedule_map = {
        sessions_vi[0]: {d: [] for d in day_names_vi},
        sessions_vi[1]: {d: [] for d in day_names_vi},
        sessions_vi[2]: {d: [] for d in day_names_vi},
    }

    has_classes = False

    for cls in all_classes:
        student_ids = [str(s) for s in cls.get("student_ids", [])]

        if child_id in student_ids:
            c_id = get_class_id(cls)
            sched = next((s for s in schedules if str(s.get("class_id")) == c_id), None)

            if sched:
                has_classes = True
                start_time = sched.get("start_time", "00:00")

                try:
                    hour = int(start_time.split(":")[0])
                except Exception:
                    hour = 8

                if hour < 12:
                    session = sessions_vi[0]
                elif hour < 17:
                    session = sessions_vi[1]
                else:
                    session = sessions_vi[2]

                for d in sched.get("days_of_week", []):
                    if d in day_names_vi:
                        schedule_map[session][d].append({
                            "class_name": cls.get("class_name"),
                            "subject": sched.get("subject", cls.get("subject", "")),
                            "time": f"{start_time} - {sched.get('end_time', '')}",
                            "room": sched.get("room", "Online"),
                        })

    if not has_classes:
        st.info(ENROLL_LABELS[lang]["info_no_schedule"])
        return

    css_style = """
    <style>
    .tt-table { width: 100%; border-collapse: collapse; text-align: center; margin-bottom: 20px; font-family: sans-serif; table-layout: fixed; }
    .tt-table th { background-color: #f8fafc; padding: 12px 4px; border: 1px solid #cbd5e1; font-weight: 600; color: #334155; font-size: 0.9em; }
    .tt-table td { border: 1px solid #cbd5e1; padding: 8px; vertical-align: top; }
    .tt-table th:first-child { width: 6%; }
    .tt-session { font-weight: bold; background-color: #f1f5f9; vertical-align: middle !important; color: #475569; writing-mode: vertical-rl; transform: rotate(180deg); text-align: center; letter-spacing: 2px;}
    .tt-card { background-color: #f0f9ff; border-left: 4px solid #0284c7; border-radius: 4px; padding: 8px; margin-bottom: 8px; text-align: left; }
    .tt-title { font-weight: 700; color: #0369a1; font-size: 0.85em; margin-bottom: 4px; line-height: 1.2;}
    .tt-subj { font-size: 0.8em; color: #334155; margin-bottom: 4px; font-weight: 500;}
    .tt-meta { font-size: 0.75em; color: #64748b; margin-top: 2px; }
    </style>
    """

    html_content = f"{css_style}<table class='tt-table'><thead><tr><th>{ENROLL_LABELS[lang]['session_label']}</th>"

    for d in display_days:
        html_content += f"<th>{d}</th>"

    html_content += "</tr></thead><tbody>"

    for idx, session_vi in enumerate(sessions_vi):
        session_label = display_sessions[idx]
        html_content += f"<tr><td class='tt-session'>{session_label}</td>"

        for day_vi in day_names_vi:
            html_content += "<td>"
            classes_in_slot = schedule_map[session_vi][day_vi]

            for c in classes_in_slot:
                html_content += "<div class='tt-card'>"
                html_content += f"<div class='tt-title'>{c['class_name']}</div>"
                html_content += f"<div class='tt-subj'>{c['subject']}</div>"
                html_content += f"<div class='tt-meta'>{c['time']} | {c['room']}</div>"
                html_content += "</div>"

            html_content += "</td>"

        html_content += "</tr>"

    html_content += "</tbody></table>"

    st.markdown(html_content, unsafe_allow_html=True)


st.title(ENROLL_LABELS[lang]["title"])
st.write(ENROLL_LABELS[lang]["subtitle"])

if not parent_id or not token:
    st.error(ENROLL_LABELS[lang]["err_login"])
    st.stop()

children = get_my_children_cached(API_TV3, token, parent_id)

if not children:
    st.warning(ENROLL_LABELS[lang]["warn_no_child"])
    st.stop()

child_options = {str(c["id"]): get_child_name(c) for c in children if c.get("id")}

public_classes = get_tuition_classes_cached(API_TUITION, API_TV1, token, parent_id)
all_classes = get_all_classes_cached(API_TV1, token, parent_id)
schedules = get_schedules_cached(API_TV1, token, parent_id)

schedule_subject_map = {}
for s in schedules:
    c_id = str(s.get("class_id", ""))
    subj = s.get("subject", "")
    if c_id and subj:
        schedule_subject_map[c_id] = subj


st.subheader(ENROLL_LABELS[lang]["expander_schedule"])
st.write(ENROLL_LABELS[lang]["expander_desc"])

if len(children) > 1:
    tabs = st.tabs([get_child_name(c) for c in children])

    for i, child in enumerate(children):
        with tabs[i]:
            render_child_timetable(child, all_classes, schedules)
else:
    render_child_timetable(children[0], all_classes, schedules)

st.divider()

st.subheader(ENROLL_LABELS[lang]["sub_enroll_section"])

selected_child_id = st.selectbox(
    ENROLL_LABELS[lang]["select_child_global"],
    options=list(child_options.keys()),
    format_func=lambda x: child_options[x],
)

st.write("")

if not public_classes:
    st.info(ENROLL_LABELS[lang]["info_empty_classes"])
else:
    available_classes = []

    for cls in public_classes:
        student_ids = [str(s) for s in cls.get("student_ids", [])]

        if str(selected_child_id) not in student_ids:
            available_classes.append(cls)

    if not available_classes:
        st.info(ENROLL_LABELS[lang]["info_all_enrolled"])
    else:
        for cls in available_classes:
            class_id = get_class_id(cls)

            with st.container(border=True):
                col1, col2 = st.columns([3, 2])

                with col1:
                    class_name = cls.get("class_name", ENROLL_LABELS[lang]["lbl_class_unknown"])
                    st.markdown(f"#### {class_name}")

                    subject_raw = schedule_subject_map.get(
                        class_id,
                        cls.get("subject", ENROLL_LABELS[lang]["lbl_sub_unassigned"]),
                    )

                    if lang == "en" and subject_raw == "Chưa xác định":
                        subject_display = "Unassigned"
                    else:
                        subject_display = subject_raw

                    teacher_name = cls.get("teacher_name") or ENROLL_LABELS[lang]["lbl_teacher_arranging"]

                    st.write(f"**{ENROLL_LABELS[lang]['lbl_subject']}** {subject_display}")
                    st.caption(f"{ENROLL_LABELS[lang]['lbl_teacher']} {teacher_name}")

                    if cls.get("description"):
                        st.write(f"**{ENROLL_LABELS[lang]['lbl_description']}** {cls.get('description')}")

                    st.divider()
                    st.markdown(f"**{ENROLL_LABELS[lang]['lbl_fee']}**")

                    registration_fee = to_float(cls.get("registration_fee", 0))
                    monthly_fee = to_float(cls.get("monthly_fee", 0))
                    cycle_months = int(cls.get("cycle_months") or 3)
                    cycle_fee = to_float(cls.get("cycle_fee", 0)) or monthly_fee * cycle_months
                    yearly_fee = to_float(cls.get("yearly_fee", 0)) or monthly_fee * 12

                    fee_cols = st.columns(4)
                    fee_cols[0].metric(ENROLL_LABELS[lang]["registration_fee"], format_money(registration_fee))
                    fee_cols[1].metric(ENROLL_LABELS[lang]["monthly_fee"], format_money(monthly_fee))
                    fee_cols[2].metric(f"{ENROLL_LABELS[lang]['cycle_fee']} ({cycle_months}T)", format_money(cycle_fee))
                    fee_cols[3].metric(ENROLL_LABELS[lang]["yearly_fee"], format_money(yearly_fee))

                    st.caption(f"{ENROLL_LABELS[lang]['billing_day']}: ngày {cls.get('billing_day', 5)}")

                with col2:
                    st.write(f"**{ENROLL_LABELS[lang]['lbl_registering_for']}** {child_options[selected_child_id]}")

                    plans = get_payment_plans(cls)

                    if not plans:
                        st.warning(ENROLL_LABELS[lang]["no_payment_plan"])
                        continue

                    selected_plan_label = st.selectbox(
                        ENROLL_LABELS[lang]["select_plan"],
                        options=[p["label"] for p in plans],
                        key=f"plan_{class_id}_{selected_child_id}",
                    )

                    selected_plan = next(p for p in plans if p["label"] == selected_plan_label)

                    start_date = st.date_input(
                        ENROLL_LABELS[lang]["start_date"],
                        value=date.today(),
                        key=f"start_{class_id}_{selected_child_id}",
                    )

                    pay_registration_now = False
                    if registration_fee > 0 and cls.get("allow_registration_fee", True):
                        pay_registration_now = st.checkbox(
                            ENROLL_LABELS[lang]["pay_registration_now"],
                            value=False,
                            key=f"pay_reg_{class_id}_{selected_child_id}",
                        )

                    pay_first_invoice_now = st.checkbox(
                        ENROLL_LABELS[lang]["pay_first_invoice_now"],
                        value=False,
                        key=f"pay_first_{class_id}_{selected_child_id}",
                    )

                    st.caption(ENROLL_LABELS[lang]["paid_now_hint"])
                    st.caption(ENROLL_LABELS[lang]["view_tuition_hint"])

                    if st.button(
                        ENROLL_LABELS[lang]["btn_enroll"],
                        key=f"btn_{class_id}_{selected_child_id}",
                        type="primary",
                        use_container_width=True,
                    ):
                        payload = {
                            "parent_id": str(parent_id),
                            "student_id": str(selected_child_id),
                            "class_id": str(class_id),
                            "billing_plan": selected_plan["key"],
                            "start_date": start_date.strftime("%Y-%m-%d"),
                            "pay_registration_now": bool(pay_registration_now),
                            "pay_first_invoice_now": bool(pay_first_invoice_now),
                        }

                        try:
                            register_res = requests.post(
                                f"{API_TUITION}/enrollments",
                                json=payload,
                                headers=get_headers(),
                                timeout=30,
                            )

                            if register_res.status_code in [200, 201]:
                                st.success(
                                    f"{ENROLL_LABELS[lang]['success_enrolled']} "
                                    f"**{child_options[selected_child_id]}**!"
                                )
                                st.info(ENROLL_LABELS[lang]["success_invoice"])
                                st.balloons()
                                st.cache_data.clear()
                                time.sleep(1)
                                st.rerun()
                            else:
                                try:
                                    detail = register_res.json().get("detail", register_res.text)
                                except Exception:
                                    detail = register_res.text

                                st.error(f"{ENROLL_LABELS[lang]['err_failed_enroll']} {detail}")

                        except Exception as e:
                            st.error(f"{ENROLL_LABELS[lang]['err_post_connection']} {e}")