import streamlit as st
import pandas as pd
import requests
import os
import time
from datetime import datetime, timedelta, date

# ================= CRITICAL: CẤU HÌNH TRANG LUÔN ĐỂ ĐẦU FILE =================
st.set_page_config(page_title="Bảng Tin Giáo Viên", page_icon=None, layout="wide")

# ================= ĐA NGÔN NGỮ =================
lang = st.session_state.get("lang", "vi")

DASHBOARD_LABELS = {
    "vi": {
        "title": "Bảng Tin Giáo Viên",
        "btn_today": "Hôm nay",
        "btn_send_req": "Gửi yêu cầu",
        "btn_back_sched": "Quay lại Lịch dạy",
        "month_label": "Tháng {} - {}",
        "req_mgmt_title": "Quản Lý Đơn Từ & Ngày Nghỉ",
        "day_names": ["Thứ 2", "Thứ 3", "Thứ 4", "Thứ 5", "Thứ 6", "Thứ 7", "Chủ nhật"],
        "sessions": ["SÁNG", "CHIỀU", "TỐI"],
        "lbl_room": "Phòng:",
        "unknown_subject": "Chưa rõ môn",
        "unknown_class": "Chưa rõ lớp",
        "tab_new_req": "Gửi Yêu Cầu Mới",
        "tab_history": "Lịch Sử Yêu Cầu",
        "req_types": ["Xin nghỉ phép", "Xin đổi lịch dạy", "Đổi phương thức dạy", "Báo cáo sự cố thiết bị"],
        "lbl_class": "Lớp học liên quan",
        "lbl_reason": "Lý do (*)",
        "btn_submit": "Xác Nhận Gửi Yêu Cầu",
        "success_msg": "Đã gửi yêu cầu thành công!",
        "info_empty_req": "Hiện tại chưa có yêu cầu nào được gửi đi.",
        "df_cols": ["Ngày Gửi", "Loại Yêu Cầu", "Chi Tiết", "Lý Do / Mô Tả", "Trạng Thái"]
    },
    "en": {
        "title": "Teacher's Dashboard",
        "btn_today": "Today",
        "btn_send_req": "Send Request",
        "btn_back_sched": "Back to Schedule",
        "month_label": "{} - {}",
        "req_mgmt_title": "Leave & Request Management",
        "day_names": ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"],
        "sessions": ["MORNING", "AFTERNOON", "EVENING"],
        "lbl_room": "Room:",
        "unknown_subject": "Subject TBD",
        "unknown_class": "Class TBD",
        "tab_new_req": "Submit New Request",
        "tab_history": "Request History",
        "req_types": ["Leave Request", "Reschedule Request", "Change Teaching Mode", "Report Equipment Issue"],
        "lbl_class": "Related Class",
        "lbl_reason": "Reason (*)",
        "btn_submit": "Confirm & Submit",
        "success_msg": "Request submitted successfully!",
        "info_empty_req": "No requests have been sent yet.",
        "df_cols": ["Sent Date", "Request Type", "Details", "Reason / Description", "Status"]
    }
}

# ================= HÀM ĐỌC FILE CSS =================
def load_css(file_name):
    current_dir = os.path.dirname(os.path.abspath(__file__)) 
    css_root = os.path.abspath(os.path.join(current_dir, "../../CSS"))
    full_path = os.path.join(css_root, file_name)
    if os.path.exists(full_path):
        with open(full_path, "r", encoding="utf-8") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

load_css("teacher/teacher_global.css")
API_URL = "http://localhost:8000"

# ================= LẤY THÔNG TIN GIÁO VIÊN ĐĂNG NHẬP =================
user_info = st.session_state.get("user_info", {})
teacher_id = str(user_info.get("id", user_info.get("_id", "")))
teacher_name = user_info.get("name", user_info.get("full_name", "Giáo viên"))

