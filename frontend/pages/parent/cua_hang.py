import streamlit as st
import requests
import time
from api_clients.tv3_client import get_store_products, purchase_product, get_gamification_profile
from utils.role_guard import require_role
from deep_translator import GoogleTranslator  # Thêm bộ dịch dự phòng trực tiếp tại chỗ

require_role(["parent", "admin"])
BACKEND_URL = "http://localhost:8000"
API_TV3 = "http://localhost:8000/api/tv3"

def get_localized_value(data_field, lang="vi", default_val=""):
    """
    Hàm bóc tách dữ liệu nâng cao cho sản phẩm:
    - Nếu dữ liệu dạng dict đa ngôn ngữ: Lấy đúng ngôn ngữ được chọn.
    - Nếu dữ liệu dạng chuỗi thô (nhập phẳng): Tự động dịch bù sang Tiếng Anh tại chỗ.
    """
    if not data_field:
        return default_val
    if isinstance(data_field, dict):
        return data_field.get(lang, data_field.get("vi", default_val))
    if isinstance(data_field, str):
        if lang == "vi":
            return data_field
        else:
            try:
                return GoogleTranslator(source='auto', target='en').translate(data_field)
            except Exception:
                return data_field
    return default_val

def render_store():
    # Lấy mã ngôn ngữ hiện hành từ session_state toàn cục (Mặc định là "vi")
    lang = st.session_state.get("lang", "vi")

    # --- BỘ TỪ ĐIỂN SONG NGỮ CHI TIẾT CHO TRANG CỬA HÀNG PHỤ HUYNH ---
    CUA_HANG_LABELS = {
        "vi": {
            "title": "🛍️ Cửa Hàng Quà Tặng iKids",
            "sidebar_balance": "Số dư ví",
            "warn_no_child": "⚠️ Chưa có hồ sơ con em. Vui lòng tạo tài khoản cho bé trước.",
            "info_updating": "ℹ️ Cửa hàng đang cập nhật sản phẩm mới.",
            "lbl_price": "Giá",
            "lbl_gift_to": "Tặng cho:",
            "lbl_be": "Bé",
            "btn_confirm": "Xác nhận tặng",
            "msg_success": "Đã tặng quà thành công cho",
            "msg_err_balance": "❌ Không đủ số dư trong ví!"
        },
        "en": {
            "title": "🛍️ iKids Gift & Reward Store",
            "sidebar_balance": "Wallet Balance",
            "warn_no_child": "⚠️ No student profiles found. Please register your child first.",
            "info_updating": "ℹ️ The store inventory is currently being updated.",
            "lbl_price": "Price",
            "lbl_gift_to": "Gift to:",
            "lbl_be": "Kid",
            "btn_confirm": "Confirm Gift",
            "msg_success": "Successfully gifted reward item to",
            "msg_err_balance": "❌ Insufficient wallet balance!"
        }
    }

    st.title(CUA_HANG_LABELS[lang]["title"])
    
    user_id = st.session_state.get("user_id")
    token = st.session_state.get("access_token") or st.session_state.get("token")
    
    profile = get_gamification_profile(user_id)
    balance = profile.get('balance', 0.0) 
    st.sidebar.markdown(f"### 💳 {CUA_HANG_LABELS[lang]['sidebar_balance']}: {balance:,.0f} VNĐ")
    
    # Lấy danh sách con
    headers = {"Authorization": f"Bearer {token}", "parent-id": str(user_id)}
    try:
        res = requests.get(f"{API_TV3}/parent/my-children", headers=headers)
        children = res.json() if res.status_code == 200 else []
        
        # Thử lấy full_name, nếu không có thì lấy name, cuối cùng là dùng 4 số cuối ID để phân biệt
        child_options = {
            c["id"]: (c.get("full_name") or c.get("name") or f"{CUA_HANG_LABELS[lang]['lbl_be']} ({str(c['id'])[-4:]})") 
            for c in children
        }
    except Exception: 
        child_options = {}

    if not child_options:
        st.warning(CUA_HANG_LABELS[lang]["warn_no_child"])
        st.stop()

    products = get_store_products()
    if not products:
        st.info(CUA_HANG_LABELS[lang]["info_updating"])
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
                        
                        # Trích xuất tên sản phẩm thông minh dựa trên dict đa ngôn ngữ hoặc chuỗi phẳng
                        product_name_display = get_localized_value(p.get('name'), lang=lang)
                        st.markdown(f"**{product_name_display}**")
                        st.markdown(f"{CUA_HANG_LABELS[lang]['lbl_price']}: :blue[{p.get('price', 0):,} VNĐ]")
                        
                        selected_child_id = st.selectbox(
                            CUA_HANG_LABELS[lang]["lbl_gift_to"], 
                            options=list(child_options.keys()), 
                            format_func=lambda x: child_options[x], 
                            key=f"sel_{p_id}"
                        )
                        
                        if st.button(CUA_HANG_LABELS[lang]["btn_confirm"], key=f"pbuy_{p_id}", use_container_width=True, type="primary"):
                            if balance >= p.get('price', 0):
                                # Truyền thêm target_student_id để backend biết tặng cho ai
                                success, msg = purchase_product(user_id, p_id, target_student_id=selected_child_id) 
                                if success:
                                    st.success(f"{CUA_HANG_LABELS[lang]['msg_success']} **{child_options[selected_child_id]}**!")
                                    st.balloons()
                                    time.sleep(1)
                                    st.cache_data.clear()
                                    st.rerun()
                                else: 
                                    # Chuyển ngữ lỗi nếu backend bắn về chuỗi tiếng Việt thô khi xem ở chế độ Eng
                                    if lang == "en" and "Ví của bé không đủ" in msg:
                                        st.error("❌ The child's wallet balance is insufficient.")
                                    else:
                                        st.error(msg)
                            else: 
                                st.error(CUA_HANG_LABELS[lang]["msg_err_balance"])

if __name__ == "__main__":
    render_store()