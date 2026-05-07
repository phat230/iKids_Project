import streamlit as st

def render_profile_page():
    st.set_page_config(layout="wide")
    st.title("👤 Quản Lý Tài Khoản")
    st.markdown("Cập nhật thông tin cá nhân, ảnh đại diện và các liên kết mạng xã hội của bạn để kết nối tốt hơn với học viên và đồng nghiệp.")

    st.divider()

    # --- CHIA LAYOUT 2 CỘT CHO THẨM MỸ ---
    col_avatar, col_info = st.columns([1, 2.5], gap="large")

    # ==========================================
    # CỘT TRÁI: QUẢN LÝ ẢNH ĐẠI DIỆN
    # ==========================================
    with col_avatar:
        st.markdown("### 🖼️ Ảnh đại diện")
        with st.container(border=True):
            st.image("https://api.dicebear.com/7.x/avataaars/svg?seed=MinhTran&backgroundColor=e2e8f0", use_column_width=True)
            st.markdown("<br>", unsafe_allow_html=True)
            uploaded_file = st.file_uploader("Tải ảnh mới lên", type=['png', 'jpg', 'jpeg'], help="Giới hạn 200MB mỗi file")
            if uploaded_file is not None:
                st.success("✅ Đã tải ảnh lên! Hãy bấm Lưu ở bên phải.")

    # ==========================================
    # CỘT PHẢI: FORM THÔNG TIN CHI TIẾT
    # ==========================================
    with col_info:
        st.markdown("### 📝 Thông tin chi tiết")
        with st.form("profile_update_form", border=True):
            st.markdown("##### 📌 Thông tin cơ bản")
            c1, c2 = st.columns(2)
            with c1:
                name = st.text_input("Họ và Tên (*)", value="Minh Tran")
            with c2:
                phone = st.text_input("Số điện thoại", placeholder="VD: 0901 234 567")

            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown("##### 🌐 Liên kết Mạng xã hội")
            c3, c4 = st.columns(2)
            with c3:
                fb = st.text_input("Link Facebook", placeholder="https://facebook.com/your_profile")
            with c4:
                github = st.text_input("Link Github (Nếu có)", placeholder="https://github.com/your_username")

            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown("##### 🎨 Sở thích & Giới thiệu")
            hobbies = st.text_area("Sở thích cá nhân / Châm ngôn giảng dạy",
                                   placeholder="Ví dụ: Thích đọc sách công nghệ, đi du lịch, và truyền cảm hứng cho trẻ em...",
                                   height=100)

            st.markdown("<br>", unsafe_allow_html=True)
            submitted = st.form_submit_button("💾 LƯU TẤT CẢ THAY ĐỔI", use_container_width=True, type="primary")

            if submitted:
                if not name.strip():
                    st.error("⚠️ Họ và Tên không được để trống!")
                else:
                    st.success("🎉 Đã cập nhật thông tin hồ sơ thành công!")

if __name__ == "__main__":
    render_profile_page()