# ================= HÀM LẤY LỊCH DẠY =================
@st.cache_data(ttl=5)
def get_my_schedules(t_id):
    try:
        headers = {"Authorization": f"Bearer {st.session_state.get('token', '')}"}
        res = requests.get(f"{API_URL}/schedule/list", headers=headers, timeout=10)
        if res.status_code == 200:
            schedules = res.json()
            my_scheds = []
            for s in schedules:
                t_teach = str(s.get("teaching_teacher_id", ""))
                t_resp = str(s.get("teacher_id", ""))
                
                if (t_id == t_teach or t_id == t_resp) and t_id != "":
                    my_scheds.append(s)
            return my_scheds
    except:
        pass
    return []

time_slots = []
for hour in range(7, 22):
    for minute in [0, 30]:
        if hour == 21 and minute == 30:
            continue
        time_slots.append(f"{hour:02d}:{minute:02d}")

# ================= KHỞI TẠO STATE & ĐIỀU HƯỚNG VIEW =================
if "current_week_date" not in st.session_state:
    st.session_state.current_week_date = date.today()

if "dashboard_view" not in st.session_state:
    st.session_state.dashboard_view = "schedule" 

def toggle_view():
    if st.session_state.dashboard_view == "schedule":
        st.session_state.dashboard_view = "request"
    else:
        st.session_state.dashboard_view = "schedule"

st.title(DASHBOARD_LABELS[lang]["title"])

col_today, col_prev, col_title, col_next, col_toggle = st.columns([1.5, 0.5, 4, 0.5, 1.5])

with col_today:
    if st.session_state.dashboard_view == "schedule":
        if st.button(DASHBOARD_LABELS[lang]["btn_today"], use_container_width=True):
            st.session_state.current_week_date = date.today()
            st.rerun()

with col_prev:
    if st.session_state.dashboard_view == "schedule":
        if st.button("<", use_container_width=True):
            st.session_state.current_week_date -= timedelta(days=7)
            st.rerun()

with col_title:
    if st.session_state.dashboard_view == "schedule":
        if lang == "vi":
            title_str = f"Tháng {st.session_state.current_week_date.month} - {st.session_state.current_week_date.year}"
        else:
            title_str = f"{st.session_state.current_week_date.strftime('%B')} {st.session_state.current_week_date.year}"
        st.markdown(f"<h3 style='text-align: center; margin-top: 0;'>{title_str}</h3>", unsafe_allow_html=True)
    else:
        st.markdown(f"<h3 style='text-align: center; margin-top: 0;'>{DASHBOARD_LABELS[lang]['req_mgmt_title']}</h3>", unsafe_allow_html=True)

with col_next:
    if st.session_state.dashboard_view == "schedule":
        if st.button(">", use_container_width=True):
            st.session_state.current_week_date += timedelta(days=7)
            st.rerun()

with col_toggle:
    btn_label = DASHBOARD_LABELS[lang]["btn_send_req"] if st.session_state.dashboard_view == "schedule" else DASHBOARD_LABELS[lang]["btn_back_sched"]
    if st.button(btn_label, use_container_width=True, type="primary"):
        toggle_view()
        st.rerun()

my_schedules = get_my_schedules(teacher_id)
sched_options = {str(s.get("id", s.get("_id", ""))): f"{s.get('class_name', '')} - {s.get('subject', '')}" for s in my_schedules}

# ================= RENDER CƠ CHẾ 2 VIEWS =================

