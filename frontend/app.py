import streamlit as st
from utils.auth_state import login_user, register_user, logout_user

# ---------------- LƯU Ý ----------------
# Nếu file này báo lỗi ở st.navigation, hãy mở Terminal chạy lệnh:
# pip install --upgrade streamlit
# ---------------------------------------

# Nếu chưa có Token -> Hiển thị màn hình Đăng Nhập / Đăng Ký
if "token" not in st.session_state:
    st.set_page_config(page_title="iKids Portal", layout="centered", page_icon="🚀")
    
    st.markdown("<h1 style='text-align: center; color: #1E3A8A;'>Hệ Thống Giáo Dục iKids</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: gray;'>Vui lòng đăng nhập để tiếp tục</p>", unsafe_allow_html=True)
    
    tab1, tab2 = st.tabs(["🔐 Đăng Nhập", "📝 Đăng Ký"])
    
    with tab1:
        with st.form("login_form"):
            email = st.text_input("Email")
            password = st.text_input("Mật khẩu", type="password")
            submit_login = st.form_submit_button("Đăng Nhập", use_container_width=True)
            
            if submit_login:
                success, msg = login_user(email, password)
                if success:
                    st.success(msg)
                    st.rerun()
                else:
                    st.error(msg)
                    
    with tab2:
        with st.form("register_form"):
            reg_name = st.text_input("Họ và Tên")
            reg_email = st.text_input("Email")
            reg_password = st.text_input("Mật khẩu", type="password")
            role_options = {"Học sinh": "student", "Phụ huynh": "parent"}
            selected_role_label = st.selectbox("Vai trò của bạn", list(role_options.keys()))
            submit_reg = st.form_submit_button("Tạo Tài Khoản", use_container_width=True)
            
            if submit_reg:
                reg_role_value = role_options[selected_role_label]
                success, msg = register_user(reg_name, reg_email, reg_password, reg_role_value)
                if success:
                    st.success(msg)
                else:
                    st.error(msg)

# Nếu ĐÃ ĐĂNG NHẬP -> Kích hoạt Điều Hướng Động (Dynamic Navigation)
else:
    role = st.session_state["role"]
    user = st.session_state["user_info"]

    # 1. Khai báo Trang Chủ (Ai cũng có)
    # Lưu ý: st.Page giúp Streamlit biết file nào tương ứng với tên gì trên Menu
    home_page = st.Page("home.py", title="Trang Chủ", icon="🏠", default=True)
    
    # 2. Xây dựng danh sách Menu tùy theo Role
    menu_pages = [home_page] # Mặc định add Trang Chủ vào đầu tiên
    
    if role == "student":
        # Khai báo các trang của Student (Sử dụng đúng tên file bạn đã tạo)
        menu_pages.append(st.Page("pages/student/dashboard.py", title="Bảng Điều Khiển", icon="🚀"))
        menu_pages.append(st.Page("pages/student/lich_hoc.py", title="Lịch Học Của Tôi", icon="📅"))
        menu_pages.append(st.Page("pages/student/quiz.py", title="Bài Tập AI", icon="📝"))
        menu_pages.append(st.Page("pages/student/ket_qua.py", title="Bảng Điểm", icon="📈"))
        menu_pages.append(st.Page("pages/student/cua_hang.py", title="Cửa Hàng Đổi Xu", icon="🎁"))
        menu_pages.append(st.Page("pages/student/ky_niem.py", title="Góc Kỷ Niệm", icon="📸"))
        
    elif role == "parent":
        # Khai báo các trang của Parent
        menu_pages.append(st.Page("pages/parent/ket_qua.py", title="Báo Cáo Học Tập", icon="📊"))
        menu_pages.append(st.Page("pages/parent/ky_niem.py", title="Góc Kỷ Niệm", icon="📸"))

    # 3. Nạp danh sách menu vào thanh điều hướng bên trái
    pg = st.navigation(menu_pages)
    
    # 4. Gắn thêm thông tin User và Nút Đăng Xuất ở dưới cùng thanh Sidebar
    with st.sidebar:
        st.divider()
        st.markdown(f"👤 **{user['name']}**")
        st.caption(f"Role: {role.upper()}")
        if st.button("🚪 Đăng Xuất", use_container_width=True):
            logout_user()
            
    # 5. Chạy trang hiện tại mà người dùng đang chọn
    pg.run()