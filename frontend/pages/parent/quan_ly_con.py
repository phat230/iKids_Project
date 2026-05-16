import streamlit as st
import requests
import pandas as pd
from datetime import datetime
import time
import os
 
# Cấu hình URL Backend
API_AUTH = "http://localhost:8000/api/auth"
API_TV3 = "http://localhost:8000/api/tv3"
 
st.set_page_config(page_title="Quản Lý Con Em - iKids", layout="wide")
 
# ================= HÀM ĐỌC FILE CSS =================
def load_css(file_name):
    """
    Tự động tìm file CSS trong thư mục frontend/CSS/
    file_name: tên file kèm thư mục con, ví dụ 'parent/quan_ly_con.css'
    """
    current_dir = os.path.dirname(os.path.abspath(__file__))
    css_root = os.path.abspath(os.path.join(current_dir, "../../CSS"))
    full_path = os.path.join(css_root, file_name)
 
    if os.path.exists(full_path):
        with open(full_path, "r", encoding="utf-8") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    else:
        st.warning(f"⚠️ Không tìm thấy file CSS tại: {full_path}")
 
# Tải CSS làm đẹp cho trang Quản lý
load_css("parent/quan_ly_con.css")
 
st.title(" Quản Lý Hồ Sơ & Phê Duyệt")
st.write("Tại đây, bạn có thể tạo tài khoản cho bé, quản lý ví tiền và phê duyệt các yêu cầu mua sắm.")
 
# 1. KIỂM TRA XÁC THỰC
parent_id = st.session_state.get("user_id")
token = st.session_state.get("access_token")
 
if not parent_id or not token:
    st.error("⚠️ Phiên làm việc hết hạn. Vui lòng đăng nhập lại.")
    st.stop()
 
headers = {"Authorization": f"Bearer {token}", "parent-id": str(parent_id)}
 
# --- HÀM HỖ TRỢ GỌI API ---
def fetch_parent_profile():
    try:
        res = requests.get(f"{API_TV3}/gamification/profile/{parent_id}", headers=headers)
        return res.json() if res.status_code == 200 else {}
    except:
        return {}

def fetch_my_children():
    try:
        res = requests.get(f"{API_TV3}/parent/my-children", headers=headers)
        return res.json() if res.status_code == 200 else []
    except:
        return []
 
def fetch_purchase_requests():
    try:
        res = requests.get(f"{API_TV3}/parent/purchase-requests", headers=headers)
        return res.json() if res.status_code == 200 else []
    except:
        return []

# ================= HIỂN THỊ SỐ DƯ VÍ PHỤ HUYNH & NÚT NẠP TIỀN =================
parent_profile = fetch_parent_profile()
parent_balance = parent_profile.get('balance', 0.0)

with st.container(border=True):
    col_wallet_text, col_wallet_metric = st.columns([3, 1])
    with col_wallet_text:
        st.markdown("###  Tài Khoản Phụ Huynh")
        st.write("Hệ thống sẽ khấu trừ trực tiếp vào số dư ví của bạn khi bạn thực hiện gửi tiền cho con em hoặc phê duyệt các yêu cầu mua sắm đồ dùng học tập.")
    with col_wallet_metric:
        st.metric(label="Số dư ví hiện tại", value=f"{parent_balance:,.0f} VNĐ")
        # Nút chuyển sang trang nạp tiền
        if st.button(" Nạp tiền ngay", use_container_width=True, type="primary"):
            st.switch_page("pages/parent/nap_tien.py")
st.write("")

# --- GIAO DIỆN CÁC TÁC VỤ ---
tab_list, tab_approve, tab_add = st.tabs([
    " Danh sách con em", 
    " Phê duyệt mua sắm", 
    " Tạo tài khoản mới"
])
 
