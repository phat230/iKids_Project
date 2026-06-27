import streamlit as st
import requests
import time
from deep_translator import GoogleTranslator

# ĐÃ SỬA: Lấy BACKEND_URL chung từ session_state và cấu hình tiền tố module TV3
BACKEND_URL = st.session_state.get("api_url", "http://localhost:8000")
API_URL = f"{BACKEND_URL}/api/tv3"

# --- CẤU HÌNH TRANG ---
st.set_page_config(page_title="Quản lý Kho hàng iKids", layout="wide")


# --- HÀM UPLOAD ẢNH LÊN BACKEND/CLOUDINARY ---
def upload_image_to_backend(uploaded_file):
    """
    Upload ảnh lên backend.
    Backend sẽ đưa ảnh lên Cloudinary và trả về:
    - image_url
    - image_public_id hoặc public_id
    """

    if uploaded_file is None:
        return {
            "image_url": "",
            "image_public_id": ""
        }

    try:
        files = {
            "file": (
                uploaded_file.name,
                uploaded_file.getvalue(),
                uploaded_file.type
            )
        }

        res = requests.post(
            f"{API_URL}/upload_image",
            files=files,
            timeout=60
        )

        if res.status_code == 200:
            data = res.json()

            return {
                "image_url": data.get("image_url", ""),
                "image_public_id": data.get("image_public_id") or data.get("public_id", "")
            }

        st.error(f"Lỗi upload ảnh: {res.text}")

    except Exception as e:
        st.error(f"Lỗi kết nối khi upload ảnh: {e}")

    return {
        "image_url": "",
        "image_public_id": ""
    }


def get_product_image_url(img):
    """
    Chuẩn hóa đường dẫn ảnh sản phẩm.

    Hỗ trợ:
    - Cloudinary URL: https://res.cloudinary.com/...
    - Ảnh local cũ: static/...
    - Ảnh rỗng hoặc placeholder
    """

    fallback_img = f"{BACKEND_URL}/static/anh_laptop.jpg"

    if not img:
        return fallback_img

    img = str(img)

    if "placeholder" in img.lower():
        return fallback_img

    if img.startswith("http://") or img.startswith("https://"):
        return img

    if img.startswith("static/"):
        return f"{BACKEND_URL}/{img}"

    return img


def get_localized_value(data_field, lang="vi", default_val=""):
    """
    Hàm bóc tách dữ liệu nâng cao cho sản phẩm:
    - Nếu dữ liệu dạng dict đa ngôn ngữ: lấy đúng ngôn ngữ được chọn.
    - Nếu dữ liệu dạng chuỗi thô: tự động dịch bù sang Tiếng Anh tại chỗ.
    """

    if not data_field:
        return default_val

    if isinstance(data_field, dict):
        return data_field.get(lang, data_field.get("vi", default_val))

    if isinstance(data_field, str):
        if lang == "vi":
            return data_field
        try:
            return GoogleTranslator(source="auto", target="en").translate(data_field)
        except Exception:
            return data_field

    return default_val


# Lấy mã ngôn ngữ hiện hành từ session_state
lang = st.session_state.get("lang", "vi")


