import streamlit as st
import requests
import time
import os
from api_clients.tv3_client import (
    get_store_products,
    purchase_product,
    get_gamification_profile,
)
from utils.role_guard import require_role
from deep_translator import GoogleTranslator

require_role(["parent", "admin"])

# Lấy BACKEND_URL chung từ session_state
BACKEND_URL = st.session_state.get("api_url", "http://localhost:8000")
API_TV3 = f"{BACKEND_URL}/api/tv3"


def load_css(file_name):
    current_dir = os.path.dirname(os.path.abspath(__file__))
    css_root = os.path.abspath(os.path.join(current_dir, "../../CSS"))
    full_path = os.path.join(css_root, file_name)

    if os.path.exists(full_path):
        with open(full_path, "r", encoding="utf-8") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)


load_css("parent/parent_global.css")


def to_float(value, default=0.0):
    try:
        if value is None:
            return default
        return float(value)
    except Exception:
        return default


def get_localized_value(data_field, lang="vi", default_val=""):
    if not data_field:
        return default_val

    if isinstance(data_field, dict):
        return data_field.get(lang, data_field.get("vi", data_field.get("en", default_val)))

    if isinstance(data_field, str):
        if lang == "vi":
            return data_field
        try:
            return GoogleTranslator(source="auto", target="en").translate(data_field)
        except Exception:
            return data_field

    return default_val


def get_product_image_url(img_path):
    """
    Chuẩn hóa ảnh sản phẩm:
    - Cloudinary / URL online: dùng trực tiếp
    - static/... cũ: ghép với BACKEND_URL
    - rỗng / placeholder / lỗi: dùng ảnh fallback an toàn
    """

    fallback_img = (
        "https://upload.wikimedia.org/wikipedia/commons/thumb/a/ac/"
        "No_image_available.svg/1024px-No_image_available.svg.png"
    )

    if not img_path:
        return fallback_img

    img_path = str(img_path).strip()

    if (
        not img_path
        or "placeholder" in img_path.lower()
        or "via.placeholder" in img_path.lower()
        or "anh_laptop.jpg" in img_path.lower()
    ):
        return fallback_img

    if img_path.startswith("http://") or img_path.startswith("https://"):
        return img_path

    if img_path.startswith("/"):
        img_path = img_path[1:]

    if img_path.startswith("static/"):
        return f"{BACKEND_URL}/{img_path}"

    return f"{BACKEND_URL}/{img_path}"


# Lấy mã ngôn ngữ hiện hành từ session_state toàn cục
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
        "msg_err_balance": "❌ Không đủ số dư trong ví!",
        "default_product": "Sản phẩm",
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
        "msg_err_balance": "❌ Insufficient wallet balance!",
        "default_product": "Product",
    },
}

st.title(CUA_HANG_LABELS[lang]["title"])

user_id = st.session_state.get("user_id")
token = st.session_state.get("access_token") or st.session_state.get("token")

profile = get_gamification_profile(user_id)
balance = to_float(profile.get("balance", 0.0))

st.sidebar.markdown(
    f"### 💳 {CUA_HANG_LABELS[lang]['sidebar_balance']}: {balance:,.0f} VNĐ"
)

# Lấy danh sách con
headers = {
    "Authorization": f"Bearer {token}",
    "parent-id": str(user_id),
}

try:
    res = requests.get(
        f"{API_TV3}/parent/my-children",
        headers=headers,
        timeout=15,
    )

    children = res.json() if res.status_code == 200 else []

    child_options = {
        c["id"]: (
            c.get("full_name")
            or c.get("name")
            or f"{CUA_HANG_LABELS[lang]['lbl_be']} ({str(c['id'])[-4:]})"
        )
        for c in children
        if c.get("id")
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
    num_cols = 4

    for i in range(0, len(products), num_cols):
        row_products = products[i:i + num_cols]
        cols = st.columns(num_cols)

        for idx, p in enumerate(row_products):
            p_id = p.get("id", p.get("_id"))
            price = to_float(p.get("price", 0))

            with cols[idx]:
                with st.container(border=True):
                    img_path = p.get("image_url", "")
                    full_img_url = get_product_image_url(img_path)

                    try:
                        st.image(full_img_url, use_container_width=True)
                    except Exception:
                        st.image(
                            "https://upload.wikimedia.org/wikipedia/commons/thumb/a/ac/"
                            "No_image_available.svg/1024px-No_image_available.svg.png",
                            use_container_width=True,
                        )

                    product_name_display = get_localized_value(
                        p.get("name"),
                        lang=lang,
                        default_val=CUA_HANG_LABELS[lang]["default_product"],
                    )

                    st.markdown(f"**{product_name_display}**")
                    st.markdown(
                        f"{CUA_HANG_LABELS[lang]['lbl_price']}: "
                        f":blue[{price:,.0f} VNĐ]"
                    )

                    selected_child_id = st.selectbox(
                        CUA_HANG_LABELS[lang]["lbl_gift_to"],
                        options=list(child_options.keys()),
                        format_func=lambda x: child_options[x],
                        key=f"sel_{p_id}",
                    )

                    if st.button(
                        CUA_HANG_LABELS[lang]["btn_confirm"],
                        key=f"pbuy_{p_id}",
                        use_container_width=True,
                        type="primary",
                    ):
                        if balance >= price:
                            success, msg = purchase_product(
                                user_id,
                                p_id,
                                target_student_id=selected_child_id,
                            )

                            if success:
                                st.success(
                                    f"{CUA_HANG_LABELS[lang]['msg_success']} "
                                    f"**{child_options[selected_child_id]}**!"
                                )
                                st.balloons()
                                time.sleep(1)
                                st.cache_data.clear()
                                st.rerun()
                            else:
                                if lang == "en" and "Ví của bé không đủ" in str(msg):
                                    st.error(
                                        "❌ The child's wallet balance is insufficient."
                                    )
                                else:
                                    st.error(msg)
                        else:
                            st.error(CUA_HANG_LABELS[lang]["msg_err_balance"])