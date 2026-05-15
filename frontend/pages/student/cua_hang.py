import streamlit as st
import os
import time
from api_clients.tv3_client import get_store_products, get_gamification_profile, purchase_product, request_purchase
from utils.role_guard import require_role

require_role(["student"])
BACKEND_URL = "http://localhost:8000"

def show_student_store():
    st.title("🎒 Cửa Hàng iKids")
    st.write("Em có thể dùng tiền tích lũy để đổi quà nhé!")
    
    user_id = st.session_state.get("user_id")
    profile = get_gamification_profile(user_id)
    balance = profile.get('balance', 0)
    
    st.sidebar.markdown("### 💰 Ví tiền của em")
    st.sidebar.subheader(f":green[{balance:,.0f} VNĐ]") 
    st.divider()

    products = get_store_products()
    
    if not products:
        st.info("Hiện chưa có sản phẩm nào.")
        return

    # --- HIỂN THỊ LƯỚI 4 CỘT ---
    num_cols = 4
    rows = [products[i:i + num_cols] for i in range(0, len(products), num_cols)]

    for row in rows:
        cols = st.columns(num_cols)
        for idx, p in enumerate(row):
            p_id = p.get('id', p.get('_id'))
            with cols[idx]:
                with st.container(border=True):
                    img_url = p.get('image_url')
                    full_img_path = f"{BACKEND_URL}/{img_url}" if img_url and img_url.startswith("static/") else (img_url or "https://via.placeholder.com/300")
                    
                    st.image(full_img_path, use_container_width=True)
                    st.markdown(f"**{p['name']}**")
                    st.write(f":orange[**{p['price']:,} VNĐ**]")
                    
                    if balance >= p['price']:
                        if st.button(f"🛒 Mua", key=f"buy_{p_id}", use_container_width=True, type="primary"):
                            success, msg = purchase_product(user_id, p_id)
                            if success:
                                st.success("Thành công!")
                                st.balloons(); time.sleep(1); st.rerun()
                            else: st.error(msg)
                    else:
                        if st.button(f"🙏 Xin Mẹ", key=f"req_{p_id}", use_container_width=True):
                            success, msg = request_purchase(user_id, p_id, p['name'], p['price'])
                            if success: st.info("Đã gửi yêu cầu!")
                            else: st.error(msg)

if __name__ == "__main__":
    show_student_store()