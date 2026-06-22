# frontend/home.py
import streamlit as st
import requests
import os
import time
import re
from streamlit_quill import st_quill
from deep_translator import GoogleTranslator

# Lấy API_URL linh hoạt từ biến môi trường
BACKEND_URL = os.getenv("API_URL", "http://localhost:8000")
API_URL = f"{BACKEND_URL}/api/tv3"

# ================= 1. HÀM HỖ TRỢ =================
def load_css(file_path):
    current_dir = os.path.dirname(os.path.abspath(__file__))
    absolute_path = os.path.abspath(os.path.join(current_dir, file_path))
    if os.path.exists(absolute_path):
        with open(absolute_path, "r", encoding="utf-8") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

def save_uploaded_file(uploaded_file):
    if uploaded_file is not None:
        try:
            files = {"file": (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)}
            res = requests.post(f"{API_URL}/upload_image", files=files)
            if res.status_code == 200:
                data = res.json()
                return data.get("image_url", "")
            else:
                st.error(f"Lỗi Server Backend khi nhận ảnh: {res.text}")
        except Exception as e:
            st.error(f"Lỗi kết nối mạng: {e}")
    return ""

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

def get_valid_image_url(img_path):
    path = str(img_path).strip() if img_path else ""
    if not path or "anh_laptop.jpg" in path:
        return "https://images.unsplash.com/photo-1546410531-dd4cb6ca7404?q=80&w=800&auto=format&fit=crop"
    if path.startswith("http"):
        return path
    clean_path = path[1:] if path.startswith("/") else path
    return f"{BACKEND_URL}/{clean_path}?v={int(time.time())}"

def strip_html_tags(text):
    """Hàm dọn dẹp thẻ HTML để đoạn trích dẫn tin tức lướt ngang được hiển thị sạch sẽ"""
    return re.sub(r'<[^>]+>', '', text)

def display_about_card(title, content, img_obj_or_url, layout, img_width):
    with st.container(border=True):
        if layout == "left":
            c1, c2 = st.columns([1, 2.5]) 
            with c1: st.image(img_obj_or_url, use_container_width=True)
            with c2:
                st.markdown(f"<h3 style='margin-top:0;'>{title}</h3>", unsafe_allow_html=True)
                st.markdown(content, unsafe_allow_html=True)
        elif layout == "right":
            c1, c2 = st.columns([2.5, 1])
            with c1:
                st.markdown(f"<h3 style='margin-top:0;'>{title}</h3>", unsafe_allow_html=True)
                st.markdown(content, unsafe_allow_html=True)
            with c2: st.image(img_obj_or_url, use_container_width=True)
        else:
            st.image(img_obj_or_url, width=img_width if img_width else None, use_container_width=(not img_width))
            st.markdown(f"<h3 style='margin-top:15px;'>{title}</h3>", unsafe_allow_html=True)
            st.markdown(content, unsafe_allow_html=True)

# TẠO BĂNG CHUYỀN LƯỚT NGANG CHO TIN TỨC TRÊN WEB
def render_horizontal_news_carousel(posts, lang, labels):
    if not posts:
        st.info(labels["msg_empty_news"])
        return

    # Khởi tạo khung bọc HTML (CSS đã được đưa sang file home_style.css)
    carousel_html = '<div class="news-carousel-wrapper">'

    for p in posts:
        img_url = get_valid_image_url(p.get('image_url'))
        title = get_localized_value(p.get('title'), lang=lang, default_val="No Title")
        raw_content = get_localized_value(p.get('content'), lang=lang, default_val="")
        clean_content = strip_html_tags(raw_content) # Xóa thẻ HTML để không vỡ layout
        date = p.get('date', '')

        # Tạo từng thẻ HTML
        card_html = f"""
        <div class="news-card-hz">
            <img class="news-img-hz" src="{img_url}" onerror="this.src='https://images.unsplash.com/photo-1546410531-dd4cb6ca7404?q=80&w=800&auto=format&fit=crop'">
            <div class="news-body-hz">
                <h4 class="news-title-hz">{title}</h4>
                <div class="news-date-hz">🕒 {date}</div>
                <p class="news-excerpt-hz">{clean_content}</p>
            </div>
        </div>
        """
        carousel_html += card_html

    carousel_html += "</div>"
    st.markdown(carousel_html, unsafe_allow_html=True)