# --- BỘ TỪ ĐIỂN SONG NGỮ CHI TIẾT CHO QUAN_LY_CUA_HANG ---
STORE_LABELS = {
    "vi": {
        "access_denied": "⚠️ Bạn không có quyền truy cập vùng này.",
        "title": "🛍️ Quản lý Kho hàng iKids",
        "caption": "Thêm mới, chỉnh sửa hoặc gỡ bỏ sản phẩm khỏi hệ thống cửa hàng.",
        "stat_total": "Tổng sản phẩm",
        "stat_max_price": "Giá cao nhất",
        "form_edit_title": "📝 ĐANG CHỈNH SỬA SẢN PHẨM",
        "form_add_title": "➕ THÊM SẢN PHẨM MỚI",
        "info_editing": "Bạn đang sửa:",
        "input_name": "Tên sản phẩm (*)",
        "input_desc": "Mô tả chi tiết",
        "input_price": "Giá bán (VNĐ)",
        "input_img": "Hình ảnh sản phẩm",
        "img_keep_hint": "Để trống nếu giữ nguyên ảnh cũ",
        "btn_save": "Lưu cập nhật",
        "btn_add": "Đăng sản phẩm",
        "btn_cancel": "Hủy bỏ",
        "msg_success_put": "Cập nhật thành công!",
        "msg_success_post": "Đã thêm sản phẩm mới!",
        "msg_err_empty": "⚠️ Thiếu thông tin bắt buộc hoặc giá sản phẩm không hợp lệ!",
        "msg_upload_failed": "Upload ảnh thất bại, vui lòng thử lại.",

        "sub_catalog": "📦 Danh mục hàng hóa",
        "search_placeholder": "Tìm kiếm sản phẩm...",
        "search_label": "🔍 Tìm kiếm sản phẩm...",
        "no_products": "Chưa có sản phẩm nào trong kho.",
        "th_img": "**Ảnh**",
        "th_info": "**Thông tin sản phẩm**",
        "th_price": "**Giá đổi thưởng**",
        "th_action": "**Hành động**",
        "btn_row_edit": "Sửa",
        "btn_row_del": "Xóa",
        "toast_del": "Đã xóa"
    },
    "en": {
        "access_denied": "⚠️ Access denied. You do not have permission to view this page.",
        "title": "🛍️ iKids Inventory Management",
        "caption": "Add new rewards, modify profiles, or remove products from the store database.",
        "stat_total": "Total Products",
        "stat_max_price": "Highest Price",
        "form_edit_title": "📝 EDITING PRODUCT DATA",
        "form_add_title": "➕ ADD NEW REWARD PRODUCT",
        "info_editing": "Currently modifying:",
        "input_name": "Product Name (*)",
        "input_desc": "Detailed Description",
        "input_price": "Price (Points/VND)",
        "input_img": "Product Image Upload",
        "img_keep_hint": "Leave blank to preserve current image",
        "btn_save": "Save Changes",
        "btn_add": "Publish Product",
        "btn_cancel": "Cancel",
        "msg_success_put": "Product profile updated successfully!",
        "msg_success_post": "New product added to inventory!",
        "msg_err_empty": "⚠️ Required fields cannot be empty and price must be greater than 0!",
        "msg_upload_failed": "Image upload failed. Please try again.",

        "sub_catalog": "📦 Inventory Catalog",
        "search_placeholder": "Search rewards...",
        "search_label": "🔍 Search rewards by name...",
        "no_products": "The store database is currently empty.",
        "th_img": "**Image**",
        "th_info": "**Product Profiles**",
        "th_price": "**Point Value**",
        "th_action": "**Actions**",
        "btn_row_edit": "Edit",
        "btn_row_del": "Delete",
        "toast_del": "Successfully removed"
    }
}


# --- KIỂM TRA QUYỀN ---
if st.session_state.get("role") not in ["admin", "operator"]:
    st.error(STORE_LABELS[lang]["access_denied"])
    st.stop()


# --- HEADER ---
st.title(STORE_LABELS[lang]["title"])
st.caption(STORE_LABELS[lang]["caption"])


# --- STATE ---
if "editing_product" not in st.session_state:
    st.session_state.editing_product = None


# --- LẤY DỮ LIỆU SẢN PHẨM ---
@st.cache_data(ttl=5)
def fetch_products():
    try:
        res = requests.get(f"{API_URL}/products", timeout=10)
        return res.json() if res.status_code == 200 else []
    except Exception:
        return []


products = fetch_products()


# --- THỐNG KÊ NHANH ---
c1, c2, c3, c4 = st.columns(4)

