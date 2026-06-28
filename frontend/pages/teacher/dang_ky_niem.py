import streamlit as st
import requests
import os
import time
from datetime import datetime

from utils.role_guard import require_role

# ================= CRITICAL: CẤU HÌNH TRANG LUÔN ĐỂ ĐẦU FILE =================
st.set_page_config(page_title="Đăng Kỷ Niệm", page_icon="📸", layout="wide")

require_role(["teacher", "admin", "operator"])

BACKEND_URL = st.session_state.get("api_url", "http://localhost:8000")
API_TV1 = f"{BACKEND_URL}/api/tv1"
API_TV3 = f"{BACKEND_URL}/api/tv3"

lang = st.session_state.get("lang", "vi")
user_id = st.session_state.get("user_id")
token = st.session_state.get("access_token") or st.session_state.get("token")
user_info = st.session_state.get("user_info", {}) or {}
role = st.session_state.get("role", "").lower()


# ================= CSS =================
def load_css(file_name):
    current_dir = os.path.dirname(os.path.abspath(__file__))
    css_root = os.path.abspath(os.path.join(current_dir, "../../CSS"))
    full_path = os.path.join(css_root, file_name)

    if os.path.exists(full_path):
        with open(full_path, "r", encoding="utf-8") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)


load_css("teacher/teacher_global.css")

