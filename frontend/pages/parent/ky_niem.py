import streamlit as st
from utils.role_guard import require_role

require_role(["parent"])

st.set_page_config(page_title="Góc Kỷ Niệm", page_icon="📸", layout="centered")

st.title(" Góc Kỷ Niệm Của Bé")
st.write("Cập nhật những khoảnh khắc sinh hoạt đáng yêu của bé tại trung tâm iKids.")
st.divider()

# Khung ảnh 1
with st.container(border=True):
    st.write(" **Cô giáo Lan Anh** đã đăng một ảnh mới - *Hôm qua*")
    
    # Dùng ảnh mẫu thay cho ảnh thật
    img_url_1 = "https://images.unsplash.com/photo-1577896851231-70ef18881754?w=600&q=80"
    st.image(img_url_1, use_container_width=True, caption="Lớp học thực hành môn Khoa học")
    
    st.write("Các chiến binh nhí hôm nay làm thí nghiệm núi lửa phun trào cực kỳ tập trung luôn nha! 🥰")
    
    col1, col2, col3 = st.columns([1, 1, 3])
    with col1:
        st.button("❤️ Thả tim (15)", key="like_1")
    with col2:
        st.download_button("📥 Tải ảnh", data="dummy_image_data", file_name="ikids_khoahoc.jpg", mime="image/jpeg", key="dl_1")
    with col3:
        st.text_input("Bình luận...", key="cmt_1", label_visibility="collapsed", placeholder="Viết bình luận...")

# Khung ảnh 2
with st.container(border=True):
    st.write("👨‍🏫 **Thầy Quốc Bảo** đã đăng một ảnh mới - *Tuần trước*")
    
    img_url_2 = "https://images.unsplash.com/photo-1509062522246-3755977927d7?w=600&q=80"
    st.image(img_url_2, use_container_width=True, caption="Lễ trao giải Rung Chuông Vàng")
    
    st.write("Buổi lễ vinh danh các bạn nhỏ xuất sắc nhất tháng 5! 🏆")
    
    col1, col2, col3 = st.columns([1, 1, 3])
    with col1:
        st.button("❤️ Thả tim (32)", key="like_2")
    with col2:
        st.download_button("📥 Tải ảnh", data="dummy_image_data", file_name="ikids_rungchuongvang.jpg", mime="image/jpeg", key="dl_2")
    with col3:
        st.text_input("Bình luận...", key="cmt_2", label_visibility="collapsed", placeholder="Viết bình luận...")