c1.metric(STORE_LABELS[lang]["stat_total"], len(products))

if products:
    prices = [
        p.get("price", 0)
        for p in products
        if isinstance(p.get("price"), (int, float))
    ]
    max_p = max(prices) if prices else 0
    c2.metric(STORE_LABELS[lang]["stat_max_price"], f"{max_p:,.0f}đ")

st.divider()


# --- FORM ĐĂNG / SỬA SẢN PHẨM ---
is_editing = st.session_state.editing_product is not None
form_title = STORE_LABELS[lang]["form_edit_title"] if is_editing else STORE_LABELS[lang]["form_add_title"]

with st.container(border=True):
    st.subheader(form_title)

    if is_editing:
        edit_prod_name = get_localized_value(
            st.session_state.editing_product.get("name"),
            lang=lang
        )
        st.info(f"💡 {STORE_LABELS[lang]['info_editing']} **{edit_prod_name}**")

    with st.form("product_form", clear_on_submit=not is_editing):
        default_p = st.session_state.editing_product or {}

        default_name_vi = get_localized_value(default_p.get("name"), lang="vi")
        default_desc_vi = get_localized_value(default_p.get("description"), lang="vi")

        col_f1, col_f2 = st.columns([2, 1])

        with col_f1:
            p_name = st.text_input(
                STORE_LABELS[lang]["input_name"],
                value=default_name_vi
            )

            p_desc = st.text_area(
                STORE_LABELS[lang]["input_desc"],
                value=default_desc_vi,
                height=100
            )

        with col_f2:
            p_price = st.number_input(
                STORE_LABELS[lang]["input_price"],
                min_value=0,
                step=1000,
                value=int(default_p.get("price", 0))
            )

            p_img = st.file_uploader(
                STORE_LABELS[lang]["input_img"],
                type=["jpg", "jpeg", "png", "webp", "gif"]
            )

            if is_editing and not p_img:
                st.caption(STORE_LABELS[lang]["img_keep_hint"])

        col_btn1, col_btn2, _ = st.columns([1, 1, 2])

        with col_btn1:
            btn_label = STORE_LABELS[lang]["btn_save"] if is_editing else STORE_LABELS[lang]["btn_add"]
            submitted = st.form_submit_button(
                btn_label,
                use_container_width=True,
                type="primary"
            )

        with col_btn2:
            cancel_clicked = st.form_submit_button(
                STORE_LABELS[lang]["btn_cancel"],
                use_container_width=True
            )

        if cancel_clicked:
            st.session_state.editing_product = None
            st.rerun()

        if submitted:
            if p_name.strip() and p_price > 0:
                # Nếu có ảnh mới thì upload ảnh lên backend/Cloudinary
                if p_img:
                    upload_data = upload_image_to_backend(p_img)
                    img_path = upload_data["image_url"]
                    image_public_id = upload_data["image_public_id"]

                    if not img_path:
                        st.error(STORE_LABELS[lang]["msg_upload_failed"])
                        st.stop()

                # Nếu đang sửa mà không chọn ảnh mới thì giữ ảnh cũ
                else:
                    img_path = default_p.get("image_url", "")
                    image_public_id = (
                        default_p.get("image_public_id")
                        or default_p.get("public_id")
                        or ""
                    )

                payload = {
                    "name": p_name.strip(),
                    "price": p_price,
                    "description": p_desc.strip(),
                    "image_url": img_path,
                    "image_public_id": image_public_id,
                    "updated_at": time.strftime("%d/%m/%Y")
                }

                try:
                    if is_editing:
                        res = requests.put(
                            f"{API_URL}/products/{default_p['id']}",
                            json=payload,
                            timeout=30
                        )
                        msg = STORE_LABELS[lang]["msg_success_put"]
                    else:
                        payload["created_at"] = time.strftime("%d/%m/%Y")
                        res = requests.post(
                            f"{API_URL}/products",
                            json=payload,
                            timeout=30
                        )
                        msg = STORE_LABELS[lang]["msg_success_post"]

                    if res.status_code == 200:
                        st.success(msg)
                        st.session_state.editing_product = None
                        st.cache_data.clear()
                        time.sleep(1)
                        st.rerun()
                    else:
                        try:
                            st.error(res.json().get("detail", "Error occurred"))
                        except Exception:
                            st.error(res.text)

                except Exception as e:
                    st.error(f"Lỗi kết nối backend: {e}")

            else:
                st.error(STORE_LABELS[lang]["msg_err_empty"])


