import streamlit as st
import requests
import pandas as pd

st.set_page_config(page_title="Admin Dashboard - iKids", layout="wide", initial_sidebar_state="expanded")

API_URL = "http://127.0.0.1:8000"

def fetch_pending_requests():
    try:
        res = requests.get(f"{API_URL}/pending-requests")
        return res.json() if res.status_code == 200 else []
    except: return []

def fetch_history_requests():
    try:
        res = requests.get(f"{API_URL}/request-history")
        return res.json() if res.status_code == 200 else []
    except: return []

# --- CSS CUSTOM ---
st.markdown("""
<style>
    .metric-card {
        background-color: #ffffff; border-radius: 10px; padding: 20px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05); border-left: 5px solid;
    }
    .tv1-border { border-color: #3b82f6; }
    .tv2-border { border-color: #10b981; }
    .tv3-border { border-color: #8b5cf6; }
</style>
""", unsafe_allow_html=True)

# --- HEADER ---
st.title("🛡️ Bảng Điều Khiển Quản Trị Trung Tâm")
st.markdown("*Hệ thống giám sát vận hành đồng bộ: Lịch dạy (TV1), Học thuật & AI (TV2), Cộng đồng (TV3)*")
st.write("---")

# --- 1. CHỈ SỐ TỔNG QUAN ---
pending_requests = fetch_pending_requests()
total_pending = len(pending_requests)

col1, col2, col3, col4 = st.columns(4)
with col1:
    st.markdown(f"""<div class="metric-card tv1-border">
        <p style="color:#64748b; margin:0; font-size:14px; font-weight:bold;">ĐƠN GV CHỜ DUYỆT (TV1)</p>
        <h2 style="color:#0f172a; margin:0; font-size:32px;">{total_pending}</h2>
        <p style="color:#ef4444; margin:0; font-size:12px;">Dữ liệu trực tiếp từ MongoDB</p></div>""", unsafe_allow_html=True)
with col2:
    st.markdown("""<div class="metric-card tv1-border">
        <p style="color:#64748b; margin:0; font-size:14px; font-weight:bold;">CA DẠY HÔM NAY (TV1)</p>
        <h2 style="color:#0f172a; margin:0; font-size:32px;">--</h2>
        <p style="color:#10b981; margin:0; font-size:12px;">Đang cập nhật luồng API</p></div>""", unsafe_allow_html=True)
with col3:
    st.markdown("""<div class="metric-card tv2-border">
        <p style="color:#64748b; margin:0; font-size:14px; font-weight:bold;">NHẬT KÝ ĐÃ NỘP (TV2)</p>
        <h2 style="color:#0f172a; margin:0; font-size:32px;">--</h2>
        <p style="color:#f59e0b; margin:0; font-size:12px;">Đang cập nhật luồng API</p></div>""", unsafe_allow_html=True)
with col4:
    st.markdown("""<div class="metric-card tv3-border">
        <p style="color:#64748b; margin:0; font-size:14px; font-weight:bold;">ĐƠN TỪ PHỤ HUYNH (TV3)</p>
        <h2 style="color:#0f172a; margin:0; font-size:32px;">--</h2>
        <p style="color:#3b82f6; margin:0; font-size:12px;">Đang cập nhật luồng API</p></div>""", unsafe_allow_html=True)

st.write("<br>", unsafe_allow_html=True)

# --- LAYOUT CHÍNH: CHIA 2 CỘT ---
left_col, right_col = st.columns([1.6, 1])