if st.session_state.dashboard_view == "schedule":
    # ---------------- VIEW 1: LỊCH DẠY ----------------
    start_of_week = st.session_state.current_week_date - timedelta(days=st.session_state.current_week_date.weekday())
    day_names = DASHBOARD_LABELS[lang]["day_names"]
    week_dates = [start_of_week + timedelta(days=i) for i in range(7)]

    sessions = DASHBOARD_LABELS[lang]["sessions"]
    schedule_map = {sessions[0]: {}, sessions[1]: {}, sessions[2]: {}}
    for session in sessions:
        for d in day_names:
            schedule_map[session][d] = []

    for s in my_schedules:
        start_time = s.get("start_time", "00:00")
        try:
            hour = int(start_time.split(":")[0])
        except:
            hour = 8 
        
        if hour < 12:
            session = sessions[0]
        elif hour < 17:
            session = sessions[1]
        else:
            session = sessions[2]
            
        raw_days = s.get("days_of_week", [])
        
        for d_idx, d_vi in enumerate(["Thứ 2", "Thứ 3", "Thứ 4", "Thứ 5", "Thứ 6", "Thứ 7", "Chủ nhật"]):
            if d_vi in raw_days:
                schedule_map[session][day_names[d_idx]].append(s)

    for session in sessions:
        for d in day_names:
            schedule_map[session][d] = sorted(schedule_map[session][d], key=lambda x: x.get("start_time", "00:00"))

    # CSS NÂNG CẤP ĐỂ ĐÓNG KHUNG & BO GÓC BẢNG LỊCH HỌC
    css_style = """
    <style>
    .schedule-wrapper {
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        overflow: hidden;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 2px 4px -1px rgba(0, 0, 0, 0.03);
        margin-top: 15px;
        background-color: white;
    }
    .schedule-table { 
        width: 100%; border-collapse: collapse; text-align: center; font-family: sans-serif; table-layout: fixed; margin: 0;
    }
    .schedule-table th { 
        background-color: #f1f5f9; padding: 16px 8px; border-bottom: 2px solid #cbd5e1; border-right: 1px solid #e2e8f0; font-weight: 600; color: #1e293b; font-size: 0.9em; 
    }
    .schedule-table th:last-child { border-right: none; }
    .schedule-table td { 
        border-bottom: 1px solid #e2e8f0; border-right: 1px solid #e2e8f0; padding: 12px; vertical-align: top; 
    }
    .schedule-table td:last-child { border-right: none; }
    .schedule-table tr:last-child td { border-bottom: none; }
    .schedule-table th:first-child { width: 6%; background-color: #e2e8f0; border-right: 2px solid #cbd5e1; }
    .session-label { 
        font-weight: bold; background-color: #f8fafc !important; vertical-align: middle !important; color: #334155; writing-mode: vertical-rl; transform: rotate(180deg); text-align: center; letter-spacing: 2px; border-right: 2px solid #cbd5e1 !important;
    }
    .class-card { 
        background: linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%);
        border-left: 4px solid #0ea5e9; border-radius: 6px; padding: 10px; margin-bottom: 8px; text-align: left; 
        box-shadow: 0 1px 3px rgba(0,0,0,0.05); transition: transform 0.2s ease, box-shadow 0.2s ease;
    }
    .class-card:hover {
        transform: translateY(-2px); box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    .class-subject { font-weight: 700; color: #0369a1; font-size: 0.85em; margin-bottom: 4px; line-height: 1.3;}
    .class-name { font-size: 0.8em; color: #475569; margin-bottom: 4px; font-weight: 600;}
    .class-time { font-size: 0.75em; color: #64748b; margin-top: 4px; display: flex; align-items: center; gap: 4px;}
    </style>
    """

    lbl_session = "Buổi" if lang == "vi" else "Session"
    
    # Bọc table vào trong schedule-wrapper
    html_content = f"{css_style}<div class='schedule-wrapper'><table class='schedule-table'><thead><tr><th>{lbl_session}</th>"

    for i, d in enumerate(day_names):
        date_str = week_dates[i].strftime('%d/%m')
        html_content += f"<th>{d}<br><span style='font-size: 0.85em; font-weight: normal; color: #64748b;'>({date_str})</span></th>"
    html_content += "</tr></thead><tbody>"

    for session in sessions:
        html_content += f"<tr><td class='session-label'>{session}</td>"
        for d in day_names:
            html_content += "<td>"
            if not schedule_map[session][d]:
                html_content += ""
            else:
                for s in schedule_map[session][d]:
                    subject = s.get('subject', DASHBOARD_LABELS[lang]['unknown_subject'])
                    c_name = s.get('class_name', DASHBOARD_LABELS[lang]['unknown_class'])
                    t_str = f"{s.get('start_time', '')} - {s.get('end_time', '')}"
                    room = s.get('room', 'Online')
                    lbl_r = DASHBOARD_LABELS[lang]['lbl_room']
                    
                    html_content += f"<div class='class-card'><div class='class-subject'>{subject}</div><div class='class-name'>{c_name}</div><div class='class-time'>{t_str} | {lbl_r} {room}</div></div>"
                    
            html_content += "</td>"
        html_content += "</tr>"

    html_content += "</tbody></table></div>"
    st.markdown(html_content, unsafe_allow_html=True)

