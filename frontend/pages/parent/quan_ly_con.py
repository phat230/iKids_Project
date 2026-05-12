import streamlit as st
import requests
import pandas as pd
from datetime import datetime

# Cấu hình URL Backend
API_AUTH = "http://localhost:8000/api/auth"
API_TV3 = "http://localhost:8000/api/tv3"

st.set_page_config(page_title="Quản Lý Con Em - iKids", layout="wide")

st.title("👨‍👩‍👦 Quản Lý Hồ Sơ & Phê Duyệt")
st.write("Tại đây, bạn có thể tạo tài khoản cho bé để bé tham gia vào hệ thống học tập iKids, theo dõi ví tiền và phê duyệt các yêu cầu mua sắm.")

# 1. KIỂM TRA XÁC THỰC
# Lấy ID thực tế của phụ huynh từ session
parent_id = st.session_state.get("user_id")
token = st.session_state.get("access_token")

if not parent_id or not token:
    st.error("🔑 Phiên làm việc hết hạn. Vui lòng đăng nhập lại.")
    st.stop()

headers = {"Authorization": f"Bearer {token}", "parent-id": str(parent_id)}

# --- HÀM HỖ TRỢ GỌI API ---
def fetch_my_children():
    """Lấy danh sách các bé đã liên kết với phụ huynh này"""
    try:
        # API này cần được triển khai ở backend/modules/tv3_community/router.py
        res = requests.get(f"{API_TV3}/parent/my-children", headers=headers)
        return res.json() if res.status_code == 200 else []
    except:
        return []

def fetch_purchase_requests():
    """Lấy danh sách yêu cầu mua đồ đang chờ duyệt"""
    try:
        res = requests.get(f"{API_TV3}/parent/purchase-requests", headers=headers)
        return res.json() if res.status_code == 200 else []
    except:
        return []

# --- GIAO DIỆN CHÍNH ---
tab_list, tab_approve, tab_add = st.tabs([
    "👥 Danh sách con em", 
    "🔔 Phê duyệt mua sắm", 
    "📝 Tạo tài khoản mới"
])

# TAB 1: DANH SÁCH & QUẢN LÝ VÍ
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
                    # Hiển thị số dư ví của con 
                    balance = child.get('balance', 0)
                    st.metric("Ví của con", f"{balance:,.0f} VNĐ")
                with col3:
                    # Tính năng nạp/rút tiền cho con 
                    with st.expander("💳 Quản lý tiền của con"):
                        amount = st.number_input("Số tiền (VNĐ)", min_value=0, step=10000, key=f"amt_{child['id']}")
                        c_btn1, c_btn2 = st.columns(2)
                        if c_btn1.button("Gửi tiền", key=f"send_{child['id']}", use_container_width=True):
                            # API xử lý chuyển tiền nội bộ từ ví mẹ sang con
                            requests.post(f"{API_TV3}/parent/transfer-to-child", 
                                          json={"child_id": child['id'], "amount": amount}, headers=headers)
                            st.rerun()
                        if c_btn2.button("Rút tiền", key=f"withdraw_{child['id']}", use_container_width=True):
                            requests.post(f"{API_TV3}/parent/withdraw-from-child", 
                                          json={"child_id": child['id'], "amount": amount}, headers=headers)
                            st.rerun()

# TAB 2: PHÊ DUYỆT MUA SẮM 
with tab_approve:
    st.subheader("Yêu cầu mua dụng cụ học tập")
    st.write("Khi con chọn món đồ trong cửa hàng, yêu cầu sẽ hiện tại đây để bạn phê duyệt.")
    
    requests_list = fetch_purchase_requests()
    
    if not requests_list:
        st.success("✨ Không có yêu cầu nào cần xử lý.")
    else:
        for req in requests_list:
            with st.container(border=True):
                c_info, c_action = st.columns([3, 1])
                with c_info:
                    st.markdown(f"**{req['child_name']}** muốn mua: `{req['product_name']}`")
                    st.markdown(f"Giá tiền: :orange[**{req['price']:,} VNĐ**]")
                with c_action:
                    if st.button("✅ Duyệt", key=f"app_{req['id']}", type="primary", use_container_width=True):
                        requests.post(f"{API_TV3}/parent/approve-purchase/{req['id']}", 
                                      json={"action": "approve"}, headers=headers)
                        st.rerun()
                    if st.button("❌ Từ chối", key=f"rej_{req['id']}", use_container_width=True):
                        requests.post(f"{API_TV3}/parent/approve-purchase/{req['id']}", 
                                      json={"action": "reject"}, headers=headers)
                        st.rerun()

# TAB 3: TẠO TÀI KHOẢN MỚI
with tab_add:
    with st.form("create_student_form"):
        st.subheader("Đăng ký thêm tài khoản cho bé")
        stu_name = st.text_input("Họ và tên của bé")
        stu_email = st.text_input("Email đăng nhập của bé (Có thể dùng email phụ của bạn)")
        stu_password = st.text_input("Mật khẩu", type="password")
        
        submit = st.form_submit_button("Tạo & Liên Kết Tài Khoản", use_container_width=True)
        
        if submit:
            if not stu_name or not stu_email or not stu_password:
                st.warning("Vui lòng điền đầy đủ thông tin.")
            else:
                payload = {
                    "name": stu_name,
                    "email": stu_email,
                    "password": stu_password,
                    "role": "student"
                }
                try:
                    # Gửi parent-id qua header để backend tự động liên kết
                    res = requests.post(f"{API_AUTH}/parent/create-student", json=payload, headers=headers)
                    if res.status_code == 200:
                        st.success("🎉 Tạo tài khoản thành công! Bé đã được tự động thêm vào danh sách quản lý.")
                        st.balloons()
                    else:
                        st.error(f"Lỗi: {res.json().get('detail', 'Không thể tạo tài khoản')}")
                except Exception:
                    st.error("Lỗi kết nối đến máy chủ.")