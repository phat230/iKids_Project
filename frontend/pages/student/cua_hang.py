import streamlit as st
import os
import time
from api_clients.tv3_client import get_store_products, get_gamification_profile, purchase_product, request_purchase
from utils.role_guard import require_role
from deep_translator import GoogleTranslator  # Thêm bộ dịch dự phòng trực tiếp tại chỗ

require_role(["student"])
BACKEND_URL = "http://localhost:8000"

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

def show_student_store():
    # Lấy mã ngôn ngữ hiện hành từ session_state toàn cục (Mặc định là "vi")
    lang = st.session_state.get("lang", "vi")

    # --- BỘ TỪ ĐIỂN SONG NGỮ CHI TIẾT CHO CỬA HÀNG HỌC SINH ---
    STUDENT_STORE_LABELS = {
        "vi": {
            "title": "🛍️ Cửa Hàng iKids",
            "subtitle": "Em có thể dùng tiền tích lũy để đổi quà nhé! 🎈",
            "sidebar_wallet": "Ví Tiền Của Em 💰",
            "info_empty": "Hiện chưa có sản phẩm nào trong kho quà thưởng.",
            "btn_buy": "🛒 Mua Ngay",
            "btn_ask": "🙏 Xin Ba Mẹ",
            "msg_success": "🎉 Đổi quà thành công! Hãy gặp thầy cô để nhận quà nhé.",
            "msg_requested": "📩 Đã gửi yêu cầu mua quà tới Ba Mẹ thành công!",
            "err_failed": "Giao dịch thất bại:"
        },
        "en": {
            "title": "🛍️ iKids Rewards Store",
            "subtitle": "You can use your accumulated pocket money to redeem gifts! 🎈",
            "sidebar_wallet": "My Pocket Money 💰",
            "info_empty": "There are currently no reward items available in the store.",
            "btn_buy": "🛒 Redeem Now",
            "btn_ask": "🙏 Ask Parent",
            "msg_success": "🎉 Successfully redeemed! Please meet your teacher to receive your gift.",
            "msg_requested": "📩 Successfully sent the purchase request to your Parents!",
            "err_failed": "Transaction failed:"
        }
    }

    st.title(STUDENT_STORE_LABELS[lang]["title"])
    st.write(STUDENT_STORE_LABELS[lang]["subtitle"])
    
    user_id = st.session_state.get("user_id")
    profile = get_gamification_profile(user_id)
    balance = profile.get('balance', 0)
    
    st.sidebar.markdown(f"### 🪙 {STUDENT_STORE_LABELS[lang]['sidebar_wallet']}")
    st.sidebar.subheader(f":green[{balance:,.0f} VNĐ]") 
    st.divider()

    products = get_store_products()
    
    if not products:
        st.info(STUDENT_STORE_LABELS[lang]["info_empty"])
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
                    
                    # Trích xuất tên sản phẩm thông minh dựa trên dữ liệu chuẩn hoặc dịch bù chuỗi thô tiếng Việt
                    product_name_display = get_localized_value(p.get('name'), lang=lang)
                    st.markdown(f"**{product_name_display}**")
                    st.write(f":orange[**{p.get('price', 0):,} VNĐ**]")
                    
                    # Kiểm tra số dư ví của bé
                    if balance >= p.get('price', 0):
                        if st.button(STUDENT_STORE_LABELS[lang]["btn_buy"], key=f"buy_{p_id}", use_container_width=True, type="primary"):
                            success, msg = purchase_product(user_id, p_id)
                            if success:
                                st.success(STUDENT_STORE_LABELS[lang]["msg_success"])
                                st.balloons()
                                time.sleep(1.5)
                                st.rerun()
                            else:
                                # Bản dịch thông báo lỗi nếu số dư phụ huynh duyệt bị nghẽn
                                if lang == "en" and "không đủ số dư" in str(msg):
                                    st.error("❌ Insufficient balance for this transaction.")
                                else:
                                    st.error(f"❌ {STUDENT_STORE_LABELS[lang]['err_failed']} {msg}")
                    else:
                        # Nếu bé không đủ tiền, cung cấp tính năng gửi yêu cầu duyệt mua tới máy Phụ huynh
                        if st.button(STUDENT_STORE_LABELS[lang]["btn_ask"], key=f"req_{p_id}", use_container_width=True):
                            # Gửi tên sản phẩm gốc Tiếng Việt lên Backend để lưu Log chính xác cho phụ huynh dễ xem
                            raw_name_vi = get_localized_value(p.get('name'), lang="vi")
                            success, msg = request_purchase(user_id, p_id, raw_name_vi, p.get('price', 0))
                            if success:
                                st.info(STUDENT_STORE_LABELS[lang]["msg_requested"])
                            else:
                                st.error(f"❌ {msg}")

if __name__ == "__main__":
    show_student_store()