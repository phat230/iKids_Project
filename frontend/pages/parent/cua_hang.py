import streamlit as st
from api_clients.tv3_client import get_store_products, purchase_product, get_gamification_profile
from utils.role_guard import require_role

# 4.3: Bảo mật - Chặn truy cập trái phép, chỉ cho phép Parent và Admin
require_role(["parent", "admin"])

def render_store():
    # 1. Tiêu đề
    st.title("🎒 Cửa Hàng Dụng Cụ iKids")
    st.write("Sử dụng số dư trong ví để mua các món đồ học tập tặng cho con em mình!")
    
    user_id = st.session_state.get("user_id")
    
    # 2. Lấy số dư ví thực tế từ Backend
    profile = get_gamification_profile(user_id)
    balance = profile.get('balance', 0.0) 
    
    # Hiển thị số dư ở Sidebar
    st.sidebar.markdown(f"### 💳 Số dư ví hiện tại:")
    st.sidebar.title(f"{balance:,.0f} VNĐ")
    
    if st.sidebar.button("➕ Nạp thêm tiền", use_container_width=True):
        # Đảm bảo đường dẫn này khớp với app.py của bạn
        try:
            st.switch_page("pages/parent/nap_tien.py")
        except:
            st.error("Không tìm thấy trang nạp tiền. Vui lòng kiểm tra lại cấu trúc thư mục.")
    
    st.divider()

    # 3. Lấy danh sách sản phẩm từ DB
    products = get_store_products()
    
    if not products:
        st.info("Cửa hàng hiện tại chưa có sản phẩm mới. Vui lòng quay lại sau!")
    else:
        # Hiển thị sản phẩm theo lưới 2 cột
        cols = st.columns(2)
        for i, p in enumerate(products):
            with cols[i % 2]:
                with st.container(border=True):
                    # Hiển thị thông tin sản phẩm
                    st.markdown(f"### {p.get('icon', '📦')} {p['name']}")
                    st.write(f"Giá: :blue[**{p['price']:,} VNĐ**]") # Thêm màu sắc cho giá tiền
                    st.caption(f"Loại: {p.get('type', 'Dụng cụ').capitalize()}")
                    
                    # Nút mua hàng
                    if st.button(f"Mua tặng con", key=f"buy_parent_{p['id']}", use_container_width=True, type="secondary"):
                        if balance >= p['price']:
                            with st.spinner("Đang thực hiện giao dịch..."):
                                success, msg = purchase_product(user_id, p['id']) 
                                if success:
                                    st.success(f"🎉 Đã mua thành công {p['name']}!")
                                    st.balloons()
                                    st.rerun() 
                                else:
                                    st.error(msg)
                        else:
                            st.error(f"Số dư không đủ. Cần thêm {(p['price'] - balance):,.0f} VNĐ.")

if __name__ == "__main__":
    render_store()