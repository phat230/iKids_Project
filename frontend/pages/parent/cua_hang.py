import streamlit as st
import requests
import time
import os
import html

from api_clients.tv3_client import (
    get_store_products,
    purchase_product,
    get_gamification_profile,
)

from utils.role_guard import require_role
from deep_translator import GoogleTranslator

require_role(["parent", "admin"])

# ================= CẤU HÌNH BACKEND =================
BACKEND_URL = st.session_state.get("api_url", "http://localhost:8000")
API_TV3 = f"{BACKEND_URL}/api/tv3"


# ================= LOAD CSS GLOBAL =================
def load_css(file_name):
    current_dir = os.path.dirname(os.path.abspath(__file__))
    css_root = os.path.abspath(os.path.join(current_dir, "../../CSS"))
    full_path = os.path.join(css_root, file_name)

    if os.path.exists(full_path):
        with open(full_path, "r", encoding="utf-8") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)


load_css("parent/parent_global.css")


# ================= CSS RIÊNG CHO TRANG CỬA HÀNG =================
st.markdown(
    """
    <style>
    .parent-store-title {
        display: flex;
        align-items: center;
        gap: 12px;
        margin-bottom: 18px;
    }

    .parent-store-title h1 {
        margin: 0;
        color: #0284c7 !important;
        font-size: 2.45rem;
        line-height: 1.2;
        font-weight: 800;
    }

    .store-card-top {
        width: 100%;
    }

    .store-img-wrap {
        width: 100%;
        height: 215px;
        overflow: hidden;
        border-radius: 14px;
        background: #f1f5f9;
        border: 1px solid #e5e7eb;
        box-shadow: 0 5px 14px rgba(15, 23, 42, 0.08);
        display: flex;
        align-items: center;
        justify-content: center;
    }

    .store-img-wrap img {
        width: 100%;
        height: 100%;
        object-fit: cover;
        border-radius: 14px !important;
        box-shadow: none !important;
        display: block;
    }

    .store-product-title {
        min-height: 44px;
        margin-top: 14px;
        margin-bottom: 8px;
        font-size: 1rem;
        font-weight: 800;
        line-height: 1.35;
        color: #0f172a;
    }

    .store-price {
        margin-bottom: 14px;
        font-size: 0.98rem;
        color: #0f172a;
    }

    .store-price strong {
        color: #0369a1;
        font-weight: 800;
    }

    .store-balance-box {
        background: #ecfdf5;
        border: 1px solid #34d399;
        color: #047857;
        padding: 14px;
        border-radius: 14px;
        margin-bottom: 16px;
        font-weight: 800;
        text-align: center;
    }

    div[data-testid="stVerticalBlockBorderWrapper"] {
        border-radius: 14px !important;
    }

    .stSelectbox div[data-baseweb="select"] > div {
        border-radius: 10px !important;
        background-color: #f8fafc !important;
    }

    .stButton > button {
        border-radius: 10px !important;
        min-height: 44px;
        font-weight: 800 !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# ================= HELPER =================
def to_float(value, default=0.0):
    try:
        if value is None or value == "":
            return default
        return float(value)
    except Exception:
        return default


def format_money(value):
    return f"{to_float(value):,.0f} VNĐ"


def get_localized_value(data_field, lang="vi", default_val=""):
    if not data_field:
        return default_val

    if isinstance(data_field, dict):
        return data_field.get(
            lang,
            data_field.get("vi", data_field.get("en", default_val)),
        )

    if isinstance(data_field, str):
        if lang == "vi":
            return data_field

        try:
            return GoogleTranslator(source="auto", target="en").translate(data_field)
        except Exception:
            return data_field

    return default_val


def get_product_image_url(img_path):
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

    return f"{BACKEND_URL}/{img_path}"


def get_child_id(child):
    return str(child.get("id") or child.get("_id") or "")


def get_child_name(child):
    return (
        child.get("full_name")
        or child.get("name")
        or f"{CUA_HANG_LABELS[lang]['lbl_be']} ({get_child_id(child)[-4:]})"
    )


def get_product_id(product, index=0):
    return str(product.get("id") or product.get("_id") or f"product_{index}")


# ================= NGÔN NGỮ =================
lang = st.session_state.get("lang", "vi")

CUA_HANG_LABELS = {
    "vi": {
        "title": "Cửa Hàng Quà Tặng iKids",
        "sidebar_balance": "Số dư ví",
        "wallet_box": "💳 Số dư ví phụ huynh",
        "warn_no_child": "⚠️ Chưa có hồ sơ con em. Vui lòng tạo tài khoản cho bé trước.",
        "info_updating": "ℹ️ Cửa hàng đang cập nhật sản phẩm mới.",
        "lbl_price": "Giá",
        "lbl_gift_to": "Tặng cho:",
        "lbl_be": "Bé",
        "btn_confirm": "Xác nhận tặng",
        "btn_disabled": "Ví không đủ",
        "msg_success": "Đã tặng quà thành công cho",
        "msg_err_balance": "❌ Không đủ số dư trong ví!",
        "default_product": "Sản phẩm",
    },
    "en": {
        "title": "iKids Gift & Reward Store",
        "sidebar_balance": "Wallet Balance",
        "wallet_box": "💳 Parent Wallet Balance",
        "warn_no_child": "⚠️ No student profiles found. Please register your child first.",
        "info_updating": "ℹ️ The store inventory is currently being updated.",
        "lbl_price": "Price",
        "lbl_gift_to": "Gift to:",
        "lbl_be": "Kid",
        "btn_confirm": "Confirm Gift",
        "btn_disabled": "Insufficient Wallet",
        "msg_success": "Successfully gifted reward item to",
        "msg_err_balance": "❌ Insufficient wallet balance!",
        "default_product": "Product",
    },
}

labels = CUA_HANG_LABELS.get(lang, CUA_HANG_LABELS["vi"])


# ================= HEADER =================
st.markdown(
    f"""
    <div class="parent-store-title">
        <div style="font-size:2.2rem;">🛍️</div>
        <h1>{labels["title"]}</h1>
    </div>
    """,
    unsafe_allow_html=True,
)


# ================= USER SESSION =================
user_id = st.session_state.get("user_id")
token = st.session_state.get("access_token") or st.session_state.get("token")

if not user_id or not token:
    st.warning("Vui lòng đăng nhập lại." if lang == "vi" else "Please log in again.")
    st.stop()


# ================= WALLET =================
profile = get_gamification_profile(user_id)
balance = to_float(profile.get("balance", 0.0))

st.sidebar.markdown(
    f"""
    <div class="store-balance-box">
        {labels["wallet_box"]}<br>
        <span style="font-size:1.35rem;">{format_money(balance)}</span>
    </div>
    """,
    unsafe_allow_html=True,
)


# ================= LẤY DANH SÁCH CON =================
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
        get_child_id(c): get_child_name(c)
        for c in children
        if get_child_id(c)
    }

except Exception:
    child_options = {}

if not child_options:
    st.warning(labels["warn_no_child"])
    st.stop()


# ================= LẤY SẢN PHẨM =================
products = get_store_products()

if not products:
    st.info(labels["info_updating"])
    st.stop()


# ================= RENDER PRODUCT GRID =================
# 3 cột sẽ đẹp hơn cho phụ huynh, tránh card quá nhỏ hoặc ảnh bị ép.
num_cols = 3

for row_start in range(0, len(products), num_cols):
    row_products = products[row_start:row_start + num_cols]
    cols = st.columns(num_cols)

    for idx, product in enumerate(row_products):
        product_id = get_product_id(product, row_start + idx)
        price = to_float(product.get("price", 0))
        image_url = get_product_image_url(product.get("image_url", ""))

        product_name = get_localized_value(
            product.get("name"),
            lang=lang,
            default_val=labels["default_product"],
        )

        safe_name = html.escape(product_name)
        safe_image_url = html.escape(image_url)

        with cols[idx]:
            with st.container(border=True):
                st.markdown(
                    f"""
                    <div class="store-card-top">
                        <div class="store-img-wrap">
                            <img src="{safe_image_url}" alt="{safe_name}">
                        </div>
                        <div class="store-product-title">{safe_name}</div>
                        <div class="store-price">
                            {labels["lbl_price"]}: <strong>{format_money(price)}</strong>
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

                selected_child_id = st.selectbox(
                    labels["lbl_gift_to"],
                    options=list(child_options.keys()),
                    format_func=lambda x: child_options.get(x, x),
                    key=f"parent_store_select_{product_id}_{row_start}_{idx}",
                )

                can_buy = balance >= price

                if not can_buy:
                    st.caption(labels["msg_err_balance"])

                if st.button(
                    labels["btn_confirm"] if can_buy else labels["btn_disabled"],
                    key=f"parent_store_buy_{product_id}_{row_start}_{idx}",
                    use_container_width=True,
                    type="primary",
                    disabled=not can_buy,
                ):
                    success, msg = purchase_product(
                        user_id,
                        product_id,
                        target_student_id=selected_child_id,
                    )

                    if success:
                        st.success(
                            f"{labels['msg_success']} "
                            f"**{child_options[selected_child_id]}**!"
                        )
                        st.balloons()
                        time.sleep(1)
                        st.cache_data.clear()
                        st.rerun()
                    else:
                        if lang == "en" and "Ví của bé không đủ" in str(msg):
                            st.error("❌ The child's wallet balance is insufficient.")
                        else:
                            st.error(msg)