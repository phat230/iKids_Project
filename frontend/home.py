# frontend/home.py

import streamlit as st
import requests
import os
import re

# =========================
# TRANG CHỦ PUBLIC
# Ai cũng xem được, không cần đăng nhập
# =========================

BACKEND_URL = st.session_state.get("api_url", os.getenv("API_URL", "http://localhost:8000"))
API_TV3 = f"{BACKEND_URL}/api/tv3"

lang = st.session_state.get("lang", "vi")


# =========================
# CSS
# =========================
def load_css(file_name):
    try:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        css_root = os.path.abspath(os.path.join(current_dir, "CSS"))
        full_path = os.path.join(css_root, file_name)

        if os.path.exists(full_path):
            with open(full_path, "r", encoding="utf-8") as f:
                st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    except Exception:
        pass


load_css("home.css")


# =========================
# LABELS
# =========================
HOME_LABELS = {
    "vi": {
        "hero_title": "iKids Education Portal",
        "hero_subtitle": "Hệ thống học tập thông minh dành cho trung tâm, giáo viên, phụ huynh và học sinh.",
        "btn_login_hint": "Bạn có thể đăng nhập hoặc đăng ký tài khoản ở thanh menu bên trái.",
        "about_title": "Về chúng tôi",
        "news_title": "Tin tức & Sự kiện",
        "contact_title": "Thông tin liên hệ",
        "address": "Địa chỉ",
        "email": "Email",
        "phone": "Hotline",
        "empty_about": "Nội dung giới thiệu đang được cập nhật.",
        "empty_news": "Hiện chưa có tin tức nào được xuất bản.",
        "empty_contact": "Thông tin liên hệ đang được cập nhật.",
        "read_more": "Xem chi tiết",
        "published_date": "Ngày đăng",
        "feature_1_title": "Quản lý lớp học",
        "feature_1_desc": "Theo dõi lớp học, lịch học, giáo viên và học sinh.",
        "feature_2_title": "Kết nối phụ huynh",
        "feature_2_desc": "Phụ huynh xem lịch học, học phí, báo cáo và thông báo.",
        "feature_3_title": "Học tập thông minh",
        "feature_3_desc": "Hỗ trợ quiz, video học liệu, điểm danh và đánh giá.",
    },
    "en": {
        "hero_title": "iKids Education Portal",
        "hero_subtitle": "A smart learning platform for centers, teachers, parents, and students.",
        "btn_login_hint": "You can sign in or register from the left sidebar menu.",
        "about_title": "About Us",
        "news_title": "News & Events",
        "contact_title": "Contact Information",
        "address": "Address",
        "email": "Email",
        "phone": "Hotline",
        "empty_about": "About content is being updated.",
        "empty_news": "No news has been published yet.",
        "empty_contact": "Contact information is being updated.",
        "read_more": "Read more",
        "published_date": "Published",
        "feature_1_title": "Class Management",
        "feature_1_desc": "Track classes, schedules, teachers, and students.",
        "feature_2_title": "Parent Connection",
        "feature_2_desc": "Parents can view schedules, tuition, reports, and notifications.",
        "feature_3_title": "Smart Learning",
        "feature_3_desc": "Support quizzes, learning videos, attendance, and assessment.",
    },
}

L = HOME_LABELS.get(lang, HOME_LABELS["vi"])


# =========================
# HELPERS
# =========================
def clean_html_to_text(raw):
    if not raw:
        return ""

    raw = str(raw)
    raw = re.sub(r"<br\s*/?>", "\n", raw, flags=re.IGNORECASE)
    raw = re.sub(r"</p>", "\n\n", raw, flags=re.IGNORECASE)
    raw = re.sub(r"<[^>]*>", "", raw)

    return raw.strip()


def get_localized(field, default=""):
    if not field:
        return default

    if isinstance(field, dict):
        return field.get(lang) or field.get("vi") or field.get("en") or default

    return str(field)


def get_image_url(img_path):
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


@st.cache_data(ttl=30)
def fetch_json(url, default_value):
    try:
        res = requests.get(url, timeout=15)

        if res.status_code == 200:
            return res.json()

        return default_value

    except Exception:
        return default_value


