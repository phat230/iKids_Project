# frontend/home.py
import streamlit as st
import requests
import os
import time
from streamlit_quill import st_quill
from deep_translator import GoogleTranslator

# FIX 1: Lấy API_URL linh hoạt từ biến môi trường
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
        current_dir = os.path.dirname(os.path.abspath(__file__))
        save_dir = os.path.abspath(os.path.join(current_dir, "static/uploads"))
        if not os.path.exists(save_dir):
            os.makedirs(save_dir)
        file_path = os.path.join(save_dir, uploaded_file.name)
        with open(file_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        return f"static/uploads/{uploaded_file.name}"
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

# Tải CSS làm đẹp toàn cục cho Trang chủ
load_css("CSS/home_style.css")

# ================= 2. QUẢN LÝ NGÔN NGỮ & PHÂN QUYỀN =================
current_lang = st.session_state.get("lang", "vi")
role = st.session_state.get("role", "guest").lower()
is_operator = role in ["operator", "admin"]

UI_LABELS = {
    "vi": {
        "about_header": "🏢 Giới thiệu trung tâm",
        "news_header": "📰 Tin tức & Sự kiện",
        "contact_header": "📞 Thông tin liên hệ",
        "btn_add": "➕ Đăng bài mới",
        "btn_save": "💾 Lưu thay đổi bài viết",
        "btn_submit_news": "🚀 Xác nhận Đăng bài",
        "btn_edit_contact": "✏️ Chỉnh sửa thông tin Liên hệ",
        "btn_save_all_about": "💾 XÁC NHẬN CẬP NHẬT TOÀN BỘ GIỚI THIỆU",
        "preview_title": "👀 Giao diện xem trước công bố",
        "preview_info": "Đây là giao diện người xem sẽ nhìn thấy sau khi bạn nhấn nút Lưu.",
        "input_title": "Tiêu đề bài viết",
        "input_layout": "Chọn bố cục hiển thị:",
        "input_width": "Chiều rộng ảnh hiển thị (px):",
        "input_content": "Nội dung bài viết (Soạn thảo như Word):"
    },
    "en": {
        "about_header": "🏢 About iKids Edu",
        "news_header": "📰 News & Events",
        "contact_header": "📞 Contact Information",
        "btn_add": "➕ Post New Article",
        "btn_save": "💾 Save Article Changes",
        "btn_submit_news": "🚀 Confirm & Publish",
        "btn_edit_contact": "✏️ Edit Contact Information",
        "btn_save_all_about": "💾 CONFIRM & UPDATE ALL ABOUT US",
        "preview_title": "👀 Live Preview",
        "preview_info": "This is the layout parents will see after you click Save.",
        "input_title": "Article Title",
        "input_layout": "Select Display Layout:",
        "input_width": "Image Display Width (px):",
        "input_content": "Article Body Content (Word Editor Style):"
    }
}

@st.cache_data(ttl=2)
def get_cms_data(endpoint):
    try:
        res = requests.get(f"{API_URL}/{endpoint}", timeout=5)
        return res.json() if res.status_code == 200 else {}
    except: return {}

about_data = get_cms_data("about")
contact_data = get_cms_data("contact")
all_posts = get_cms_data("posts")

# ================= 3. HEADER GIAO DIỆN BIỂU MẪU =================
st.markdown("<div class='header-container'>", unsafe_allow_html=True)
col_logo, col_title = st.columns([1, 5])
with col_logo:
    logo_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "static/logo.png"))
    st.image(logo_path if os.path.exists(logo_path) else "https://api.dicebear.com/7.x/initials/svg?seed=iKids", width=95)
with col_title:
    st.markdown("<h1 style='margin:0;'>iKids Edu Headquarter</h1>", unsafe_allow_html=True)
    st.caption("🌐 Systems Content Management Multilang iKids v2.5")
st.markdown("</div>", unsafe_allow_html=True)
st.divider()

# ================= 4. BÀI GIỚI THIỆU (ABOUT) =================
about_title_vi = get_localized_value(about_data.get('title'), lang="vi", default_val="Về iKids Edu")
about_content_vi = get_localized_value(about_data.get('content'), lang="vi", default_val="")
about_content_display = get_localized_value(about_data.get('content'), lang=current_lang, default_val="")