st.markdown(
    """
    <style>
    .memory-note {
        padding: 14px 16px;
        border-radius: 14px;
        background: #ecfeff;
        border: 1px solid #67e8f9;
        color: #155e75;
        margin-bottom: 16px;
        font-weight: 600;
    }

    .memory-preview-box {
        padding: 16px;
        border-radius: 16px;
        background: #f8fafc;
        border: 1px dashed #94a3b8;
        margin-top: 12px;
    }

    .memory-desc {
        font-size: 1rem;
        line-height: 1.6;
        color: #334155;
        margin-top: 10px;
    }

    img {
        border-radius: 14px !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


LABELS = {
    "vi": {
        "title": "📸 Đăng Ảnh Kỷ Niệm Lớp Học",
        "subtitle": "Giáo viên chia sẻ hình ảnh hoạt động học tập, vui chơi và các khoảnh khắc đáng nhớ của lớp mình phụ trách.",
        "tab_post": "📝 Đăng kỷ niệm mới",
        "tab_list": "📚 Kỷ niệm đã đăng",
        "select_class": "Chọn lớp học (*)",
        "input_title": "Tiêu đề / Chủ đề kỷ niệm",
        "input_desc": "Mô tả kỷ niệm (*)",
        "placeholder_desc": "Ví dụ: Hôm nay các bé tham gia hoạt động nhóm rất vui vẻ...",
        "input_image": "Chọn ảnh kỷ niệm (*)",
        "btn_submit": "🚀 Đăng kỷ niệm",
        "btn_refresh": "🔄 Làm mới",
        "warn_login": "Vui lòng đăng nhập lại.",
        "warn_missing": "Vui lòng chọn lớp, nhập mô tả và chọn ảnh.",
        "warn_no_class": "Bạn chưa được phân công lớp nào hoặc hệ thống chưa có dữ liệu lớp học.",
        "uploading": "Đang tải ảnh lên Cloudinary...",
        "posting": "Đang lưu kỷ niệm...",
        "success": "Đăng kỷ niệm thành công!",
        "failed": "Không thể đăng kỷ niệm:",
        "empty": "Chưa có kỷ niệm nào.",
        "teacher": "Giáo viên",
        "posted_at": "Ngày đăng",
        "description": "Mô tả",
        "preview": "Xem trước bài đăng",
        "delete": "Xóa",
        "delete_success": "Đã xóa kỷ niệm.",
        "delete_failed": "Xóa thất bại:",
        "class": "Lớp",
        "api_hint": "Nếu vẫn báo Method Not Allowed, backend chưa có route POST /api/tv3/memories hoặc chưa restart server.",
    },
    "en": {
        "title": "📸 Post Class Memories",
        "subtitle": "Teachers can share learning activities and memorable photos for their assigned classes.",
        "tab_post": "📝 New Memory",
        "tab_list": "📚 Posted Memories",
        "select_class": "Select class (*)",
        "input_title": "Memory title / Topic",
        "input_desc": "Description (*)",
        "placeholder_desc": "Example: Today the students enjoyed a fun group activity...",
        "input_image": "Choose memory image (*)",
        "btn_submit": "🚀 Post Memory",
        "btn_refresh": "🔄 Refresh",
        "warn_login": "Please log in again.",
        "warn_missing": "Please select class, enter description, and choose an image.",
        "warn_no_class": "No assigned classes found.",
        "uploading": "Uploading image to Cloudinary...",
        "posting": "Saving memory...",
        "success": "Memory posted successfully!",
        "failed": "Failed to post memory:",
        "empty": "No memories yet.",
        "teacher": "Teacher",
        "posted_at": "Posted at",
        "description": "Description",
        "preview": "Preview",
        "delete": "Delete",
        "delete_success": "Memory deleted.",
        "delete_failed": "Delete failed:",
        "class": "Class",
        "api_hint": "If Method Not Allowed still appears, backend does not have POST /api/tv3/memories or server was not restarted.",
    },
}

L = LABELS.get(lang, LABELS["vi"])


# ================= HELPERS =================
def get_headers(json_type=True):
    headers = {
        "Authorization": f"Bearer {token}",
        "teacher-id": str(user_id),
    }

    if json_type:
        headers["Content-Type"] = "application/json"

    return headers


def get_teacher_name():
    return (
        user_info.get("full_name")
        or user_info.get("name")
        or st.session_state.get("full_name")
        or st.session_state.get("username")
        or L["teacher"]
    )


def normalize_text(value):
    return str(value or "").strip().lower()


def get_class_id(cls):
    return str(cls.get("id") or cls.get("_id") or "")


def get_class_name(cls):
    return (
        cls.get("class_name")
        or cls.get("name")
        or cls.get("title")
        or f"Lớp {get_class_id(cls)[-4:]}"
    )


def get_class_subject(cls):
    return cls.get("subject") or cls.get("course_name") or cls.get("level") or ""


def class_label(cls):
    name = get_class_name(cls)
    subject = get_class_subject(cls)
    status = cls.get("status", "")

    parts = [name]

    if subject:
        parts.append(subject)

    if status:
        parts.append(status)

    return " - ".join(parts)


def class_belongs_to_teacher(cls):
    """
    Lọc lớp giáo viên đang dạy.
    Hỗ trợ nhiều kiểu dữ liệu vì mỗi dự án có thể lưu teacher khác nhau:
    - teacher_id
    - teacher_ids
    - teacher
    - teacher_name
    - teachers: list
    """
    if role in ["admin", "operator"]:
        return True

    current_teacher_id = str(user_id)
    current_teacher_name = normalize_text(get_teacher_name())

    # Các field ID đơn
    id_fields = [
        "teacher_id",
        "teacher_ref",
        "main_teacher_id",
        "instructor_id",
    ]

    for field in id_fields:
        if str(cls.get(field, "")) == current_teacher_id:
            return True

    # Field teacher có thể là string hoặc dict
    teacher_value = cls.get("teacher")

    if isinstance(teacher_value, dict):
        if str(teacher_value.get("id") or teacher_value.get("_id") or "") == current_teacher_id:
            return True

        teacher_name = normalize_text(
            teacher_value.get("full_name")
            or teacher_value.get("name")
            or teacher_value.get("email")
        )

        if teacher_name and teacher_name == current_teacher_name:
            return True

    elif teacher_value:
        if str(teacher_value) == current_teacher_id:
            return True

    # Các field ID dạng list
    list_fields = [
        "teacher_ids",
        "teacher_id_list",
        "teachers",
        "teacher_refs",
    ]

    for field in list_fields:
        values = cls.get(field, [])

        if not isinstance(values, list):
            continue

        for item in values:
            if isinstance(item, dict):
                item_id = str(item.get("id") or item.get("_id") or "")
                item_name = normalize_text(
                    item.get("full_name")
                    or item.get("name")
                    or item.get("email")
                )

                if item_id == current_teacher_id:
                    return True

                if item_name and item_name == current_teacher_name:
                    return True
            else:
                if str(item) == current_teacher_id:
                    return True

    # Các field tên giáo viên
    name_fields = [
        "teacher_name",
        "teacher_full_name",
        "instructor_name",
    ]

    for field in name_fields:
        teacher_name = normalize_text(cls.get(field))
        if teacher_name and teacher_name == current_teacher_name:
            return True

    return False


@st.cache_data(ttl=30)
def fetch_all_classes(api_tv1, auth_token):
    try:
        headers = {
            "Authorization": f"Bearer {auth_token}",
        }

        res = requests.get(
            f"{api_tv1}/classes",
            headers=headers,
            timeout=20,
        )

        if res.status_code == 200:
            data = res.json()

            if isinstance(data, list):
                return data

            if isinstance(data, dict):
                return data.get("items", data.get("data", []))

        return []

    except Exception:
        return []


def upload_image_to_backend(uploaded_file):
    try:
        files = {
            "file": (
                uploaded_file.name,
                uploaded_file.getvalue(),
                uploaded_file.type,
            )
        }

        res = requests.post(
            f"{API_TV3}/upload_image",
            files=files,
            timeout=60,
        )

        if res.status_code == 200:
            data = res.json()
            return {
                "image_url": data.get("image_url", ""),
                "image_public_id": data.get("image_public_id") or data.get("public_id", ""),
            }

        return {
            "image_url": "",
            "image_public_id": "",
            "error": res.text,
        }

    except Exception as e:
        return {
            "image_url": "",
            "image_public_id": "",
            "error": str(e),
        }


def create_memory(payload):
    try:
        res = requests.post(
            f"{API_TV3}/memories",
            json=payload,
            headers=get_headers(json_type=True),
            timeout=30,
        )

        return res

    except Exception as e:
        class DummyResponse:
            status_code = 500
            text = str(e)

            def json(self):
                return {"detail": str(e)}

        return DummyResponse()


def fetch_memories():
    try:
        res = requests.get(
            f"{API_TV3}/memories",
            headers=get_headers(json_type=False),
            timeout=20,
        )

        if res.status_code == 200:
            data = res.json()

            if isinstance(data, list):
                return data

            if isinstance(data, dict):
                return data.get("items", data.get("data", []))

        return []

    except Exception:
        return []


def delete_memory(memory_id):
    try:
        res = requests.delete(
            f"{API_TV3}/memories/{memory_id}",
            headers=get_headers(json_type=False),
            timeout=20,
        )

        return res

    except Exception as e:
        class DummyResponse:
            status_code = 500
            text = str(e)

            def json(self):
                return {"detail": str(e)}

        return DummyResponse()


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


def format_datetime(value):
    if not value:
        return "---"

    value = str(value)

    try:
        dt = datetime.fromisoformat(value.replace("Z", ""))
        return dt.strftime("%d/%m/%Y %H:%M")
    except Exception:
        return value[:16].replace("T", " ")


# ================= MAIN UI =================
st.title(L["title"])
st.caption(L["subtitle"])

if not user_id or not token:
    st.warning(L["warn_login"])
    st.stop()

st.markdown(f"<div class='memory-note'>{L['api_hint']}</div>", unsafe_allow_html=True)

if st.button(L["btn_refresh"]):
    st.cache_data.clear()
    st.rerun()


all_classes = fetch_all_classes(API_TV1, token)
teacher_classes = [cls for cls in all_classes if class_belongs_to_teacher(cls)]

class_options = {
    get_class_id(cls): cls
    for cls in teacher_classes
    if get_class_id(cls)
}

tab_post, tab_list = st.tabs([L["tab_post"], L["tab_list"]])


# ================= TAB POST =================
with tab_post:
    if not class_options:
        st.warning(L["warn_no_class"])
        st.stop()

    with st.container(border=True):
        st.markdown("### " + L["tab_post"])

        selected_class_id = st.selectbox(
            L["select_class"],
            options=list(class_options.keys()),
            format_func=lambda cid: class_label(class_options[cid]),
        )

        selected_class = class_options[selected_class_id]

        memory_title = st.text_input(L["input_title"])

        description = st.text_area(
            L["input_desc"],
            placeholder=L["placeholder_desc"],
            height=160,
        )

        uploaded_image = st.file_uploader(
            L["input_image"],
            type=["png", "jpg", "jpeg", "webp"],
        )

        if uploaded_image:
            st.markdown(f"#### {L['preview']}")
            st.image(uploaded_image, use_container_width=True)
            st.markdown(
                f"<div class='memory-desc'>{description or L['description']}</div>",
                unsafe_allow_html=True,
            )

        if st.button(L["btn_submit"], type="primary", use_container_width=True):
            if not selected_class_id or not description.strip() or not uploaded_image:
                st.warning(L["warn_missing"])
            else:
                with st.spinner(L["uploading"]):
                    upload_data = upload_image_to_backend(uploaded_image)

                image_url = upload_data.get("image_url", "")
                image_public_id = upload_data.get("image_public_id", "")

                if not image_url:
                    st.error(f"{L['failed']} {upload_data.get('error', '')}")
                    st.stop()

                payload = {
                    "title": memory_title.strip() or "Kỷ niệm lớp học",
                    "description": description.strip(),

                    "media_url": image_url,
                    "image_url": image_url,
                    "image_public_id": image_public_id,

                    "teacher_id": str(user_id),
                    "teacher_name": get_teacher_name(),

                    "class_id": str(selected_class_id),
                    "class_name": get_class_name(selected_class),
                    "class_subject": get_class_subject(selected_class),

                    "type": "image",
                    "likes": 0,
                    "created_at": datetime.utcnow().isoformat(),
                    "status": "published",
                }

                with st.spinner(L["posting"]):
                    res = create_memory(payload)

                if res.status_code in [200, 201]:
                    st.success(L["success"])
                    st.balloons()
                    time.sleep(1)
                    st.cache_data.clear()
                    st.rerun()
                else:
                    try:
                        detail = res.json().get("detail", res.text)
                    except Exception:
                        detail = res.text

                    st.error(f"{L['failed']} {detail}")


# ================= TAB LIST =================
with tab_list:
    memories = fetch_memories()

    # Giáo viên chỉ xem kỷ niệm của mình, admin/operator xem tất cả
    if role == "teacher":
        memories = [
            m for m in memories
            if str(m.get("teacher_id", "")) == str(user_id)
        ]

    if not memories:
        st.info(L["empty"])
    else:
        for item in memories:
            memory_id = str(item.get("id") or item.get("_id") or "")
            teacher_name = item.get("teacher_name") or L["teacher"]
            created_at = format_datetime(item.get("created_at"))
            desc = item.get("description") or ""
            media_url = item.get("media_url") or item.get("image_url") or ""

            with st.container(border=True):
                col_img, col_info = st.columns([1.3, 2])

                with col_img:
                    st.image(get_valid_image_url(media_url), use_container_width=True)

                with col_info:
                    st.markdown(f"### {item.get('title', 'Kỷ niệm lớp học')}")
                    st.caption(f"👨‍🏫 {teacher_name} | 🕒 {created_at}")
                    st.caption(f"🏫 {L['class']}: {item.get('class_name', '---')}")

                    if item.get("class_subject"):
                        st.caption(f"📚 {item.get('class_subject')}")

                    st.markdown(desc)

                    if memory_id:
                        if st.button(
                            L["delete"],
                            key=f"delete_memory_{memory_id}",
                            use_container_width=True,
                        ):
                            res = delete_memory(memory_id)

                            if res.status_code == 200:
                                st.success(L["delete_success"])
                                time.sleep(0.5)
                                st.cache_data.clear()
                                st.rerun()
                            else:
                                st.error(f"{L['delete_failed']} {res.text}")