import streamlit as st
import os
import time
from api_clients.tv3_client import get_store_products, purchase_product, get_gamification_profile, request_purchase
from utils.role_guard import require_role
from deep_translator import GoogleTranslator

# Kiểm tra phân quyền truy cập
require_role(["student"])

# ĐÃ SỬA: Lấy BACKEND_URL chung từ session_state toàn cục
BACKEND_URL = st.session_state.get("api_url", "http://localhost:8000")

def load_css(file_name):
    current_dir = os.path.dirname(os.path.abspath(__file__))
    css_path = os.path.abspath(os.path.join(current_dir, "../../CSS/student/student_global.css"))
    if os.path.exists(css_path):
        with open(css_path, "r", encoding="utf-8") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

load_css("student_global.css")

def get_localized_value(data_field, lang="vi", default_val=""):
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
balance = profile.get('balance', 0.0) 

st.sidebar.markdown(f"### 🪙 {STUDENT_STORE_LABELS[lang]['sidebar_wallet']}")
st.sidebar.subheader(f":green[{balance:,.0f} VNĐ]") 
st.divider()

products = get_store_products()

if not products:
    st.info(STUDENT_STORE_LABELS[lang]["info_empty"])
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
                    # ĐÃ SỬA: Loại bỏ via.placeholder và fallback về ảnh an toàn
                    fallback_img = "static/anh_laptop.jpg"
                    full_img_url = f"{BACKEND_URL}/{img_path}" if img_path and img_path.startswith("static/") else (img_path if "placeholder" not in str(img_path) else fallback_img)
                    
                    st.image(full_img_url, use_container_width=True)
                    
                    product_name_display = get_localized_value(p.get('name'), lang=lang)
                    st.markdown(f"**{product_name_display}**")
                    st.markdown(f":orange[**{p.get('price', 0):,} VNĐ**]")
                    
                    if balance >= p.get('price', 0):
                        if st.button(STUDENT_STORE_LABELS[lang]["btn_buy"], key=f"buy_{p_id}", use_container_width=True, type="primary"):
                            success, msg = purchase_product(user_id, p_id)
                            if success:
                                st.success(STUDENT_STORE_LABELS[lang]["msg_success"])
                                st.balloons()
                                time.sleep(1.5)
                                st.rerun()
                            else:
                                st.error(f"❌ {STUDENT_STORE_LABELS[lang]['err_failed']} {msg}")
                    else:
                        if st.button(STUDENT_STORE_LABELS[lang]["btn_ask"], key=f"req_{p_id}", use_container_width=True):
                            raw_name_vi = get_localized_value(p.get('name'), lang="vi")
                            success, msg = request_purchase(user_id, p_id, raw_name_vi, p.get('price', 0))
                            if success:
                                st.info(STUDENT_STORE_LABELS[lang]["msg_requested"])
                            else:
                                st.error(f"❌ {msg}")