else:
    # ---------------- VIEW 2: GỬI YÊU CẦU ----------------
    if "my_leave_requests" not in st.session_state:
        st.session_state.my_leave_requests = []

    tab_form, tab_list = st.tabs([DASHBOARD_LABELS[lang]["tab_new_req"], DASHBOARD_LABELS[lang]["tab_history"]])

    with tab_form:
        req_type = st.selectbox("Chọn loại yêu cầu (*)" if lang == "vi" else "Select Request Type (*)", DASHBOARD_LABELS[lang]["req_types"])
        
        with st.container(border=True):
            with st.form("dynamic_request_form", clear_on_submit=True):
                
                if req_type in ["Xin nghỉ phép", "Leave Request"]:
                    sel_class = st.selectbox(DASHBOARD_LABELS[lang]["lbl_class"], options=list(sched_options.keys()), format_func=lambda x: sched_options[x])
                    c1, c2 = st.columns(2)
                    with c1: 
                        ngay_nghi = st.date_input("Ngày xin nghỉ" if lang == "vi" else "Leave Date")
                    with c2: 
                        ngay_day_bu = st.date_input("Ngày dạy bù" if lang == "vi" else "Makeup Date")
                    c3, c4 = st.columns(2)
                    with c3: 
                        gio_bd_bu = st.selectbox("Giờ bắt đầu dạy bù" if lang == "vi" else "Makeup Start Time", options=time_slots, index=time_slots.index("18:00") if "18:00" in time_slots else 0)
                    with c4: 
                        gio_kt_bu = st.selectbox("Giờ kết thúc dạy bù" if lang == "vi" else "Makeup End Time", options=time_slots, index=time_slots.index("19:30") if "19:30" in time_slots else 0)
                    ly_do = st.text_area(DASHBOARD_LABELS[lang]["lbl_reason"])

                elif req_type in ["Xin đổi lịch dạy", "Reschedule Request"]:
                    sel_class = st.selectbox(DASHBOARD_LABELS[lang]["lbl_class"], options=list(sched_options.keys()), format_func=lambda x: sched_options[x])
                    ngay_moi = st.date_input("Ngày học mới đề xuất" if lang == "vi" else "Proposed New Date")
                    c1, c2 = st.columns(2)
                    with c1: 
                        gio_bd_moi = st.selectbox("Giờ bắt đầu mới" if lang == "vi" else "New Start Time", options=time_slots, index=time_slots.index("18:00") if "18:00" in time_slots else 0)
                    with c2: 
                        gio_kt_moi = st.selectbox("Giờ kết thúc mới" if lang == "vi" else "New End Time", options=time_slots, index=time_slots.index("19:30") if "19:30" in time_slots else 0)
                    ly_do = st.text_area(DASHBOARD_LABELS[lang]["lbl_reason"])

                elif req_type in ["Đổi phương thức dạy", "Change Teaching Mode"]:
                    sel_class = st.selectbox(DASHBOARD_LABELS[lang]["lbl_class"], options=list(sched_options.keys()), format_func=lambda x: sched_options[x])
                    ngay_ap_dung = st.date_input("Ngày bắt đầu áp dụng" if lang == "vi" else "Effective Date")
                    c1, c2 = st.columns(2)
                    with c1:
                        opt_mode = ["Học Online", "Học Trực tiếp tại Trung tâm"] if lang == "vi" else ["Online", "In-person at Center"]
                        phuong_thuc = st.selectbox("Phương thức mới" if lang == "vi" else "New Mode", opt_mode)
                    with c2:
                        phong_hoc = st.text_input("Tên phòng (Nếu dạy trực tiếp)" if lang == "vi" else "Room Name (If in-person)", placeholder="VD: Phòng A102" if lang == "vi" else "e.g., Room A102")
                    ly_do = st.text_area(DASHBOARD_LABELS[lang]["lbl_reason"])

                elif req_type in ["Báo cáo sự cố thiết bị", "Report Equipment Issue"]:
                    c1, c2 = st.columns(2)
                    with c1:
                        phong_su_co = st.text_input("Phòng học xảy ra sự cố (*)" if lang == "vi" else "Room with issue (*)", placeholder="VD: Phòng Lab 1" if lang == "vi" else "e.g., Lab 1")
                    with c2:
                        thiet_bi_loi = st.text_input("Tên thiết bị lỗi (*)" if lang == "vi" else "Faulty Equipment Name (*)", placeholder="VD: Máy chiếu, Mic..." if lang == "vi" else "e.g., Projector, Mic...")
                    ly_do = st.text_area("Mô tả chi tiết tình trạng sự cố (*)" if lang == "vi" else "Detailed description of the issue (*)")

                if st.form_submit_button(DASHBOARD_LABELS[lang]["btn_submit"], type="primary", use_container_width=True):
                    chi_tiet = ""
                    if req_type in ["Xin nghỉ phép", "Leave Request"]:
                        chi_tiet = f"Lớp: {sched_options.get(sel_class, '')} | Nghỉ: {ngay_nghi.strftime('%d/%m/%Y')} | Bù: {ngay_day_bu.strftime('%d/%m/%Y')} ({gio_bd_bu}-{gio_kt_bu})"
                    elif req_type in ["Xin đổi lịch dạy", "Reschedule Request"]:
                        chi_tiet = f"Lớp: {sched_options.get(sel_class, '')} | Lịch mới: {ngay_moi.strftime('%d/%m/%Y')} ({gio_bd_moi}-{gio_kt_moi})"
                    elif req_type in ["Đổi phương thức dạy", "Change Teaching Mode"]:
                        pt = f"Trực tiếp ({phong_hoc})" if phuong_thuc in ["Học Trực tiếp tại Trung tâm", "In-person at Center"] else "Online"
                        chi_tiet = f"Lớp: {sched_options.get(sel_class, '')} | Áp dụng từ: {ngay_ap_dung.strftime('%d/%m/%Y')} | Dạng: {pt}"
                    elif req_type in ["Báo cáo sự cố thiết bị", "Report Equipment Issue"]:
                        chi_tiet = f"Phòng: {phong_su_co} | Thiết bị lỗi: {thiet_bi_loi}"

                    if not ly_do:
                        st.error("Vui lòng điền đầy đủ các thông tin bắt buộc (*)." if lang == "vi" else "Please fill in all required fields (*).")
                    else:
                        new_req = {
                            "id": str(int(time.time())),
                            "teacher_id": teacher_id,
                            "teacher_name": teacher_name,
                            "type": req_type,
                            "details": chi_tiet,
                            "reason": ly_do,
                            "status": "Chờ duyệt" if lang == "vi" else "Pending",
                            "created_at": datetime.now().strftime("%d/%m/%Y %H:%M")
                        }
                        
                        try:
                            headers = {"Authorization": f"Bearer {st.session_state.get('token', '')}"}
                            requests.post(f"{API_URL}/requests/create", json=new_req, headers=headers)
                        except: pass
                        
                        st.session_state.my_leave_requests.insert(0, new_req)
                        st.success(DASHBOARD_LABELS[lang]["success_msg"])
                        time.sleep(0.5)
                        st.rerun()

    with tab_list:
        if not st.session_state.my_leave_requests:
            st.info(DASHBOARD_LABELS[lang]["info_empty_req"])
        else:
            df_req = pd.DataFrame(st.session_state.my_leave_requests)
            df_display = df_req.rename(columns={
                "type": DASHBOARD_LABELS[lang]["df_cols"][1], 
                "details": DASHBOARD_LABELS[lang]["df_cols"][2],
                "reason": DASHBOARD_LABELS[lang]["df_cols"][3], 
                "status": DASHBOARD_LABELS[lang]["df_cols"][4], 
                "created_at": DASHBOARD_LABELS[lang]["df_cols"][0]
            })
            st.dataframe(
                df_display[DASHBOARD_LABELS[lang]["df_cols"]], 
                use_container_width=True, 
                hide_index=True
            )