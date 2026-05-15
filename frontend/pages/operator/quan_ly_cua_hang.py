import streamlit as st
import requests
import os
import time
from PIL import Image

API_URL = "http://localhost:8000/api/tv3"

# --- CẤU HÌNH TRANG ---
st.set_page_config(page_title="Quản lý Kho hàng iKids", layout="wide")

# --- HÀM XỬ LÝ ẢNH ---
def save_processed_image(uploaded_file, target_size=(500, 500)):
    if uploaded_file is not None:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        backend_static_dir = os.path.abspath(os.path.join(current_dir, "../../../backend/static/products"))
        
        if not os.path.exists(backend_static_dir): 
            os.makedirs(backend_static_dir)
            
        file_path = os.path.join(backend_static_dir, uploaded_file.name)
        img = Image.open(uploaded_file)
        
        # Center Crop to Square
        width, height = img.size
        min_dim = min(width, height)
        left = (width - min_dim) / 2
        top = (height - min_dim) / 2
        right = (width + min_dim) / 2
        bottom = (height + min_dim) / 2
        img = img.crop((left, top, right, bottom))
        
        # Resize
        img = img.resize(target_size, Image.Resampling.LANCZOS)
        img.save(file_path)
        return f"static/products/{uploaded_file.name}"
    return None

# --- KIỂM TRA QUYỀN ---
if st.session_state.get("role") not in ["admin", "operator"]:
    st.error("🚫 Bạn không có quyền truy cập vùng này.")
    st.stop()

# --- HEADER ---
st.title("📦 Quản lý Kho hàng iKids")
st.caption("Thêm mới, chỉnh sửa hoặc gỡ bỏ sản phẩm khỏi hệ thống cửa hàng.")

# --- STATE ---
if "editing_product" not in st.session_state:
    st.session_state.editing_product = None

# --- LẤY DỮ LIỆU SẢN PHẨM ---
@st.cache_data(ttl=5)
def fetch_products():
    try:
        res = requests.get(f"{API_URL}/products", timeout=5)
        return res.json() if res.status_code == 200 else []
    except:
        return []

products = fetch_products()

# --- THỐNG KÊ NHANH ---
c1, c2, c3, c4 = st.columns(4)
c1.metric("Tổng sản phẩm", len(products))
if products:
    max_p = max([p['price'] for p in products])
    c2.metric("Giá cao nhất", f"{max_p:,}đ")
st.divider()

# --- FORM ĐĂNG / SỬA (Sử dụng Layout 2 cột bên trong) ---
is_editing = st.session_state.editing_product is not None
form_title = "🛠️ ĐANG CHỈNH SỬA SẢN PHẨM" if is_editing else "➕ THÊM SẢN PHẨM MỚI"

with st.container(border=True):
    st.subheader(form_title)
    if is_editing:
        st.info(f"Bạn đang sửa: **{st.session_state.editing_product['name']}**")
    
    with st.form("product_form", clear_on_submit=not is_editing):
        default_p = st.session_state.editing_product or {}
        
        col_f1, col_f2 = st.columns([2, 1])
        with col_f1:
            p_name = st.text_input("Tên sản phẩm (*)", value=default_p.get("name", ""))
            p_desc = st.text_area("Mô tả chi tiết", value=default_p.get("description", ""), height=100)
        
        with col_f2:
            p_price = st.number_input("Giá bán (VNĐ)", min_value=0, step=1000, value=int(default_p.get("price", 0)))
            p_img = st.file_uploader("Hình ảnh", type=["jpg", "png", "jpeg"])
            if is_editing and not p_img:
                st.caption("Để trống nếu giữ nguyên ảnh cũ")

        col_btn1, col_btn2, _ = st.columns([1, 1, 2])
        with col_btn1:
            btn_label = "Lưu cập nhật" if is_editing else "Đăng sản phẩm"
            submitted = st.form_submit_button(btn_label, use_container_width=True, type="primary")
        with col_btn2:
            if st.form_submit_button("Hủy bỏ", use_container_width=True):
                st.session_state.editing_product = None
                st.rerun()

        if submitted:
            if p_name and p_price > 0:
                img_path = save_processed_image(p_img) if p_img else default_p.get("image_url")
                payload = {
                    "name": p_name,
                    "price": p_price,
                    "description": p_desc,
                    "image_url": img_path,
                    "updated_at": time.strftime("%d/%m/%Y")
                }
                
                if is_editing:
                    res = requests.put(f"{API_URL}/products/{default_p['id']}", json=payload)
                    msg = "Cập nhật thành công!"
                else:
                    payload["created_at"] = time.strftime("%d/%m/%Y")
                    res = requests.post(f"{API_URL}/products", json=payload)
                    msg = "Đã thêm sản phẩm mới!"

                if res.status_code == 200:
                    st.success(msg)
                    st.session_state.editing_product = None
                    st.cache_data.clear()
                    time.sleep(1)
                    st.rerun()
            else:
                st.error("Thiếu thông tin bắt buộc!")

st.write("##")

# --- DANH SÁCH SẢN PHẨM HIỆN CÓ ---
col_head1, col_head2 = st.columns([2, 1])
with col_head1:
    st.subheader("🛒 Danh mục hàng hóa")
with col_head2:
    search_query = st.text_input("🔍 Tìm kiếm sản phẩm...", placeholder="Nhập tên sản phẩm...")

if not products:
    st.info("Chưa có sản essence phẩm nào trong kho.")
else:
    # Lọc sản phẩm theo tìm kiếm
    filtered_prods = [p for p in products if search_query.lower() in p['name'].lower()]
    
    # Hiển thị tiêu đề cột
    t_col1, t_col2, t_col3, t_col4, t_col5 = st.columns([1, 2, 1, 1, 1])
    t_col1.write("**Ảnh**")
    t_col2.write("**Thông tin**")
    t_col3.write("**Giá**")
    t_col4.write("**Hành động**")
    
    st.divider()

    for p in filtered_prods:
        with st.container():
            c1, c2, c3, c4, c5 = st.columns([1, 2, 1, 1, 1])
            
            with c1:
                img = p.get('image_url')
                full_img_url = f"http://localhost:8000/{img}" if img and img.startswith("static") else (img or "https://via.placeholder.com/150")
                st.image(full_img_url, use_container_width=True)
            
            with c2:
                st.markdown(f"**{p['name']}**")
                st.caption(p.get('description', 'Không có mô tả.'))
                st.caption(f"📅 Cập nhật: {p.get('updated_at', '---')}")
            
            with c3:
                st.markdown(f"#### {p['price']:,}đ")
            
            with c4:
                if st.button("✏️ Sửa", key=f"edit_{p['id']}", use_container_width=True):
                    st.session_state.editing_product = p
                    st.rerun()
            
            with c5:
                if st.button("🗑️ Xóa", key=f"del_{p['id']}", use_container_width=True):
                    if requests.delete(f"{API_URL}/products/{p['id']}").status_code == 200:
                        st.toast(f"Đã xóa {p['name']}!")
                        st.cache_data.clear()
                        time.sleep(0.5)
                        st.rerun()
            
            st.write("---")