if is_operator:
    st.subheader(UI_LABELS[current_lang]["about_header"])
    
    with st.expander("🛠️ THIẾT LẬP BÀI GIỚI THIỆU", expanded=False):
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

    st.markdown(f"### {UI_LABELS[current_lang]['preview_title']}")
    st.info(UI_LABELS[current_lang]["preview_info"])
    
    with st.container(border=True):
        # FIX 2: Thay thế ảnh preview mặc định
        preview_img = "static/anh_laptop.jpg" 
        if uploaded_about_imgs:
            preview_img = uploaded_about_imgs[0]
        elif about_data.get('images'):
            preview_img = about_data.get('images')[0]

        if about_layout == "Ảnh TRÁI - Chữ PHẢI":
            cp1, cp2 = st.columns([1, 1])
            cp1.image(preview_img, width=about_img_width)
            cp2.markdown(new_about_content if current_lang == 'vi' else about_content_display, unsafe_allow_html=True)
        elif about_layout == "Ảnh PHẢI - Chữ TRÁI":
            cp1, cp2 = st.columns([1, 1])
            cp1.markdown(new_about_content if current_lang == 'vi' else about_content_display, unsafe_allow_html=True)
            cp2.image(preview_img, width=about_img_width)
        else:
            st.image(preview_img, width=about_img_width)
            st.markdown(new_about_content if current_lang == 'vi' else about_content_display, unsafe_allow_html=True)

else:
    st.subheader(UI_LABELS[current_lang]["about_header"])
    
    layout = about_data.get('layout', 'left')
    images = about_data.get('images', [])
    # FIX 3: Thay thế ảnh hiển thị mặc định cho người xem
    img_main = images[0] if images else "static/anh_laptop.jpg"
    i_width = int(about_data.get('img_width', 500))

    if layout == "left":
        c1, c2 = st.columns([1, 1])
        c1.image(img_main, width=i_width)
        c2.markdown(about_content_display, unsafe_allow_html=True)
    elif layout == "right":
        c1, c2 = st.columns([1, 1])
        c1.markdown(about_content_display, unsafe_allow_html=True)
        c2.image(img_main, width=i_width)
    else:
        st.image(img_main, width=i_width)
        st.markdown(about_content_display, unsafe_allow_html=True)

st.write("")

# ================= 5. TIN TỨC & SỰ KIỆN =================
st.subheader(UI_LABELS[current_lang]["news_header"])

if "editing_post_data" not in st.session_state:
    st.session_state.editing_post_data = None

if is_operator:
    if st.button(UI_LABELS[current_lang]["btn_add"], type="primary"):
        st.session_state.show_add = True
        st.session_state.editing_post_data = None
    
    if st.session_state.get("show_add"):
        with st.container(border=True):
            st.write("#### 📝 Soạn bài mới")
            nt = st.text_input("Tiêu đề tin tức (*)")
            c_nl, c_ns = st.columns(2)
            nl = c_nl.selectbox("Chọn bố cục bài viết:", ["Ảnh Trái", "Ảnh Phải", "Dạng Banner"])
            ns = c_ns.slider("Kích thước ảnh đại diện (px):", 100, 800, 400, key="new_news_size")
            nc = st_quill(placeholder="Nội dung chi tiết...", html=True, key="q_add_news")
            ni = st.file_uploader("Tải ảnh đại diện bài viết", type=["png", "jpg", "jpeg"])
            
            if st.button(UI_LABELS[current_lang]["btn_submit_news"]):
                if nt and nc:
                    img_path = save_uploaded_file(ni) if ni else ""
                    l_val = "left" if nl == "Ảnh Trái" else ("right" if nl == "Ảnh Phải" else "full")
                    requests.post(f"{API_URL}/posts", json={
                        "title": nt, "content": nc, "image_url": img_path, 
                        "layout": l_val, "img_width": ns, "status": "published", "date": time.strftime("%d/%m/%Y")
                    })
                    st.session_state.show_add = False
                    st.rerun()

    if st.session_state.editing_post_data:
        p_edit = st.session_state.editing_post_data
        p_edit_title_vi = get_localized_value(p_edit.get('title'), lang="vi")
        p_edit_content_vi = get_localized_value(p_edit.get('content'), lang="vi")
        
        with st.container(border=True):
            st.write(f"#### 🛠️ Sửa bài: {p_edit_title_vi}")
            et = st.text_input("Sửa tiêu đề", value=p_edit_title_vi)
            ec_l, ec_s = st.columns(2)
            el = ec_l.selectbox("Sửa bố cục:", ["Ảnh Trái", "Ảnh Phải", "Dạng Banner"], 
                                index=0 if p_edit.get('layout')=="left" else (1 if p_edit.get('layout')=="right" else 2))
            es = ec_s.slider("Sửa kích thước ảnh (px):", 100, 800, int(p_edit.get('img_width', 400)))
            ec = st_quill(value=p_edit_content_vi, html=True, key="q_edit_news")
            ei = st.file_uploader("Tải ảnh mới thay thế:", type=["png", "jpg", "jpeg"])
            
            if st.button(UI_LABELS[current_lang]["btn_save"]):
                final_img = p_edit.get('image_url')
                if ei: final_img = save_uploaded_file(ei)
                l_val = "left" if el == "Ảnh Trái" else ("right" if el == "Ảnh Phải" else "full")
                requests.put(f"{API_URL}/posts/{p_edit.get('id')}", json={
                    "title": et, "content": ec, "image_url": final_img, "layout": l_val, "img_width": es
                })
                st.session_state.editing_post_data = None
                st.rerun()