def safe_list(data):
    return data if isinstance(data, list) else []


def safe_dict(data):
    return data if isinstance(data, dict) else {}


# =========================
# FETCH CMS PUBLIC DATA
# =========================
about_data = safe_dict(fetch_json(f"{API_TV3}/about", {}))
contact_data = safe_dict(fetch_json(f"{API_TV3}/contact", {}))
posts_data = safe_list(fetch_json(f"{API_TV3}/posts", []))

published_posts = [
    p for p in posts_data
    if isinstance(p, dict) and p.get("status", "published") == "published"
]


# =========================
# HERO
# =========================
st.markdown(
    f"""
    <div style="
        padding: 42px 36px;
        border-radius: 24px;
        background: linear-gradient(135deg, #1e3a8a, #0f766e);
        color: white;
        margin-bottom: 28px;
        box-shadow: 0 12px 30px rgba(15, 23, 42, 0.18);
    ">
        <h1 style="margin:0; font-size:42px; font-weight:900;">{L['hero_title']}</h1>
        <p style="font-size:18px; margin-top:12px; max-width:850px; line-height:1.6;">
            {L['hero_subtitle']}
        </p>
        <p style="
            margin-top:18px;
            padding:12px 16px;
            background:rgba(255,255,255,0.14);
            border-radius:14px;
            display:inline-block;
        ">
            {L['btn_login_hint']}
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)


# =========================
# FEATURES
# =========================
f1, f2, f3 = st.columns(3)

with f1:
    st.container(border=True).markdown(
        f"### 📚 {L['feature_1_title']}\n{L['feature_1_desc']}"
    )

with f2:
    st.container(border=True).markdown(
        f"### 👨‍👩‍👧 {L['feature_2_title']}\n{L['feature_2_desc']}"
    )

with f3:
    st.container(border=True).markdown(
        f"### 🤖 {L['feature_3_title']}\n{L['feature_3_desc']}"
    )

st.write("")


# =========================
# ABOUT
# =========================
st.subheader(L["about_title"])

about_title = get_localized(about_data.get("title"), "iKids Education")
about_content = clean_html_to_text(get_localized(about_data.get("content"), ""))

about_images = about_data.get("images", [])
about_img = get_image_url(about_images[0]) if isinstance(about_images, list) and about_images else ""

with st.container(border=True):
    col_img, col_text = st.columns([1, 2])

    with col_img:
        if about_img:
            st.image(about_img, use_container_width=True)

    with col_text:
        st.markdown(f"### {about_title}")
        st.write(about_content or L["empty_about"])


st.write("")


# =========================
# NEWS
# =========================
st.subheader(L["news_title"])

if not published_posts:
    st.info(L["empty_news"])
else:
    cols = st.columns(3)

    for idx, post in enumerate(published_posts[:6]):
        with cols[idx % 3]:
            post_title = get_localized(post.get("title"), "No title")
            post_content = clean_html_to_text(get_localized(post.get("content"), ""))
            post_img = get_image_url(post.get("image_url"))
            post_date = post.get("date", "---")

            with st.container(border=True):
                st.image(post_img, use_container_width=True)
                st.markdown(f"#### {post_title}")
                st.caption(f"{L['published_date']}: {post_date}")

                if post_content:
                    st.write(post_content[:180] + ("..." if len(post_content) > 180 else ""))


st.write("")


# =========================
# CONTACT
# =========================
st.subheader(L["contact_title"])

address = get_localized(contact_data.get("address"), "")
description = clean_html_to_text(get_localized(contact_data.get("description"), ""))
phone = contact_data.get("phone", "")
email = contact_data.get("email", "")

with st.container(border=True):
    if not contact_data:
        st.info(L["empty_contact"])
    else:
        if description:
            st.write(description)

        c1, c2, c3 = st.columns(3)

        with c1:
            st.markdown(f"**📍 {L['address']}**")
            st.write(address or "---")

        with c2:
            st.markdown(f"**📧 {L['email']}**")
            st.write(email or "---")

        with c3:
            st.markdown(f"**☎️ {L['phone']}**")
            st.write(phone or "---")