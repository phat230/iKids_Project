import streamlit as st
import os
# Import cả 2 hàm: purchase_product (mua thẳng) và request_purchase (xin phép)
from api_clients.tv3_client import get_store_products, get_gamification_profile, purchase_product, request_purchase
from utils.role_guard import require_role

# Bảo mật - Chỉ cho phép Học sinh truy cập
require_role(["student"])

# ================= HÀM ĐỌC FILE CSS (SỬA LỖI ĐƯỜNG DẪN TUYỆT ĐỐI) =================
def load_css(file_name):
    """
    Tự động tìm file CSS trong thư mục frontend/CSS/
    file_name: tên file kèm thư mục con, ví dụ 'student/cua_hang.css'
    """
    # Lấy đường dẫn tuyệt đối đến thư mục chứa file cua_hang.py hiện tại
    current_dir = os.path.dirname(os.path.abspath(__file__)) # frontend/pages/student
    
    # Tìm đường dẫn đến thư mục CSS (lùi 2 cấp từ pages/student/ rồi vào CSS/)
    css_root = os.path.abspath(os.path.join(current_dir, "../../CSS"))
    full_path = os.path.join(css_root, file_name)

    if os.path.exists(full_path):
        with open(full_path, "r", encoding="utf-8") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    else:
        st.warning(f"⚠️ Không tìm thấy file CSS tại: {full_path}")

def show_student_store():
    # Tải CSS làm đẹp cho cửa hàng (Chỉ truyền phần sau thư mục CSS/)
    load_css("student/cua_hang.css")

    # 1. Cấu hình tiêu đề trang
    st.title("🛍️ Cửa Hàng iKids")
    st.write("Em có thể dùng tiền tự tích lũy để mua đồ hoặc xin phép Ba Mẹ mua tặng nhé!")
    
    user_id = st.session_state.get("user_id")
    
    if not user_id:
        st.error("Vui lòng đăng nhập để tiếp tục.")
        st.stop()
    
    # 2. Lấy số dư thực tế từ ví của bé
    profile = get_gamification_profile(user_id)
    balance = profile.get('balance', 0)
    
    # Hiển thị số dư hiện có ở Sidebar
    st.sidebar.markdown("### 👛 Ví tiền của em")
    st.sidebar.subheader(f":green[{balance:,.0f} VNĐ]") 
    st.sidebar.info("💡 Nếu ví có đủ tiền, em có thể tự mua ngay mà không cần chờ Ba Mẹ duyệt!")
    
    st.divider()

    # 3. Lấy danh sách sản phẩm
    products = get_store_products()
    
    if not products:
        st.info("Hiện chưa có sản phẩm nào trong cửa hàng. Quay lại sau nhé!")
        return

    # 4. Hiển thị danh sách sản phẩm theo dạng lưới 2 cột
    cols = st.columns(2)
    for idx, p in enumerate(products):
        with cols[idx % 2]:
            with st.container(border=True):
                # Hiển thị thông tin sản phẩm
                st.markdown(f"### {p.get('icon', '🎁')} {p['name']}")
                st.write(f"Giá: :orange[**{p['price']:,} VNĐ**]")
                
                # --- LOGIC XỬ LÝ NÚT BẤM DỰA TRÊN SỐ DƯ ---
                if balance >= p['price']:
                    # TRƯỜNG HỢP 1: ĐỦ TIỀN -> TỰ MUA LUÔN
                    if st.button(f"🛒 Mua ngay bằng ví", key=f"buy_{p['id']}", use_container_width=True, type="primary"):
                        with st.spinner("Đang thực hiện thanh toán..."):
                            success, msg = purchase_product(user_id, p['id'])
                            if success:
                                st.success(f"🎉 Tuyệt vời! Em đã tự mua thành công {p['name']}.")
                                st.balloons()
                                st.rerun() # Reload để cập nhật lại số dư ví mới
                            else:
                                st.error(msg)
                else:
                    # TRƯỜNG HỢP 2: KHÔNG ĐỦ TIỀN -> HIỆN NÚT XIN PHÉP
                    st.caption(f"⚠️ Thiếu {(p['price'] - balance):,.0f} VNĐ để tự mua.")
                    if st.button(f"🙏 Xin Ba Mẹ mua giúp", key=f"req_{p['id']}", use_container_width=True):
                        with st.spinner("Đang gửi tin nhắn cho Ba Mẹ..."):
                            # Gửi yêu cầu chờ duyệt (status pending)
                            success, msg = request_purchase(user_id, p['id'], p['name'], p['price'])
                            if success:
                                st.info(f"✅ Đã gửi yêu cầu mua {p['name']}. Em hãy đợi Ba Mẹ đồng ý nhé!")
                            else:
                                st.error(msg)

if __name__ == "__main__":
    show_student_store()