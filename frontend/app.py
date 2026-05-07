import streamlit as st
from utils.auth_state import logout_user

# 1. CẤU HÌNH TRANG
st.set_page_config(
    page_title="iKids Portal - Hệ thống học tập thông minh",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 2. ĐỊNH NGHĨA CÁC TRANG CƠ BẢN
home_page = st.Page("home.py", title="Trang Chủ", icon="🏠", default=True)
login_page = st.Page("auth/login.py", title="Đăng Nhập", icon="🔐")
register_page = st.Page("auth/register.py", title="Đăng Ký", icon="📝")
forgot_page = st.Page("auth/forgot_password.py", title="Quên Mật Khẩu", icon="🔑")

# 3. XỬ LÝ ĐIỀU HƯỚNG
if "token" not in st.session_state:
    # --- CHƯA ĐĂNG NHẬP ---
    pg = st.navigation({
        "Hệ thống": [home_page],
        "Tài khoản": [login_page, register_page, forgot_page]
    })
    
    # CSS ẩn "Quên Mật Khẩu"
    st.markdown("""
        <style>
            [data-testid="stSidebarNav"] ul li:has(span:contains("Quên Mật Khẩu")) {
                display: none;
            }
        </style>
    """, unsafe_allow_html=True)
    pg.run()

else:
    # --- ĐÃ ĐĂNG NHẬP ---
    role = st.session_state.get("role")
    user = st.session_state.get("user_info", {"name": "Thành viên iKids"})
    
    menu_pages = [home_page] 
    
    # --- PHÂN QUYỀN MENU ---
    
    # 1. Role: Admin (QUAN TRỌNG - Bổ sung mới)
    if role == "admin":
        menu_pages.extend([
            st.Page("pages/admin/dashboard.py", title="Bảng Điều Khiển Admin", icon="🛡️"),
            st.Page("pages/admin/quan_ly_nhan_su.py", title="Quản Lý Nhân Sự", icon="👥"),
            st.Page("pages/student/trang_ca_nhan.py", title="Cài Đặt Hệ Thống", icon="⚙️")
        ])

    # 2. Role: Operator (Nhân viên vận hành - Bổ sung mới)
    elif role == "operator":
        menu_pages.extend([
            st.Page("pages/operator/dashboard.py", title="Bảng Vận Hành", icon="🕹️"),
            st.Page("pages/operator/xep_lich.py", title="Xếp Lịch Dạy", icon="📅"),
            st.Page("pages/operator/quan_ly_lop.py", title="Quản Lý Lớp Học", icon="🏫"),
            st.Page("pages/student/trang_ca_nhan.py", title="Trang Cá Nhân", icon="👤")
        ])

    # 3. Role: Teacher
    elif role == "teacher":
        menu_pages.extend([
            st.Page("pages/teacher/dashboard.py", title="Bảng Tin Giáo Viên", icon="👨‍🏫"),
            st.Page("pages/teacher/nhat_ky.py", title="Nhật Ký & Điểm Danh", icon="📔"),
            st.Page("pages/teacher/tao_quiz.py", title="Tạo Bài Tập AI", icon="🤖"),
            st.Page("pages/student/trang_ca_nhan.py", title="Trang Cá Nhân", icon="⚙️")
        ])

    # 4. Role: Student
    elif role == "student":
        menu_pages.extend([
            st.Page("pages/student/dashboard.py", title="Góc Học Tập", icon="🚀"),
            st.Page("pages/student/lich_hoc.py", title="Lịch Học", icon="📅"),
            st.Page("pages/student/trang_ca_nhan.py", title="Trang Cá Nhân", icon="🧑‍🎤")
        ])

    # 5. Role: Parent
    elif role == "parent":
        menu_pages.extend([
            st.Page("pages/parent/quan_ly_con.py", title="Quản Lý Con Em", icon="👨‍👩‍👦"),
            st.Page("pages/parent/ket_qua.py", title="Báo Cáo Học Tập", icon="📊"),
            st.Page("pages/student/trang_ca_nhan.py", title="Cài Đặt Tài Khoản", icon="⚙️")
        ])

    # Chạy Navigation
    pg = st.navigation(menu_pages)
    
    # Hiển thị Sidebar
    with st.sidebar:
        st.markdown(f"### 👤 {user['name']}")
        avatar_url = user.get("avatar_url")
        if avatar_url:
            st.image(f"http://localhost:8000/{avatar_url}", width=100)
        else:
            st.markdown("![Avatar](https://www.w3schools.com/howto/img_avatar.png)") # Ảnh mặc định
            
        st.caption(f"Vai trò: {role.upper()}")
        st.divider()
        if st.button("🚪 Đăng Xuất", key="logout_sidebar", use_container_width=True):
            logout_user()
            
    pg.run()