display_posts = all_posts if is_operator else [p for p in all_posts if p.get('status') == 'published']
if display_posts:
    for p in display_posts:
        p_id = p.get('id', p.get('_id'))
        with st.container(border=True):
            # FIX 4: Thay thế ảnh hiển thị mặc định của tin tức
            img_p = p.get('image_url') or "static/anh_laptop.jpg"
            
            # Xử lý trường hợp ảnh upload bị lỗi đường dẫn tương đối
            if img_p.startswith("static/") and not os.path.exists(img_p):
                img_p = "static/anh_laptop.jpg" # Fallback an toàn

            p_width = int(p.get('img_width', 400))
            
            p_title_display = get_localized_value(p.get('title'), lang=current_lang, default_val="No Title")
            p_content_display = get_localized_value(p.get('content'), lang=current_lang, default_val="No Content")
            
            if p.get('layout') == "left":
                c1, c2 = st.columns([1, 2])
                c1.image(img_p, width=p_width)
                c2.markdown(f"### {p_title_display}\n{p_content_display}", unsafe_allow_html=True)
            elif p.get('layout') == "right":
                c1, c2 = st.columns([2, 1])
                c1.markdown(f"### {p_title_display}\n{p_content_display}", unsafe_allow_html=True)
                c2.image(img_p, width=p_width)
            else:
                st.image(img_p, width=p_width)
                st.markdown(f"### {p_title_display}\n{p_content_display}", unsafe_allow_html=True)
            
            if is_operator:
                oc1, oc2 = st.columns([1, 9])
                if oc1.button("✏️", key=f"ed_{p_id}"):
                    st.session_state.editing_post_data = p
                    st.rerun()
                if oc2.button("🗑️ Xóa", key=f"dl_{p_id}"):
                    requests.delete(f"{API_URL}/posts/{p_id}")
                    st.rerun()

# ================= 6. LIÊN HỆ & NÚT CẬP NHẬT TỔNG =================
st.write("")
st.divider()

if is_operator:
    st.subheader("📞 Quản lý thông tin liên hệ")
    if "editing_contact" not in st.session_state:
        st.session_state.editing_contact = False
    
    if st.button(UI_LABELS[current_lang]["btn_edit_contact"]):
        st.session_state.editing_contact = not st.session_state.editing_contact

    if st.session_state.editing_contact:
        contact_addr_vi = get_localized_value(contact_data.get('address'), lang="vi")
        with st.container(border=True):
            new_phone = st.text_input("Hotline", value=contact_data.get('phone', ''))
            new_email = st.text_input("Email hỗ trợ", value=contact_data.get('email', ''))
            new_addr = st.text_input("Địa chỉ trụ sở (Tiếng Việt)", value=contact_addr_vi)
            if st.button("💾 Chỉ lưu Liên hệ"):
                requests.put(f"{API_URL}/contact", json={"phone": new_phone, "email": new_email, "address": new_addr})
                st.session_state.editing_contact = False
                st.success("Đã cập nhật thông tin liên hệ!")
                time.sleep(1)
                st.rerun()

    st.write("")
    if st.button(UI_LABELS[current_lang]["btn_save_all_about"], type="primary", use_container_width=True):
        with st.spinner("Đang lưu và dịch bài giới thiệu..."):
            final_imgs = about_data.get('images', []) if keep_old else []
            if uploaded_about_imgs:
                for f in uploaded_about_imgs:
                    path = save_uploaded_file(f)
                    if path: final_imgs.append(path)
            
            l_val = "left" if about_layout == "Ảnh TRÁI - Chữ PHẢI" else ("right" if about_layout == "Ảnh PHẢI - Chữ TRÁI" else "full")
            requests.put(f"{API_URL}/about", json={
                "title": new_about_title, "content": new_about_content,
                "images": final_imgs, "layout": l_val, "img_width": about_img_width
            })
            st.success("Đã cập nhật thành công bài giới thiệu!")
            time.sleep(1)
            st.rerun()
else:
    contact_addr_display = get_localized_value(contact_data.get('address'), lang=current_lang, default_val="Đang cập nhật / Updating")
    
    st.markdown(f"""
    <div class="contact-footer">
        <h3>{UI_LABELS[current_lang]['contact_header']}</h3>
        <p>📍 <b>{"Địa chỉ / Address"}:</b> {contact_addr_display}</p>
        <p>✉️ <b>Email:</b> {contact_data.get('email', 'Đang cập nhật')}</p>
        <p>☎️ <b>Hotline:</b> {contact_data.get('phone', 'Đang cập nhật')}</p>
    </div>
    """, unsafe_allow_html=True)