load_css("CSS/home_style.css")

# ================= 2. QUẢN LÝ NGÔN NGỮ & CACHE =================
current_lang = st.session_state.get("lang", "vi")
role = st.session_state.get("role", "guest").lower()
is_operator = role in ["operator", "admin"]

UI_LABELS = {
    "vi": {
        "about_header": "🏢 Giới thiệu trung tâm",
        "news_header": "📰 Tin tức & Sự kiện",
        "contact_header": "📞 Thông tin liên hệ",
        "btn_add": "➕ Đăng bài mới",
        "btn_save": "💾 Lưu thay đổi",
        "btn_submit_news": "🚀 Xác nhận Đăng bài",
        "btn_edit_contact": "✏️ Sửa thông tin Liên hệ",
        "btn_save_all_about": "💾 CẬP NHẬT GIỚI THIỆU",
        "input_title": "Tiêu đề bài viết",
        "input_layout": "Bố cục hiển thị:",
        "input_width": "Độ rộng ảnh (px):",
        "input_content": "Nội dung bài viết:",
        "preview_title": "👀 XEM TRƯỚC GIAO DIỆN:"
    },
    "en": {
        "about_header": "🏢 About iKids Edu",
        "news_header": "📰 News & Events",
        "contact_header": "📞 Contact Info",
        "btn_add": "➕ Post New",
        "btn_save": "💾 Save Changes",
        "btn_submit_news": "🚀 Publish",
        "btn_edit_contact": "✏️ Edit Contact",
        "btn_save_all_about": "💾 UPDATE ABOUT US",
        "input_title": "Article Title",
        "input_layout": "Layout:",
        "input_width": "Image Width (px):",
        "input_content": "Article Content:",
        "preview_title": "👀 LIVE PREVIEW:"
    }
}

@st.cache_data(ttl=2)
def get_cms_data(endpoint):
    try:
        res = requests.get(f"{API_URL}/{endpoint}", timeout=5)
        if res.status_code == 200: return res.json()
    except: pass
    return None

def refresh_cms():
    get_cms_data.clear()
    time.sleep(0.5)
    st.rerun()

about_data = get_cms_data("about") or {}
contact_data = get_cms_data("contact") or {}
all_posts = get_cms_data("posts") or []
if isinstance(all_posts, dict): all_posts = []

# ================= 3. HEADER GIAO DIỆN =================
st.markdown("<div class='header-container'>", unsafe_allow_html=True)
col_logo, col_title = st.columns([1, 6])
with col_logo:
    logo_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "static/logo.png"))
    st.image(logo_path if os.path.exists(logo_path) else "https://api.dicebear.com/7.x/initials/svg?seed=iKids", width=95)
with col_title:
    st.markdown("<h1 style='margin:0;'>iKids Education</h1>", unsafe_allow_html=True)
    st.caption("Khơi nguồn sáng tạo - Vững bước tương lai 🚀" if current_lang=="vi" else "Inspiring Creativity - Building the Future 🚀")
st.markdown("</div>", unsafe_allow_html=True)
st.divider()

about_title_vi = get_localized_value(about_data.get('title'), lang="vi", default_val="Về iKids Edu")
about_content_vi = get_localized_value(about_data.get('content'), lang="vi", default_val="")
about_content_display = get_localized_value(about_data.get('content'), lang=current_lang, default_val="")

