import streamlit as st
import requests

# Cấu hình API Backend
API_URL = "http://localhost:8000"
API_TV3 = "http://localhost:8000/api/tv3"

st.set_page_config(page_title="Đăng Ký Lớp Học", page_icon="📑")
st.title("📑 Đăng Ký Lớp Học Cho Con")
st.write("Dưới đây là danh sách các lớp học đang mở. Phụ huynh có thể chọn lớp phù hợp cho con em mình.")

# 1. KIỂM TRA ĐĂNG NHẬP
parent_id = st.session_state.get("user_id")
token = st.session_state.get("access_token")

if not parent_id or not token:
    st.error("🔒 Vui lòng đăng nhập với tài khoản Phụ huynh để đăng ký lớp.")
    st.stop()

headers = {"Authorization": f"Bearer {token}", "parent-id": str(parent_id)}

# 2. LẤY DANH SÁCH CÁC CON CỦA PHỤ HUYNH
@st.cache_data(ttl=30)
def get_my_children():
    try:
        res = requests.get(f"{API_TV3}/parent/my-children", headers=headers)
        return res.json() if res.status_code == 200 else []
    except:
        return []

children = get_my_children()

if not children:
    st.warning("⚠️ Bạn chưa có hồ sơ học sinh nào. Vui lòng sang trang 'Quản Lý Con Em' để tạo tài khoản cho bé trước khi đăng ký lớp!")
    st.stop()

# Tạo Dictionary để đưa vào ô Selectbox (Ví dụ: {"id_1": "Bé Mít", "id_2": "Bé Xoài"})
child_options = {c["id"]: c["name"] for c in children}

st.divider()

# 3. GỌI API LẤY DANH SÁCH LỚP PUBLIC
try:
    res = requests.get(f"{API_URL}/classes/public")
    public_classes = res.json() if res.status_code == 200 else []
except Exception as e:
    st.error(f"⚠️ Không thể kết nối đến máy chủ Backend: {e}")
    public_classes = []

# 4. HIỂN THỊ DANH SÁCH LỚP HỌC
if not public_classes:
    st.info("💡 Hiện tại hệ thống chưa có lớp học nào đang mở đăng ký.")
else:
    for cls in public_classes:
        with st.container(border=True):
            col1, col2 = st.columns([3, 2])
            
            class_id = cls.get('id', cls.get('_id', ''))
            
            with col1:
                st.markdown(f"#### 🏫 {cls.get('class_name', 'Tên lớp chưa rõ')}")
                st.write(f"**📚 Môn học:** {cls.get('subject', 'Chưa cập nhật')}")
                st.caption(f"👨‍🏫 Giáo viên phụ trách: {cls.get('teacher_name', 'Đang xếp')}")
            
            with col2:
                # Ô TÙY CHỌN BÉ ĐỂ ĐĂNG KÝ
                selected_child_id = st.selectbox(
                    "👶 Chọn bé tham gia lớp này:",
                    options=list(child_options.keys()),
                    format_func=lambda x: child_options[x],
                    key=f"child_select_{class_id}"
                )
                
                if st.button("🚀 Đăng ký học ngay", key=f"btn_{class_id}", type="primary", use_container_width=True):
                    # Kiểm tra xem bé đã có trong lớp chưa (Tránh đăng ký trùng)
                    current_students = cls.get("student_ids", [])
                    
                    if selected_child_id in current_students:
                        st.warning(f"Bé **{child_options[selected_child_id]}** đã được đăng ký lớp này từ trước rồi!")
                    else:
                        payload = {"class_id": class_id, "student_id": selected_child_id}
                        try:
                            # Gọi API đăng ký
                            register_res = requests.post(f"{API_URL}/classes/register", json=payload)
                            
                            if register_res.status_code in [200, 201]:
                                st.success(f"🎉 Đã đăng ký thành công bé **{child_options[selected_child_id]}** vào lớp {cls.get('class_name')}!")
                                st.balloons()
                            else:
                                st.error("❌ Đăng ký thất bại. Lớp học có thể đã đầy hoặc lỗi hệ thống.")
                        except Exception as e:
                            st.error("❌ Lỗi kết nối khi gửi yêu cầu đăng ký.")