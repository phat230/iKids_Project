import streamlit as st
import requests
import time
from api_clients.tv3_client import get_store_products, purchase_product, get_gamification_profile
from utils.role_guard import require_role

require_role(["parent", "admin"])
BACKEND_URL = "http://localhost:8000"
API_TV3 = "http://localhost:8000/api/tv3"

def render_store():
    st.title(" Cửa Hàng Quà Tặng iKids")
    
    user_id = st.session_state.get("user_id")
    token = st.session_state.get("access_token")
    
    profile = get_gamification_profile(user_id)
    balance = profile.get('balance', 0.0) 
    st.sidebar.markdown(f"###  Số dư ví: {balance:,.0f} VNĐ")
    
    # Lấy danh sách con
    headers = {"Authorization": f"Bearer {token}", "parent-id": str(user_id)}
    try:
        res = requests.get(f"{API_TV3}/parent/my-children", headers=headers)
        children = res.json() if res.status_code == 200 else []
        
        # Thử lấy full_name, nếu không có thì lấy name, cuối cùng là dùng 4 số cuối ID để phân biệt
        child_options = {
            c["id"]: (c.get("full_name") or c.get("name") or f"Bé ({str(c['id'])[-4:]})") 
            for c in children
        }
    except Exception as e: 
        child_options = {}

    if not child_options:
        st.warning("⚠️ Chưa có hồ sơ con em.")
        st.stop()

    products = get_store_products()
    if not products:
        st.info("Cửa hàng đang cập nhật.")
    else:
        # --- HIỂN THỊ LƯỚI 4 CỘT ---
        num_cols = 4
        for i in range(0, len(products), num_cols):
            row_products = products[i:i + num_cols]
            cols = st.columns(num_cols)
            for idx, p in enumerate(row_products):
                p_id = p.get('id', p.get('_id'))
                with cols[idx]:
                    with st.container(border=True):
                        img_path = p.get('image_url')
                        full_img_url = f"{BACKEND_URL}/{img_path}" if img_path and img_path.startswith("static/") else (img_path or "https://via.placeholder.com/300")
                        
                        st.image(full_img_url, use_container_width=True)
                        st.markdown(f"**{p['name']}**")
                        st.markdown(f"Giá: :blue[{p['price']:,} VNĐ]")
                        
                        selected_child_id = st.selectbox(
                            "Tặng cho:", 
                            options=list(child_options.keys()), 
                            format_func=lambda x: child_options[x], 
                            key=f"sel_{p_id}"
                        )
                        
                        if st.button(f"Xác nhận tặng", key=f"pbuy_{p_id}", use_container_width=True, type="primary"):
                            if balance >= p['price']:
                                # Truyền thêm target_student_id để backend biết tặng cho ai
                                success, msg = purchase_product(user_id, p_id, target_student_id=selected_child_id) 
                                if success:
                                    st.success(f"Đã tặng quà cho {child_options[selected_child_id]}!")
                                    st.balloons(); time.sleep(1); st.rerun()
                                else: st.error(msg)
                            else: st.error("Không đủ số dư")

if __name__ == "__main__":
    render_store()