# ================= QUẢN LÝ GIAO DIỆN (ADMIN/OPERATOR) =================
if is_operator:
    tab_about, tab_news, tab_contact = st.tabs(["🏢 Giới thiệu", "📰 Tin tức & Sự kiện", "📞 Liên hệ"])
    
    # --- TAB GIỚI THIỆU ---
    with tab_about:
        new_about_title = st.text_input(UI_LABELS[current_lang]["input_title"], value=about_title_vi)
        c_lay, c_size = st.columns(2)
        about_layout = c_lay.selectbox(UI_LABELS[current_lang]["input_layout"], 
            ["Ảnh TRÁI - Chữ PHẢI", "Ảnh PHẢI - Chữ TRÁI", "Banner (Ảnh TRÊN)"],
            index=0 if about_data.get('layout') == "left" else (1 if about_data.get('layout') == "right" else 2)
        )
        about_img_width = c_size.slider(UI_LABELS[current_lang]["input_width"], 200, 1000, int(about_data.get('img_width', 500)))
        
        st.write(UI_LABELS[current_lang]["input_content"])
        new_about_content = st_quill(value=about_content_vi, html=True, key="q_about")
        
        uploaded_about_imgs = st.file_uploader("Tải ảnh mới từ máy tính:", type=["png", "jpg", "jpeg"], accept_multiple_files=True)
        keep_old = st.checkbox("Giữ lại ảnh cũ", value=True)

        # HỆ THỐNG XEM TRƯỚC GIỚI THIỆU
        st.markdown("---")
        st.markdown(f"#### {UI_LABELS[current_lang]['preview_title']}")
        preview_layout = "left" if about_layout == "Ảnh TRÁI - Chữ PHẢI" else ("right" if about_layout == "Ảnh PHẢI - Chữ TRÁI" else "full")
        preview_img = uploaded_about_imgs[0] if uploaded_about_imgs else get_valid_image_url(about_data.get('images', [''])[0] if about_data.get('images') else "")
        display_about_card(new_about_title, new_about_content, preview_img, preview_layout, about_img_width)
        st.markdown("<br>", unsafe_allow_html=True)

        if st.button(UI_LABELS[current_lang]["btn_save_all_about"], type="primary"):
            with st.spinner("Đang lưu..."):
                new_imgs = []
                if uploaded_about_imgs:
                    for f in uploaded_about_imgs:
                        path = save_uploaded_file(f)
                        if path: new_imgs.append(path)
                
                old_imgs = about_data.get('images', []) if keep_old else []
                final_imgs = new_imgs + old_imgs
                
                requests.put(f"{API_URL}/about", json={
                    "title": new_about_title, "content": new_about_content,
                    "images": final_imgs, "layout": preview_layout, "img_width": about_img_width
                })
                st.success("Đã cập nhật Giới thiệu!")
                refresh_cms()

    # --- TAB TIN TỨC ---
    with tab_news:
        if "editing_post_data" not in st.session_state:
            st.session_state.editing_post_data = None

        if st.button(UI_LABELS[current_lang]["btn_add"], type="primary"):
            st.session_state.show_add = True
            st.session_state.editing_post_data = None
        
        # FORM THÊM MỚI
        if st.session_state.get("show_add"):
            with st.container(border=True):
                st.write("#### 📝 Soạn bài mới")
                nt = st.text_input("Tiêu đề tin tức (*)", key="add_nt")
                
                # Bỏ thanh chọn Layout bên Web vì giờ giao diện lướt ngang ép buộc 1 kiểu
                st.info("💡 Lưu ý: Tin tức sẽ được hiển thị dạng thẻ Lướt Ngang (Ảnh trên, Chữ dưới) cho chuẩn mobile.")
                ns = st.slider("Kích thước ảnh:", 100, 800, 400, key="add_ns")
                nc = st_quill(placeholder="Nội dung...", html=True, key="q_add_news")
                ni = st.file_uploader("Tải ảnh đại diện", type=["png", "jpg", "jpeg"], key="add_ni")

                if st.button(UI_LABELS[current_lang]["btn_submit_news"]):
                    if nt and nc:
                        img_path = save_uploaded_file(ni) if ni else ""
                        requests.post(f"{API_URL}/posts", json={
                            "title": nt, "content": nc, "image_url": img_path, 
                            "layout": "full", "img_width": ns, "status": "published", "date": time.strftime("%d/%m/%Y")
                        })
                        st.session_state.show_add = False
                        st.success("Đăng bài thành công!")
                        refresh_cms()

        # FORM SỬA BÀI
        if st.session_state.editing_post_data:
            p_edit = st.session_state.editing_post_data
            p_edit_title_vi = get_localized_value(p_edit.get('title'), lang="vi")
            p_edit_content_vi = get_localized_value(p_edit.get('content'), lang="vi")
            
            with st.container(border=True):
                st.write(f"#### 🛠️ Sửa bài: {p_edit_title_vi}")
                et = st.text_input("Sửa tiêu đề", value=p_edit_title_vi)
                es = st.slider("Kích thước ảnh:", 100, 800, int(p_edit.get('img_width', 400)))
                ec = st_quill(value=p_edit_content_vi, html=True, key="q_edit_news")
                ei = st.file_uploader("Đổi ảnh đại diện:", type=["png", "jpg", "jpeg"])

                if st.button(UI_LABELS[current_lang]["btn_save"]):
                    final_img = p_edit.get('image_url')
                    if ei: final_img = save_uploaded_file(ei)
                    requests.put(f"{API_URL}/posts/{p_edit.get('id', p_edit.get('_id'))}", json={
                        "title": et, "content": ec, "image_url": final_img, "layout": "full", "img_width": es
                    })
                    st.session_state.editing_post_data = None
                    st.success("Lưu thành công!")
                    refresh_cms()

        st.divider()
        st.write(f"**Danh sách bài viết đã đăng ({len(all_posts)})**")
        for p in all_posts:
            p_id = p.get('id', p.get('_id'))
            with st.container(border=True):
                img_p = get_valid_image_url(p.get('image_url'))
                p_title_display = get_localized_value(p.get('title'), lang=current_lang, default_val="No Title")
                
                c1, c2, c3 = st.columns([2, 5, 2])
                c1.image(img_p, use_container_width=True)
                c2.markdown(f"**{p_title_display}**<br><small>{p.get('date', '')}</small>", unsafe_allow_html=True)
                
                with c3:
                    if st.button("✏️ Sửa", key=f"ed_{p_id}", use_container_width=True):
                        st.session_state.editing_post_data = p
                        st.rerun()
                    if st.button("🗑️ Xóa", key=f"dl_{p_id}", use_container_width=True):
                        requests.delete(f"{API_URL}/posts/{p_id}")
                        refresh_cms()

    # --- TAB LIÊN HỆ ---
    with tab_contact:
        contact_addr_vi = get_localized_value(contact_data.get('address'), lang="vi")
        with st.container(border=True):
            st.write("#### ☎️ Cập nhật thông tin liên lạc")
            new_phone = st.text_input("Hotline", value=contact_data.get('phone', ''))
            new_email = st.text_input("Email hỗ trợ", value=contact_data.get('email', ''))
            new_addr = st.text_input("Địa chỉ trụ sở (Tiếng Việt)", value=contact_addr_vi)
            
            if st.button("💾 Lưu thông tin Liên hệ", type="primary"):
                requests.put(f"{API_URL}/contact", json={"phone": new_phone, "email": new_email, "address": new_addr})
                st.success("Đã cập nhật thông tin liên hệ!")
                refresh_cms()