# TAB 1: DANH SÁCH & QUẢN LÝ VÍ CON
with tab_list:
    st.subheader("Các con đang theo học")
    children = fetch_my_children()
    
    if not children:
        st.info("Bạn chưa liên kết với tài khoản học sinh nào.")
    else:
        for child in children:
            with st.container(border=True):
                col1, col2, col3 = st.columns([2, 2, 2])
                with col1:
                    st.markdown(f"**Bé:** {child['name']}")
                    st.caption(f"Email: {child['email']}")
                with col2:
                    balance = child.get('balance', 0)
                    st.metric("Ví của con", f"{balance:,.0f} VNĐ")
                with col3:
                    with st.expander(" Giao dịch ví của con"):
                        amount = st.number_input("Số tiền (VNĐ)", min_value=0, step=10000, key=f"amt_{child['id']}")
                        c_btn1, c_btn2 = st.columns(2)
                        
                        if c_btn1.button("Gửi tiền", key=f"send_{child['id']}", use_container_width=True, type="primary"):
                            if amount <= 0:
                                st.warning("Vui lòng nhập số tiền")
                            elif amount > parent_balance:
                                st.error(f"Số dư ví phụ huynh không đủ (Hiện có: {parent_balance:,.0f} VNĐ).")
                            else:
                                with st.spinner("Đang gửi tiền..."):
                                    res = requests.post(f"{API_TV3}/parent/transfer-to-child", 
                                                        json={"child_id": child['id'], "amount": amount}, headers=headers)
                                    if res.status_code == 200:
                                        st.success(f"Đã chuyển {amount:,.0f} VNĐ thành công!")
                                        st.toast(f" Bé {child['name']} đã nhận được thông báo tiền về!", )
                                        time.sleep(1)
                                        st.rerun()
                                    else:
                                        st.error("Không thể hoàn tất giao dịch giao tiếp máy chủ.")
 
                        if c_btn2.button("Rút tiền", key=f"withdraw_{child['id']}", use_container_width=True):
                            if amount <= 0:
                                st.warning("Vui lòng nhập số tiền")
                            else:
                                with st.spinner("Đang rút tiền..."):
                                    res = requests.post(f"{API_TV3}/parent/withdraw-from-child", 
                                                        json={"child_id": child['id'], "amount": amount}, headers=headers)
                                    if res.status_code == 200:
                                        st.success(f"Đã rút {amount:,.0f} VNĐ về ví của bạn.")
                                        st.toast(" Đã gửi thông báo rút tiền cho bé.", icon="ℹ️")
                                        time.sleep(1)
                                        st.rerun()
                                    else:
                                        st.error("Số dư của bé không đủ để rút.")
 
# TAB 2: PHÊ DUYỆT MUA SẮM 
with tab_approve:
    st.subheader("Yêu cầu mua dụng cụ học tập")
    requests_list = fetch_purchase_requests()
    
    if not requests_list:
        st.success(" Không có yêu cầu nào cần xử lý.")
    else:
        for req in requests_list:
            with st.container(border=True):
                c_info, c_action = st.columns([3, 1])
                with c_info:
                    st.markdown(f"**{req['child_name']}** muốn mua: `{req['product_name']}`")
                    st.markdown(f"Giá tiền: :orange[**{req['price']:,} VNĐ**]")
                with c_action:
                    if parent_balance < req['price']:
                        st.error("Ví của bạn không đủ số dư")
                        st.button(" Duyệt", key=f"app_{req['id']}", type="primary", use_container_width=True, disabled=True)
                    else:
                        if st.button(" Duyệt", key=f"app_{req['id']}", type="primary", use_container_width=True):
                            requests.post(f"{API_TV3}/parent/approve-purchase/{req['id']}", 
                                          json={"action": "approve"}, headers=headers)
                            st.rerun()
                            
                    if st.button(" Từ Chối", key=f"rej_{req['id']}", use_container_width=True):
                        requests.post(f"{API_TV3}/parent/approve-purchase/{req['id']}", 
                                      json={"action": "reject"}, headers=headers)
                        st.rerun()
 
# TAB 3: TẠO TÀI KHOẢN MỚI
with tab_add:
    with st.form("create_student_form"):
        st.subheader("Đăng ký thêm tài khoản cho bé")
        stu_name = st.text_input("Họ và tên của bé")
        stu_email = st.text_input("Email đăng nhập của bé")
        stu_password = st.text_input("Mật khẩu", type="password")
        
        if st.form_submit_button("Tạo & Liên Kết Tài Khoản", use_container_width=True):
            if not stu_name or not stu_email or not stu_password:
                st.warning("Vui lòng điền đầy đủ thông tin.")
            else:
                payload = {"name": stu_name, "email": stu_email, "password": stu_password, "role": "student"}
                try:
                    res = requests.post(f"{API_AUTH}/parent/create-student", json=payload, headers=headers)
                    if res.status_code == 200:
                        st.success("🎉 Tạo tài khoản thành công!")
                        st.balloons()
                        time.sleep(2)
                        st.rerun()
                    else:
                        st.error(f"Lỗi: {res.json().get('detail', 'Lỗi hệ thống')}")
                except:
                    st.error("Lỗi kết nối.")