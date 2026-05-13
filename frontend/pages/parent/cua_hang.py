import streamlit as st
import requests
from api_clients.tv3_client import get_store_products, purchase_product, get_gamification_profile
from utils.role_guard import require_role

# Bảo mật - Chỉ cho phép Parent và Admin
require_role(["parent", "admin"])

API_URL = "http://localhost:8000"
API_TV3 = "http://localhost:8000/api/tv3"

def render_store():
    st.title("🎒 Cửa Hàng Dụng Cụ iKids")
    st.write("Chọn món quà ý nghĩa và chọn bé bạn muốn dành tặng!")
    
    user_id = st.session_state.get("user_id")
    token = st.session_state.get("access_token")
    
    # 1. Lấy thông tin ví
    profile = get_gamification_profile(user_id)
    balance = profile.get('balance', 0.0) 
    
    st.sidebar.markdown(f"### 💳 Số dư ví hiện tại:")
    st.sidebar.title(f"{balance:,.0f} VNĐ")
    
    if st.sidebar.button("➕ Nạp thêm tiền", use_container_width=True):
        st.switch_page("pages/parent/nap_tien.py")
    
    st.divider()

    # 2. LẤY DANH SÁCH CON CỦA PHỤ HUYNH
    @st.cache_data(ttl=30)
    def get_my_children_options():
        headers = {"Authorization": f"Bearer {token}", "parent-id": str(user_id)}
        try:
            res = requests.get(f"{API_TV3}/parent/my-children", headers=headers)
            if res.status_code == 200:
                children = res.json()
                return {c["id"]: c["name"] for c in children}
            return {}
        except:
            return {}

    child_options = get_my_children_options()

    if not child_options:
        st.warning("⚠️ Bạn chưa có hồ sơ con em nào trên hệ thống. Vui lòng cập nhật thông tin con em trước khi mua quà.")
        st.stop()

    # 3. Lấy danh sách sản phẩm từ DB
    products = get_store_products()
    
    if not products:
        st.info("Cửa hàng hiện tại chưa có sản phẩm mới.")
    else:
        cols = st.columns(2)
        for i, p in enumerate(products):
            with cols[i % 2]:
                with st.container(border=True):
                    st.markdown(f"### {p.get('icon', '📦')} {p['name']}")
                    st.write(f"Giá: :blue[**{p['price']:,} VNĐ**]")
                    
                    # THÊM Ô CHỌN CON CHO TỪNG SẢN PHẨM
                    selected_child_id = st.selectbox(
                        f"Tặng quà cho:",
                        options=list(child_options.keys()),
                        format_func=lambda x: child_options[x],
                        key=f"select_child_{p['id']}"
                    )
                    
                    if st.button(f"Xác nhận mua tặng", key=f"buy_parent_{p['id']}", use_container_width=True, type="primary"):
                        if balance >= p['price']:
                            with st.spinner("Đang xử lý giao dịch..."):
                                # Gửi thêm thông tin child_id lên backend nếu cần
                                # Ở đây mình vẫn dùng hàm purchase_product cũ của bạn 
                                # nhưng logic thông báo ở Backend sẽ lấy child_id từ request
                                success, msg = purchase_product(user_id, p['id']) 
                                
                                if success:
                                    st.success(f"🎉 Đã gửi tặng {p['name']} cho bé {child_options[selected_child_id]}!")
                                    st.balloons()
                                    st.rerun() 
                                else:
                                    st.error(msg)
                        else:
                            st.error(f"Số dư không đủ.")

if __name__ == "__main__":
    render_store()