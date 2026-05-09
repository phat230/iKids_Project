import streamlit as st
from api_clients.tv3_client import get_store_products, purchase_product, get_gamification_profile
from utils.role_guard import require_role

# 4.3: Bảo mật - Chỉ cho phép Học sinh truy cập (Học sinh tự mua bằng ví cá nhân)
require_role(["student"])

def show_student_store():
    # 1. Cấu hình tiêu đề trang
    st.title("🛍️ Cửa Hàng iKids")
    st.write("Dùng số tiền em tích lũy được từ việc học để đổi lấy những món quà yêu thích nhé!")
    
    user_id = st.session_state.get("user_id")
    
    if not user_id:
        st.error("Vui lòng đăng nhập để tiếp tục.")
        st.stop()
    
    # 2. Lấy số dư thực tế từ hệ thống Gamification
    profile = get_gamification_profile(user_id)
    balance = profile.get('balance', 0)
    
    # Hiển thị số dư hiện có một cách nổi bật ở Sidebar
    st.sidebar.markdown("### 💰 Ví tiền của em")
    st.sidebar.subheader(f":green[{balance:,.0f} VNĐ]") # Màu xanh cho tiền của bé
    st.sidebar.info("💡 Học tập chăm chỉ và làm bài tập điểm cao để được Ba Mẹ nạp thêm tiền nhé!")
    
    st.divider()

    # 3. Lấy danh sách sản phẩm thực tế từ cơ sở dữ liệu
    products = get_store_products()
    
    if not products:
        st.info("Hiện chưa có sản phẩm nào trong cửa hàng. Quay lại sau nhé!")
        return

    # 4. Hiển thị danh sách sản phẩm theo dạng lưới 2 cột
    cols = st.columns(2)
    for idx, p in enumerate(products):
        with cols[idx % 2]:
            # Thêm border và hiệu ứng cho container
            with st.container(border=True):
                # Hiển thị Icon, Tên và Giá sản phẩm
                st.markdown(f"### {p.get('icon', '📦')} {p['name']}")
                st.write(f"Giá: :orange[**{p['price']:,} VNĐ**]")
                
                # Nút thực hiện mua hàng
                if st.button(f"🛒 Mua ngay", key=f"btn_{p['id']}", use_container_width=True, type="primary"):
                    if balance >= p['price']:
                        # Hiệu ứng spinner khi gọi API
                        with st.spinner("Đang kiểm tra túi tiền của em..."):
                            success, msg = purchase_product(user_id, p['id'])
                            if success:
                                st.success(f"🎊 Chúc mừng! Em đã mua thành công {p['name']}")
                                st.balloons() # Hiệu ứng bóng bay chúc mừng 
                                st.rerun()    # Tải lại trang để cập nhật số dư mới
                            else:
                                st.error(msg)
                    else:
                        # Thông báo khi số dư không đủ
                        st.warning(f"Số dư không đủ. Em cần thêm :red[**{(p['price'] - balance):,.0f} VNĐ**] nữa!")

if __name__ == "__main__":
    show_student_store()