import streamlit as st
from api_clients.tv3_client import get_gamification_profile, get_store_products, purchase_product

# Không gọi st.set_page_config nếu đã gọi ở app.py

st.title("🛒 Cửa Hàng Học Liệu iKids")
st.write("Mua sắm sách, dụng cụ thí nghiệm và phụ kiện học tập chính hãng.")

user_id = st.session_state.get("user_id")

if not user_id:
    st.error("Vui lòng đăng nhập để xem cửa hàng.")
    st.stop()

# 1. Lấy số dư ví VNĐ thực tế
profile = get_gamification_profile(user_id)
balance = profile.get('balance', 0.0)

# Hiển thị số dư định dạng VNĐ
st.info(f"💳 **Số dư tài khoản của bạn:** {balance:,.0f} VNĐ")
st.divider()

# 2. Hiển thị danh sách sản phẩm thực tế
products = get_store_products()

if not products:
    st.write("Cửa hàng hiện tại chưa có sản phẩm mới.")
else:
    cols = st.columns(2)
    for index, item in enumerate(products):
        col = cols[index % 2]
        
        with col:
            with st.container(border=True):
                # Hiển thị Icon, Tên và Giá tiền VNĐ
                st.markdown(f"### {item['icon']} {item['name']}")
                st.markdown(f"**Giá bán:** `{item['price']:,.0f} VNĐ`")
                st.caption(f"Loại: {item['type'].capitalize()}")
                
                if st.button("Thanh toán ngay", key=f"btn_buy_{item['id']}", use_container_width=True):
                    if balance < item['price']:
                        st.warning(f"Số dư không đủ. Bạn cần nạp thêm {item['price'] - balance:,.0f} VNĐ để mua sản phẩm này.")
                    else:
                        # Gọi API mua hàng thực tế
                        success, msg = purchase_product(user_id, item['id'])
                        if success:
                            st.success(msg)
                            st.balloons()
                            st.rerun()
                        else:
                            st.error(msg)