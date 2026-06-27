# frontend/home.py

import os
import re
import time
import requests
import streamlit as st

# =========================================================
# HOME PUBLIC + CMS ADMIN/OPERATOR
# - Khách chưa đăng nhập vẫn xem được trang chủ
# - Admin/operator đăng nhập thì có tab chỉnh sửa CMS
# =========================================================

BACKEND_URL = st.session_state.get("api_url", os.getenv("API_URL", "http://localhost:8000"))
API_URL = f"{BACKEND_URL}/api/tv3"

current_lang = st.session_state.get("lang", "vi")
role = str(st.session_state.get("role", "")).lower()
token = st.session_state.get("token") or st.session_state.get("access_token") or ""

is_operator = role in ["admin", "operator"]


# =========================================================
# LABELS
# =========================================================

UI_LABELS = {
    "vi": {
        "header_title": "iKids Education Portal",
        "header_subtitle": "Hệ thống học tập thông minh dành cho trung tâm, giáo viên, phụ huynh và học sinh.",
        "public_hint": "Trang chủ này ai cũng có thể xem. Bạn hãy đăng nhập/đăng ký bên cạnh để trải nghiệm nhé!",
        "cms_title": "Quản trị nội dung trang chủ",
        "tab_preview": "Xem trang chủ",
        "tab_about": "Giới thiệu",
        "tab_news": "Tin tức & Sự kiện",
        "tab_contact": "Liên hệ",
        "about_header": "Về iKids Edu",
        "news_header": "Tin tức & Sự kiện",
        "contact_header": "Thông tin liên hệ",
        "input_title": "Tiêu đề",
        "input_content": "Nội dung",
        "input_layout": "Bố cục hiển thị",
        "input_width": "Kích thước ảnh",
        "preview_title": "Xem trước",
        "btn_save_about": "Lưu Giới thiệu",
        "btn_save_contact": "Lưu thông tin Liên hệ",
        "btn_add_news": "Soạn bài mới",
        "btn_submit_news": "Đăng bài",
        "btn_save_news": "Lưu bài viết",
        "btn_cancel": "Hủy",
        "btn_edit": "Sửa",
        "btn_delete": "Xóa",
        "btn_back": "Quay lại trang chủ",
        "msg_saved_about": "Đã cập nhật Giới thiệu!",
        "msg_saved_contact": "Đã cập nhật thông tin liên hệ!",
        "msg_post_created": "Đăng bài thành công!",
        "msg_post_updated": "Lưu bài viết thành công!",
        "msg_post_deleted": "Đã xóa bài viết!",
        "msg_empty_news": "Hiện chưa có tin tức nào được xuất bản.",
        "msg_no_about": "Nội dung giới thiệu đang được cập nhật.",
        "msg_no_contact": "Thông tin liên hệ đang được cập nhật.",
        "read_more": "Đọc chi tiết ➔",
        "date_label": "Ngày đăng",
        "address": "Địa chỉ",
        "email": "Email",
        "phone": "Hotline",
        "upload_image": "Tải ảnh lên",
        "keep_old_image": "Giữ ảnh cũ nếu không chọn ảnh mới",
        "post_title": "Tiêu đề tin tức (*)",
        "post_content": "Nội dung tin tức (*)",
        "post_image": "Ảnh đại diện",
        "post_status": "Trạng thái",
        "published": "published",
        "draft": "draft",
        "list_posts": "Danh sách bài viết",
        "not_found": "Không tìm thấy bài viết hoặc bài viết đã bị xóa.",
    },
    "en": {
        "header_title": "iKids Education Portal",
        "header_subtitle": "A smart learning platform for centers, teachers, parents, and students.",
        "public_hint": "This homepage is public. Admin/operators can edit content after signing in.",
        "cms_title": "Homepage CMS",
        "tab_preview": "Preview Homepage",
        "tab_about": "About",
        "tab_news": "News & Events",
        "tab_contact": "Contact",
        "about_header": "About iKids Edu",
        "news_header": "News & Events",
        "contact_header": "Contact Information",
        "input_title": "Title",
        "input_content": "Content",
        "input_layout": "Display layout",
        "input_width": "Image width",
        "preview_title": "Preview",
        "btn_save_about": "Save About",
        "btn_save_contact": "Save Contact",
        "btn_add_news": "New Post",
        "btn_submit_news": "Publish Post",
        "btn_save_news": "Save Post",
        "btn_cancel": "Cancel",
        "btn_edit": "Edit",
        "btn_delete": "Delete",
        "btn_back": "Back to Home",
        "msg_saved_about": "About section updated!",
        "msg_saved_contact": "Contact information updated!",
        "msg_post_created": "Post published successfully!",
        "msg_post_updated": "Post updated successfully!",
        "msg_post_deleted": "Post deleted!",
        "msg_empty_news": "No news has been published yet.",
        "msg_no_about": "About content is being updated.",
        "msg_no_contact": "Contact information is being updated.",
        "read_more": "Read more ➔",
        "date_label": "Published",
        "address": "Address",
        "email": "Email",
        "phone": "Hotline",
        "upload_image": "Upload image",
        "keep_old_image": "Keep old image if no new image is selected",
        "post_title": "News title (*)",
        "post_content": "News content (*)",
        "post_image": "Cover image",
        "post_status": "Status",
        "published": "published",
        "draft": "draft",
        "list_posts": "Post list",
        "not_found": "Article not found or deleted.",
    },
}