st.write("##")


# --- DANH SÁCH SẢN PHẨM HIỆN CÓ ---
col_head1, col_head2 = st.columns([2, 1])

with col_head1:
    st.subheader(STORE_LABELS[lang]["sub_catalog"])

with col_head2:
    search_query = st.text_input(
        STORE_LABELS[lang]["search_label"],
        placeholder=STORE_LABELS[lang]["search_placeholder"],
        label_visibility="collapsed"
    )


if not products:
    st.info(STORE_LABELS[lang]["no_products"])

else:
    filtered_prods = []

    for p in products:
        p_name_lang = get_localized_value(p.get("name"), lang=lang)

        if search_query.lower() in p_name_lang.lower():
            filtered_prods.append(p)

    t_col1, t_col2, t_col3, t_col4, t_col5 = st.columns([1, 2, 1, 1, 1])

    t_col1.write(STORE_LABELS[lang]["th_img"])
    t_col2.write(STORE_LABELS[lang]["th_info"])
    t_col3.write(STORE_LABELS[lang]["th_price"])
    t_col4.write(STORE_LABELS[lang]["th_action"])

    st.divider()

    for p in filtered_prods:
        display_name = get_localized_value(
            p.get("name"),
            lang=lang
        )

        display_desc = get_localized_value(
            p.get("description"),
            lang=lang,
            default_val="No description provided." if lang == "en" else "Không có mô tả."
        )

        product_id = p.get("id") or p.get("_id")

        with st.container():
            c1, c2, c3, c4, c5 = st.columns([1, 2, 1, 1, 1])

            with c1:
                img = p.get("image_url", "")
                full_img_url = get_product_image_url(img)

                try:
                    st.image(full_img_url, use_container_width=True)
                except Exception:
                    st.image(
                        f"{BACKEND_URL}/static/anh_laptop.jpg",
                        use_container_width=True
                    )

            with c2:
                st.markdown(f"**{display_name}**")
                st.caption(display_desc)
                st.caption(
                    f"📅 {'Cập nhật' if lang == 'vi' else 'Updated'}: {p.get('updated_at', '---')}"
                )

            with c3:
                try:
                    price = float(p.get("price", 0))
                except Exception:
                    price = 0

                st.markdown(f"#### {price:,.0f}đ")

            with c4:
                if st.button(
                    STORE_LABELS[lang]["btn_row_edit"],
                    key=f"edit_{product_id}",
                    use_container_width=True
                ):
                    st.session_state.editing_product = p
                    st.rerun()

            with c5:
                if st.button(
                    STORE_LABELS[lang]["btn_row_del"],
                    key=f"del_{product_id}",
                    use_container_width=True
                ):
                    try:
                        res = requests.delete(
                            f"{API_URL}/products/{product_id}",
                            timeout=30
                        )

                        if res.status_code == 200:
                            st.toast(
                                f"✅ {STORE_LABELS[lang]['toast_del']} {display_name}!"
                            )
                            st.cache_data.clear()
                            time.sleep(0.5)
                            st.rerun()
                        else:
                            try:
                                st.error(res.json().get("detail", "Xóa thất bại"))
                            except Exception:
                                st.error(res.text)

                    except Exception as e:
                        st.error(f"Lỗi kết nối backend: {e}")

            st.write("---")