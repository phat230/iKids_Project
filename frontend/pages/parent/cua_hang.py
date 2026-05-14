import streamlit as st
import requests
import os
from api_clients.tv3_client import get_store_products, purchase_product, get_gamification_profile
from utils.role_guard import require_role

# Bảo mật - Chỉ cho phép Parent và Admin
require_role(["parent", "admin"])

# ================= HÀM ĐỌC FILE CSS (SỬA LỖI ĐƯỜNG DẪN TUYỆT ĐỐI) =================
def load_css(file_name):
    """
    Tự động tìm file CSS trong thư mục frontend/CSS/
    file_name: tên file kèm thư mục con, ví dụ 'parent/cua_hang.css'
    """
    # Lấy đường dẫn tuyệt đối đến thư mục chứa file cua_hang.py hiện tại
    current_dir = os.path.dirname(os.path.abspath(__file__)) # frontend/pages/parent
    
    # Tìm đường dẫn đến thư mục CSS (lùi 2 cấp từ pages/parent/ rồi vào CSS/)
    css_root = os.path.abspath(os.path.join(current_dir, "../../CSS"))
    full_path = os.path.join(css_root, file_name)

    if os.path.exists(full_path):
        with open(full_path, "r", encoding="utf-8") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    else:
        st.warning(f"⚠️ Không tìm thấy file CSS tại: {full_path}")

API_URL = "http://localhost:8000"
API_TV3 = "http://localhost:8000/api/tv3"

def render_store():
    # Tải CSS làm đẹp Cửa hàng (Chỉ truyền phần sau thư mục CSS/)
    load_css("parent/cua_hang.css")

    st.title("🛍️ Cửa Hàng Dụng Cụ iKids")
    st.write("Chọn món quà ý nghĩa và chọn bé bạn muốn dành tặng!")
    
    user_id = st.session_state.get("user_id")
    token = st.session_state.get("access_token")
    
    if not user_id or not token:
        st.error("⚠️ Vui lòng đăng nhập để thực hiện mua sắm.")
        st.stop()

    # 1. Lấy thông tin ví của phụ huynh
    profile = get_gamification_profile(user_id)
    balance = profile.get('balance', 0.0) 
    
    st.sidebar.markdown(f"### 💳 Số dư ví hiện tại:")
    st.sidebar.title(f"{balance:,.0f} VNĐ")
    
    if st.sidebar.button("➕ Nạp thêm tiền", use_container_width=True, type="primary"):
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
        st.warning("⚠️ Bạn chưa có hồ sơ con em nào trên hệ thống. Vui lòng tạo tài khoản cho bé trước khi mua quà.")
        st.stop()

    # 3. Lấy danh sách sản phẩm từ DB
    products = get_store_products()
    
    if not products:
        st.info("Cửa hàng hiện tại chưa có sản phẩm mới.")
    else:
        # Hiển thị dạng lưới 2 cột
        cols = st.columns(2)
        for i, p in enumerate(products):
            with cols[i % 2]:
                with st.container(border=True):
                    # Hiển thị Icon và Tên sản phẩm
                    st.markdown(f"### {p.get('icon', '🎁')} {p['name']}")
                    st.markdown(f"Giá: :blue[**{p['price']:,} VNĐ**]")
                    
                    # Ô CHỌN CON CHO TỪNG SẢN PHẨM
                    selected_child_id = st.selectbox(
                        f"Tặng quà cho:",
                        options=list(child_options.keys()),
                        format_func=lambda x: child_options[x],
                        key=f"select_child_{p['id']}"
                    )
                    
                    # Nút xác nhận mua
                    if st.button(f"Xác nhận mua tặng", key=f"buy_parent_{p['id']}", use_container_width=True, type="primary"):
                        if balance >= p['price']:
                            with st.spinner("Đang xử lý giao dịch..."):
                                # Gọi API mua sản phẩm
                                success, msg = purchase_product(user_id, p['id']) 
                                
                                if success:
                                    st.success(f"🎉 Đã gửi tặng {p['name']} cho bé {child_options[selected_child_id]}!")
                                    st.balloons()
                                    time.sleep(1) # Đợi 1 chút để xem hiệu ứng
                                    st.rerun() 
                                else:
                                    st.error(msg)
                        else:
                            st.error(f"Số dư ví không đủ để mua sản phẩm này.")

if __name__ == "__main__":
    render_store()