# =========================================================
# CỘT TRÁI: TV1 (VẬN HÀNH & NHÂN SỰ)
# =========================================================
with left_col:
    st.subheader("📑 1. Phê duyệt & Điều phối (Thành viên 1)")
    
    # ---------------------------------------------------------
    # PHẦN A: ĐƠN CHỜ DUYỆT 
    # ---------------------------------------------------------
    st.markdown(f"**A. Yêu cầu đang chờ duyệt ({total_pending})**")
    if not pending_requests:
        st.success("✨ Tuyệt vời! Hiện tại không có đơn hỗ trợ nào cần xử lý.")
    else:
        for req in pending_requests:
            with st.container(border=True):
                c_info, c_btn = st.columns([3, 1])
                
                with c_info:
                    icon = "🔴" if "nghỉ" in req.get('type', '').lower() else "🔄"
                    st.markdown(f"<h6 style='margin-bottom: 5px;'>{icon} {req.get('type', '')} - GV: {req.get('teacher_name', '')}</h6>", unsafe_allow_html=True)
                    st.caption(f"**Lớp:** {req.get('class_name', '')} | **Ngày:** {req.get('date', '')}")
                    st.markdown(f"**Lý do:** {req.get('reason', '')}")
                
                with c_btn:
                    if st.button("✅ Phê duyệt", key=f"app_{req['id']}", type="primary", use_container_width=True):
                        res = requests.post(f"{API_URL}/approve/{req['id']}")
                        if res.status_code == 200:
                            st.rerun()
                    if st.button("❌ Từ chối", key=f"rej_{req['id']}", use_container_width=True):
                        res = requests.post(f"{API_URL}/reject/{req['id']}")
                        if res.status_code == 200:
                            st.rerun()

    st.write("---")

    # ---------------------------------------------------------
    # PHẦN B: LỊCH SỬ XÉT DUYỆT (Có thêm Cột LÝ DO và THỜI GIAN)
    # ---------------------------------------------------------
    st.markdown("**B. Lịch sử xét duyệt gần đây**")
    history_requests = fetch_history_requests()
    
    if not history_requests:
        st.info("Chưa có lịch sử xét duyệt nào.")
    else:
        history_data = []
        for h in history_requests:
            status_text = "✅ Đã duyệt" if h.get('status') == "approved" else "❌ Từ chối"
            
            # Xử lý format thời gian
            raw_time = h.get("updated_at")
            time_str = "Chưa rõ"
            if raw_time:
                try:
                    time_obj = pd.to_datetime(raw_time)
                    time_str = time_obj.strftime("%d/%m/%Y %H:%M")
                except:
                    pass
                    
            history_data.append({
                "Giáo viên": h.get("teacher_name", ""),
                "Loại đơn": h.get("type", ""),
                "Lý do": h.get("reason", ""),
                "Lớp học": h.get("class_name", ""),
                "Thời gian xử lý": time_str,
                "Trạng thái": status_text
            })
            
        df_history = pd.DataFrame(history_data)
        st.dataframe(df_history, use_container_width=True, hide_index=True)


# =========================================================
# CỘT PHẢI: TV2 & TV3 (CHUYÊN MÔN & CỘNG ĐỒNG)
# =========================================================
with right_col:
    st.subheader("📊 2. Học thuật & Tương tác")
    
    with st.container(border=True):
        st.markdown("**A. Báo cáo Video AI & Nhật ký (TV2)**")
        st.caption("Đo lường mức độ tương tác và sử dụng học liệu của giáo viên.")
        
        # Đã xóa dữ liệu ảo (Mock Data). Chờ API kết nối từ TV2
        st.info("🕒 Đang chờ kết nối dữ liệu từ module Học thuật (TV2)...")
        
        if st.button("Xem chi tiết Nhật ký chưa nộp", use_container_width=True, disabled=True):
            pass

    with st.container(border=True):
        st.markdown("**B. Trung tâm Tương tác Phụ huynh (TV3)**")
        st.caption("Các yêu cầu từ App Phụ huynh được hệ thống tự động Convert thành Request.")
        
        # Đã xóa dữ liệu ảo (Mock Data). Chờ API kết nối từ TV3
        st.info("🕒 Đang chờ kết nối dữ liệu từ module Phụ huynh (TV3)...")
        
        if st.button("Chuyển yêu cầu cho Vận Hành xử lý", use_container_width=True, disabled=True):
            pass