L = UI_LABELS.get(current_lang, UI_LABELS["vi"])


# =========================================================
# CSS
# =========================================================

st.markdown(
    """
    <style>
    .home-hero {
        padding: 42px 36px;
        border-radius: 24px;
        background: linear-gradient(135deg, #1e3a8a, #0f766e);
        color: white;
        margin-bottom: 26px;
        box-shadow: 0 12px 28px rgba(15, 23, 42, 0.18);
    }
    .home-hero h1 {
        margin: 0;
        font-size: 42px;
        font-weight: 900;
    }
    .home-hero p {
        font-size: 18px;
        margin-top: 12px;
        max-width: 850px;
        line-height: 1.6;
    }
    .news-carousel-wrapper {
        display: flex;
        gap: 18px;
        overflow-x: auto;
        padding: 10px 4px 20px 4px;
        scroll-snap-type: x mandatory;
    }
    .news-card-hz {
        min-width: 290px;
        max-width: 290px;
        border-radius: 18px;
        overflow: hidden;
        background: white;
        border: 1px solid #e2e8f0;
        box-shadow: 0 8px 20px rgba(15, 23, 42, 0.08);
        scroll-snap-align: start;
    }
    .news-img-hz {
        width: 100%;
        height: 170px;
        object-fit: cover;
        background: #f1f5f9;
    }
    .news-body-hz {
        padding: 16px;
    }
    .news-title-hz {
        margin: 0;
        font-size: 1.05rem;
        color: #1e3a8a;
        line-height: 1.35;
    }
    .news-date-hz {
        margin-top: 8px;
        font-size: 0.82rem;
        color: #64748b;
        font-weight: 600;
    }
    .news-excerpt-hz {
        margin-top: 10px;
        color: #475569;
        font-size: 0.92rem;
        line-height: 1.45;
        min-height: 58px;
        max-height: 58px;
        overflow: hidden;
    }
    .read-more-btn {
        display: inline-block;
        margin-top: 10px;
        padding: 8px 12px;
        border-radius: 999px;
        background: #0f766e;
        color: white !important;
        text-decoration: none !important;
        font-weight: 700;
        font-size: 0.85rem;
    }
    .contact-footer {
        padding: 24px;
        border-radius: 18px;
        background: linear-gradient(135deg, #1e3a8a, #0f172a);
        color: white;
        margin-top: 22px;
    }
    .contact-footer h3 {
        margin-top: 0;
        color: white;
    }
    .contact-footer p {
        margin: 8px 0;
        color: #e2e8f0;
    }
    .news-detail-content {
        font-size: 1.08rem;
        line-height: 1.8;
        color: #334155;
        margin-top: 20px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# =========================================================
# HELPERS
# =========================================================

def get_headers():
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


def strip_html_tags(raw):
    if not raw:
        return ""

    raw = str(raw)
    raw = re.sub(r"<br\s*/?>", "\n", raw, flags=re.IGNORECASE)
    raw = re.sub(r"</p>", "\n\n", raw, flags=re.IGNORECASE)
    raw = re.sub(r"<[^>]*>", "", raw)

    return raw.strip()


def text_to_html(text):
    if not text:
        return ""
    return str(text).replace("\n", "<br>")


def get_localized_value(data_field, lang="vi", default_val=""):
    if not data_field:
        return default_val

    if isinstance(data_field, dict):
        return (
            data_field.get(lang)
            or data_field.get("vi")
            or data_field.get("en")
            or default_val
        )

    return str(data_field)


def get_valid_image_url(img_path):
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


@st.cache_data(ttl=20)
def get_cms_data(endpoint):
    try:
        res = requests.get(f"{API_URL}/{endpoint}", timeout=15)
        if res.status_code == 200:
            return res.json()
    except Exception:
        pass

    if endpoint == "posts":
        return []

    return {}


def refresh_cms():
    st.cache_data.clear()
    time.sleep(0.3)
    st.rerun()


def upload_image_to_backend(uploaded_file):
    if uploaded_file is None:
        return {"image_url": "", "image_public_id": ""}

    try:
        files = {
            "file": (
                uploaded_file.name,
                uploaded_file.getvalue(),
                uploaded_file.type,
            )
        }

        res = requests.post(
            f"{API_URL}/upload_image",
            files=files,
            timeout=60,
        )

        if res.status_code == 200:
            data = res.json()
            return {
                "image_url": data.get("image_url", ""),
                "image_public_id": data.get("image_public_id") or data.get("public_id", ""),
            }

        st.error(res.text)

    except Exception as e:
        st.error(f"Lỗi upload ảnh: {e}")

    return {"image_url": "", "image_public_id": ""}


def display_about_card(title, content, img_url, layout="left", img_width=500):
    img_url = get_valid_image_url(img_url)
    clean_content = content or L["msg_no_about"]

    if layout == "right":
        col_text, col_img = st.columns([2, 1])
        with col_text:
            st.markdown(f"### {title}")
            st.markdown(clean_content, unsafe_allow_html=True)
        with col_img:
            st.image(img_url, use_container_width=True)

    elif layout == "full":
        st.image(img_url, use_container_width=True)
        st.markdown(f"### {title}")
        st.markdown(clean_content, unsafe_allow_html=True)

    else:
        col_img, col_text = st.columns([1, 2])
        with col_img:
            st.image(img_url, use_container_width=True)
        with col_text:
            st.markdown(f"### {title}")
            st.markdown(clean_content, unsafe_allow_html=True)


def render_horizontal_news_carousel(posts):
    if not posts:
        st.info(L["msg_empty_news"])
        return

    carousel_html = '<div class="news-carousel-wrapper">\n'

    for p in posts:
        post_id = str(p.get("id", p.get("_id", "")))
        img_url = get_valid_image_url(p.get("image_url"))
        title = get_localized_value(p.get("title"), lang=current_lang, default_val="No Title")
        raw_content = get_localized_value(p.get("content"), lang=current_lang, default_val="")
        clean_content = strip_html_tags(raw_content)
        date = p.get("date", "")

        card_html = f"""
<div class="news-card-hz">
    <img class="news-img-hz" src="{img_url}">
    <div class="news-body-hz">
        <h4 class="news-title-hz">{title}</h4>
        <div class="news-date-hz">🕒 {date}</div>
        <p class="news-excerpt-hz">{clean_content}</p>
        <a href="?post_id={post_id}" target="_self" class="read-more-btn">{L['read_more']}</a>
    </div>
</div>
"""
        carousel_html += card_html

    carousel_html += "</div>"
    st.markdown(carousel_html, unsafe_allow_html=True)


def get_query_param(name):
    try:
        value = st.query_params.get(name)
        if isinstance(value, list):
            return value[0] if value else None
        return value
    except Exception:
        return None


def show_news_detail(post_id, posts):
    post = next(
        (p for p in posts if str(p.get("id", p.get("_id", ""))) == str(post_id)),
        None,
    )

    if st.button(f"🔙 {L['btn_back']}", key="btn_back_top"):
        st.query_params.clear()
        st.rerun()

    st.divider()

    if not post:
        st.error(L["not_found"])
        return

    title = get_localized_value(post.get("title"), lang=current_lang, default_val="No Title")
    content = get_localized_value(post.get("content"), lang=current_lang, default_val="")
    img_url = get_valid_image_url(post.get("image_url"))
    date = post.get("date", "")

    st.markdown(
        f"<h1 style='color:#1e3a8a; font-size:2.2rem;'>{title}</h1>",
        unsafe_allow_html=True,
    )
    st.markdown(
        f"<p style='color:#64748b; font-weight:700;'>🕒 {L['date_label']}: {date}</p>",
        unsafe_allow_html=True,
    )

    c1, c2, c3 = st.columns([1, 8, 1])
    with c2:
        st.image(img_url, use_container_width=True)

    st.markdown(
        f"<div class='news-detail-content'>{content}</div>",
        unsafe_allow_html=True,
    )

    st.divider()

    if st.button(f"🔙 {L['btn_back']}", key="btn_back_bottom"):
        st.query_params.clear()
        st.rerun()


# =========================================================
# DATA
# =========================================================

about_data = get_cms_data("about") or {}
contact_data = get_cms_data("contact") or {}
all_posts = get_cms_data("posts") or []

if not isinstance(about_data, dict):
    about_data = {}

if not isinstance(contact_data, dict):
    contact_data = {}

if not isinstance(all_posts, list):
    all_posts = []

published_posts = [
    p for p in all_posts
    if isinstance(p, dict) and p.get("status", "published") == "published"
]


# =========================================================
# HEADER
# =========================================================

st.markdown(
    f"""
    <div class="home-hero">
        <h1>{L['header_title']}</h1>
        <p>{L['header_subtitle']}</p>
        <p style="
            display:inline-block;
            padding:10px 14px;
            background:rgba(255,255,255,0.15);
            border-radius:14px;
            font-size:0.95rem;
        ">{L['public_hint']}</p>
    </div>
    """,
    unsafe_allow_html=True,
)

selected_post_id = get_query_param("post_id")


# =========================================================
# DETAIL PAGE
# =========================================================

if selected_post_id:
    show_news_detail(selected_post_id, all_posts)
    st.stop()


# =========================================================
# CMS ADMIN/OPERATOR
# =========================================================

def render_cms_about_tab():
    about_title_vi = get_localized_value(
        about_data.get("title"),
        lang="vi",
        default_val="Về iKids Edu",
    )
    about_content_vi = strip_html_tags(
        get_localized_value(
            about_data.get("content"),
            lang="vi",
            default_val="",
        )
    )

    new_about_title = st.text_input(L["input_title"], value=about_title_vi)

    c_lay, c_size = st.columns(2)

    layout_options = {
        "Ảnh TRÁI - Chữ PHẢI": "left",
        "Ảnh PHẢI - Chữ TRÁI": "right",
        "Banner (Ảnh TRÊN)": "full",
    }

    reverse_layout = {
        "left": 0,
        "right": 1,
        "full": 2,
    }

    current_layout = about_data.get("layout", "left")

    selected_layout_label = c_lay.selectbox(
        L["input_layout"],
        list(layout_options.keys()),
        index=reverse_layout.get(current_layout, 0),
    )

    preview_layout = layout_options[selected_layout_label]

    about_img_width = c_size.slider(
        L["input_width"],
        200,
        1000,
        int(about_data.get("img_width", 500) or 500),
    )

    new_about_content_text = st.text_area(
        L["input_content"],
        value=about_content_vi,
        height=180,
    )

    uploaded_about_imgs = st.file_uploader(
        L["upload_image"],
        type=["png", "jpg", "jpeg", "webp", "gif"],
        accept_multiple_files=True,
        key="about_imgs",
    )

    keep_old = st.checkbox(L["keep_old_image"], value=True)

    old_images = about_data.get("images", [])
    old_public_ids = about_data.get("image_public_ids", [])

    if not isinstance(old_images, list):
        old_images = []

    if not isinstance(old_public_ids, list):
        old_public_ids = []

    preview_img = ""
    if uploaded_about_imgs:
        preview_img = uploaded_about_imgs[0]
    elif old_images:
        preview_img = old_images[0]

    st.markdown("---")
    st.markdown(f"#### {L['preview_title']}")

    display_about_card(
        new_about_title,
        text_to_html(new_about_content_text),
        preview_img,
        preview_layout,
        about_img_width,
    )

    if st.button(L["btn_save_about"], type="primary", use_container_width=True):
        with st.spinner("Đang lưu..."):
            new_imgs = []
            new_public_ids = []

            if uploaded_about_imgs:
                for f in uploaded_about_imgs:
                    upload_data = upload_image_to_backend(f)
                    if upload_data["image_url"]:
                        new_imgs.append(upload_data["image_url"])
                        new_public_ids.append(upload_data["image_public_id"])

            final_imgs = []
            final_public_ids = []

            if keep_old:
                final_imgs.extend(old_images)
                final_public_ids.extend(old_public_ids)

            final_imgs = new_imgs + final_imgs
            final_public_ids = new_public_ids + final_public_ids

            payload = {
                "title": new_about_title,
                "content": text_to_html(new_about_content_text),
                "images": final_imgs,
                "image_public_ids": final_public_ids,
                "layout": preview_layout,
                "img_width": about_img_width,
            }

            res = requests.put(
                f"{API_URL}/about",
                json=payload,
                headers=get_headers(),
                timeout=30,
            )

            if res.status_code == 200:
                st.success(L["msg_saved_about"])
                refresh_cms()
            else:
                st.error(res.text)


def render_cms_news_tab():
    if "editing_post_data" not in st.session_state:
        st.session_state.editing_post_data = None

    if "show_add_post" not in st.session_state:
        st.session_state.show_add_post = False

    col_add, col_cancel = st.columns([1, 3])

    with col_add:
        if st.button(L["btn_add_news"], type="primary", use_container_width=True):
            st.session_state.show_add_post = True
            st.session_state.editing_post_data = None
            st.rerun()

    with col_cancel:
        if st.session_state.show_add_post or st.session_state.editing_post_data:
            if st.button(L["btn_cancel"], use_container_width=False):
                st.session_state.show_add_post = False
                st.session_state.editing_post_data = None
                st.rerun()

    edit_mode = st.session_state.editing_post_data is not None
    show_form = st.session_state.show_add_post or edit_mode

    if show_form:
        p_edit = st.session_state.editing_post_data or {}

        old_title = get_localized_value(p_edit.get("title"), lang="vi", default_val="")
        old_content = strip_html_tags(
            get_localized_value(p_edit.get("content"), lang="vi", default_val="")
        )
        old_img = p_edit.get("image_url", "")
        old_public_id = p_edit.get("image_public_id", "")

        with st.container(border=True):
            st.write("#### 🛠️ Sửa bài viết" if edit_mode else "#### 📝 Soạn bài mới")

            post_title = st.text_input(
                L["post_title"],
                value=old_title,
                key="post_title_form",
            )

            post_content = st.text_area(
                L["post_content"],
                value=old_content,
                height=220,
                key="post_content_form",
            )

            post_status = st.selectbox(
                L["post_status"],
                options=["published", "draft"],
                index=0 if p_edit.get("status", "published") == "published" else 1,
            )

            post_img = st.file_uploader(
                L["post_image"],
                type=["png", "jpg", "jpeg", "webp", "gif"],
                key="post_img_form",
            )

            if old_img and not post_img:
                st.caption(L["keep_old_image"])
                st.image(get_valid_image_url(old_img), width=260)

            if st.button(
                L["btn_save_news"] if edit_mode else L["btn_submit_news"],
                type="primary",
                use_container_width=True,
            ):
                if not post_title.strip() or not post_content.strip():
                    st.error("Vui lòng nhập tiêu đề và nội dung.")
                else:
                    image_url = old_img
                    image_public_id = old_public_id

                    if post_img:
                        upload_data = upload_image_to_backend(post_img)
                        image_url = upload_data["image_url"]
                        image_public_id = upload_data["image_public_id"]

                    payload = {
                        "title": post_title.strip(),
                        "content": text_to_html(post_content),
                        "image_url": image_url,
                        "image_public_id": image_public_id,
                        "layout": "full",
                        "img_width": 500,
                        "status": post_status,
                        "date": p_edit.get("date") or time.strftime("%d/%m/%Y"),
                    }

                    if edit_mode:
                        post_id = p_edit.get("id") or p_edit.get("_id")
                        res = requests.put(
                            f"{API_URL}/posts/{post_id}",
                            json=payload,
                            headers=get_headers(),
                            timeout=30,
                        )
                        success_msg = L["msg_post_updated"]
                    else:
                        res = requests.post(
                            f"{API_URL}/posts",
                            json=payload,
                            headers=get_headers(),
                            timeout=30,
                        )
                        success_msg = L["msg_post_created"]

                    if res.status_code in [200, 201]:
                        st.session_state.show_add_post = False
                        st.session_state.editing_post_data = None
                        st.success(success_msg)
                        refresh_cms()
                    else:
                        st.error(res.text)

    st.divider()
    st.write(f"### {L['list_posts']} ({len(all_posts)})")

    if not all_posts:
        st.info(L["msg_empty_news"])
        return

    for p in all_posts:
        p_id = p.get("id") or p.get("_id")
        p_title_display = get_localized_value(p.get("title"), lang=current_lang, default_val="No Title")
        img_p = get_valid_image_url(p.get("image_url"))

        with st.container(border=True):
            c1, c2, c3 = st.columns([1.2, 4, 1.5])

            with c1:
                st.image(img_p, use_container_width=True)

            with c2:
                st.markdown(f"**{p_title_display}**")
                st.caption(f"{L['date_label']}: {p.get('date', '---')}")
                st.caption(f"Status: {p.get('status', 'published')}")

            with c3:
                if st.button(L["btn_edit"], key=f"edit_post_{p_id}", use_container_width=True):
                    st.session_state.editing_post_data = p
                    st.session_state.show_add_post = False
                    st.rerun()

                if st.button(L["btn_delete"], key=f"delete_post_{p_id}", use_container_width=True):
                    res = requests.delete(
                        f"{API_URL}/posts/{p_id}",
                        headers=get_headers(),
                        timeout=30,
                    )

                    if res.status_code == 200:
                        st.success(L["msg_post_deleted"])
                        refresh_cms()
                    else:
                        st.error(res.text)


def render_cms_contact_tab():
    contact_addr_vi = get_localized_value(contact_data.get("address"), lang="vi", default_val="")
    contact_desc_vi = strip_html_tags(
        get_localized_value(contact_data.get("description"), lang="vi", default_val="")
    )

    with st.container(border=True):
        st.write("#### ☎️ Cập nhật thông tin liên hệ")

        new_phone = st.text_input(
            L["phone"],
            value=contact_data.get("phone", ""),
        )

        new_email = st.text_input(
            L["email"],
            value=contact_data.get("email", ""),
        )

        new_addr = st.text_input(
            L["address"],
            value=contact_addr_vi,
        )

        new_desc = st.text_area(
            L["input_content"],
            value=contact_desc_vi,
            height=120,
        )

        if st.button(L["btn_save_contact"], type="primary", use_container_width=True):
            payload = {
                "phone": new_phone,
                "email": new_email,
                "address": new_addr,
                "description": text_to_html(new_desc),
            }

            res = requests.put(
                f"{API_URL}/contact",
                json=payload,
                headers=get_headers(),
                timeout=30,
            )

            if res.status_code == 200:
                st.success(L["msg_saved_contact"])
                refresh_cms()
            else:
                st.error(res.text)


def render_public_home():
    about_title = get_localized_value(
        about_data.get("title"),
        lang=current_lang,
        default_val=L["about_header"],
    )

    about_content = get_localized_value(
        about_data.get("content"),
        lang=current_lang,
        default_val=L["msg_no_about"],
    )

    layout = about_data.get("layout", "left")
    images = about_data.get("images", [])

    if not isinstance(images, list):
        images = []

    img_main = images[0] if images else ""

    st.subheader(L["about_header"])
    display_about_card(
        about_title,
        about_content,
        img_main,
        layout,
        int(about_data.get("img_width", 500) or 500),
    )

    st.write("")
    st.divider()

    st.subheader(L["news_header"])
    render_horizontal_news_carousel(published_posts)

    st.write("")
    st.divider()

    contact_addr_display = get_localized_value(
        contact_data.get("address"),
        lang=current_lang,
        default_val="Đang cập nhật" if current_lang == "vi" else "Updating",
    )

    contact_desc = get_localized_value(
        contact_data.get("description"),
        lang=current_lang,
        default_val="",
    )

    st.markdown(
        f"""
        <div class="contact-footer">
            <h3>{L['contact_header']}</h3>
            <p>{contact_desc}</p>
            <p>📍 <b>{L['address']}:</b> {contact_addr_display}</p>
            <p>✉️ <b>{L['email']}:</b> {contact_data.get('email', 'Đang cập nhật')}</p>
            <p>☎️ <b>{L['phone']}:</b> {contact_data.get('phone', 'Đang cập nhật')}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


if is_operator:
    st.markdown(f"## 🛠️ {L['cms_title']}")

    tab_preview, tab_about, tab_news, tab_contact = st.tabs(
        [
            L["tab_preview"],
            L["tab_about"],
            L["tab_news"],
            L["tab_contact"],
        ]
    )

    with tab_preview:
        render_public_home()

    with tab_about:
        render_cms_about_tab()

    with tab_news:
        render_cms_news_tab()

    with tab_contact:
        render_cms_contact_tab()

else:
    render_public_home()
