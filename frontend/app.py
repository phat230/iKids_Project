import streamlit as st
from utils.auth_state import logout_user

# 1. CẤU HÌNH TRANG CHUẨN IKIDS
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

# TRANG THÔNG BÁO DÙNG CHUNG (Mới thêm)
notification_page = st.Page("pages/shared/thong_bao.py", title="Hộp Thư & Thông Báo", icon="🔔")

# 3. XỬ LÝ ĐIỀU HƯỚNG
if "token" not in st.session_state or st.session_state.token is None:
    # --- GIAO DIỆN KHI CHƯA ĐĂNG NHẬP ---
    pg = st.navigation({
        "Hệ thống": [home_page],
        "Tài khoản": [login_page, register_page, forgot_page]
    })
    
    # CSS ẩn trang Quên mật khẩu khỏi menu chính
    st.markdown("""
        <style>
            [data-testid="stSidebarNav"] ul li:has(span:contains("Quên Mật Khẩu")) {
                display: none;
            }
        </style>
    """, unsafe_allow_html=True)
    pg.run()

else:
    # --- GIAO DIỆN KHI ĐÃ ĐĂNG NHẬP ---
    role = st.session_state.get("role", "").lower()
    user = st.session_state.get("user_info", {})
    
    # Mọi User khi đăng nhập đều có trang Home và trang Thông báo
    menu_pages = [home_page, notification_page] 
    
    # --- PHÂN QUYỀN MENU CHI TIẾT ---
    
    # 1. Role: Admin
    if role == "admin":
        menu_pages.extend([
            st.Page("pages/admin/dashboard.py", title="Bảng Điều Khiển Admin", icon="🛡️"),
            st.Page("pages/admin/quan_ly_nhan_su.py", title="Quản Lý Nhân Sự", icon="👥"),
            st.Page("pages/student/trang_ca_nhan.py", title="Cài Đặt Hệ Thống", icon="⚙️")
        ])

    # 2. Role: Operator (Nhân viên vận hành)
    elif role == "operator":
        menu_pages.extend([
            st.Page("pages/operator/dashboard.py", title="Bảng Vận Hành", icon="🕹️"),
            st.Page("pages/operator/xep_lich.py", title="Xếp Lịch Dạy", icon="📅"),
            st.Page("pages/operator/quan_ly_lop.py", title="Quản Lý Lớp Học", icon="🏫"), 
            st.Page("pages/student/trang_ca_nhan.py", title="Trang Cá Nhân", icon="👤")
        ])

    # 3. Role: Teacher (Giáo viên)
    elif role == "teacher":
        menu_pages.extend([
            st.Page("pages/teacher/dashboard.py", title="Bảng Tin Giáo Viên", icon="👨‍🏫"),
            st.Page("pages/teacher/nhat_ky.py", title="Nhật Ký & Điểm Danh", icon="📔"),
            st.Page("pages/teacher/tao_quiz.py", title="Quản Lý Bài Tập AI", icon="🤖"),
            st.Page("pages/teacher/kho_hoc_lieu.py", title="Kho Học Liệu", icon="📚"),
            st.Page("pages/teacher/giao_bai.py", title="Giao Bài Tập", icon="📤"),
            st.Page("pages/student/trang_ca_nhan.py", title="Trang Cá Nhân", icon="⚙️")        
        ])

    # 4. Role: Student (Học sinh)
    elif role == "student":
        menu_pages.extend([
            st.Page("pages/student/dashboard.py", title="Góc Học Tập", icon="🚀"),
            st.Page("pages/student/lich_hoc.py", title="Lịch Học", icon="📅"),
            st.Page("pages/student/quiz.py", title="Trạm Quiz AI", icon="📝"),
            st.Page("pages/student/cua_hang.py", title="Cửa Hàng iKids", icon="🛒"),
            st.Page("pages/student/ky_niem.py", title="Góc Kỷ Niệm", icon="📸"),
            st.Page("pages/student/trang_ca_nhan.py", title="Trang Cá Nhân", icon="🧑‍🎤"),
            st.Page("pages/student/video.py", title="Rạp Chiếu Video AI", icon="📺")
        ])

    # 5. Role: Parent (Phụ huynh)
    elif role == "parent":
        menu_pages.extend([
            st.Page("pages/parent/quan_ly_con.py", title="Quản Lý Con Em", icon="👨‍👩‍👦"),
            st.Page("pages/parent/chon_lop.py", title="Đăng Ký Lớp Học", icon="📑"), 
            st.Page("pages/parent/ket_qua.py", title="Báo Cáo Học Tập", icon="📊"),
            st.Page("pages/parent/nap_tien.py", title="Nạp Tiền & Ví", icon="💳"),
            st.Page("pages/parent/cua_hang.py", title="Mua Đồ Cho Con", icon="🛒"),
            st.Page("pages/parent/ky_niem.py", title="Kỷ Niệm Của Con", icon="📸"),
            st.Page("pages/parent/lien_he.py", title="Liên Hệ & Xin Nghỉ", icon="📞"),
            st.Page("pages/student/trang_ca_nhan.py", title="Cài Đặt Tài Khoản", icon="⚙️")
        ])

    # Khởi tạo Navigation
    pg = st.navigation(menu_pages)
    
    # Hiển thị thông tin định danh ở Sidebar
    with st.sidebar:
        st.write(f"### Chào, {user.get('full_name', 'Thành viên')}! 👋")
        
        # Xử lý Avatar chuyên nghiệp
        avatar_url = user.get("avatar_url")
        if avatar_url:
            st.image(f"http://localhost:8000{avatar_url}", width=100)
        else:
            st.image("https://www.w3schools.com/howto/img_avatar.png", width=100)
            
        st.caption(f"Quyền truy cập: {role.upper()}")
        
        # Hiển thị thông báo chấm đỏ nếu có tin nhắn mới (Tùy chọn thêm)
        st.divider()
        
        if st.button("🚪 Đăng Xuất", key="logout_sidebar", use_container_width=True, type="primary"):
            logout_user()
            st.rerun()
            
    pg.run()