# ================= GIAO DIỆN KHÁCH / PHỤ HUYNH =================
else:
    # 1. Khối Giới Thiệu
    st.subheader(UI_LABELS[current_lang]["about_header"])
    layout = about_data.get('layout', 'left')
    images = about_data.get('images', [])
    img_main = get_valid_image_url(images[0] if images else "")
    i_width = int(about_data.get('img_width', 500))

    display_about_card(about_title_vi, about_content_display, img_main, layout, i_width)

    st.write("")
    st.divider()

    # 2. Khối Tin Tức (Lướt Ngang - Carousel)
    st.subheader(UI_LABELS[current_lang]["news_header"])
    display_posts = [p for p in all_posts if p.get('status') == 'published']
    
    render_horizontal_news_carousel(display_posts, current_lang, UI_LABELS[current_lang])

    # 3. Khối Liên Hệ
    contact_addr_display = get_localized_value(contact_data.get('address'), lang=current_lang, default_val="Đang cập nhật")
    st.markdown(f"""
    <div class="contact-footer">
        <h3>{UI_LABELS[current_lang]['contact_header']}</h3>
        <p>📍 <b>{"Địa chỉ" if current_lang=="vi" else "Address"}:</b> {contact_addr_display}</p>
        <p>✉️ <b>Email:</b> {contact_data.get('email', 'Đang cập nhật')}</p>
        <p>☎️ <b>Hotline:</b> {contact_data.get('phone', 'Đang cập nhật')}</p>
    </div>
    """, unsafe_allow_html=True)