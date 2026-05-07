import streamlit as st
from utils.auth_state import logout_user

# 1. CẤU HÌNH TRANG (Chỉ khai báo duy nhất tại đây)
st.set_page_config(
    page_title="iKids Portal - Hệ thống học tập thông minh",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 2. ĐỊNH NGHĨA CÁC TRANG (Dẫn link tới file vật lý)
# Lưu ý: Đảm bảo các file này tồn tại trong thư mục tương ứng
home_page = st.Page("home.py", title="Trang Chủ", icon="🏠", default=True)
login_page = st.Page("auth/login.py", title="Đăng Nhập", icon="🔐")
register_page = st.Page("auth/register.py", title="Đăng Ký", icon="📝")
forgot_page = st.Page("auth/forgot_password.py", title="Quên Mật Khẩu", icon="🔑")

# 3. XỬ LÝ ĐIỀU HƯỚNG THEO TRẠNG THÁI ĐĂNG NHẬP
if "token" not in st.session_state:
    # --- GIAO DIỆN KHI CHƯA ĐĂNG NHẬP ---
    pg = st.navigation({
        "Hệ thống": [home_page],
        "Tài khoản": [login_page, register_page, forgot_page]
    })
    
    # CSS để ẩn mục "Quên Mật Khẩu" khỏi sidebar nhưng vẫn cho phép switch_page hoạt động
    st.markdown("""
        <style>
            /* Tìm mục menu có nhãn Quên Mật Khẩu và ẩn nó đi */
            [data-testid="stSidebarNav"] ul li:has(span:contains("Quên Mật Khẩu")) {
                display: none;
            }
        </style>
    """, unsafe_allow_html=True)
    pg.run()

else:
    # --- GIAO DIỆN KHI ĐÃ ĐĂNG NHẬP ---
    role = st.session_state.get("role")
    user = st.session_state.get("user_info", {"name": "Thành viên iKids"})
    
    # Khởi tạo danh sách menu dựa trên vai trò
    menu_pages = [home_page] 
    
    # Phân quyền menu cho Học sinh
    if role == "student":
        menu_pages.extend([
            st.Page("pages/student/dashboard.py", title="Bảng Điều Khiển", icon="🚀"),
            st.Page("pages/student/lich_hoc.py", title="Lịch Học Của Tôi", icon="📅"),
            st.Page("pages/student/quiz.py", title="Bài Tập AI", icon="📝"),
            st.Page("pages/student/ket_qua.py", title="Bảng Điểm", icon="📈"),
            st.Page("pages/student/cua_hang.py", title="Cửa Hàng Đổi Xu", icon="🎁"),
            st.Page("pages/student/ky_niem.py", title="Góc Kỷ Niệm", icon="📸"),
            st.Page("pages/student/trang_ca_nhan.py", title="Trang Cá Nhân", icon="🧑‍🎤")
        ])
        
    # Phân quyền menu cho Phụ huynh
    elif role == "parent":
        menu_pages.extend([
            st.Page("pages/parent/quan_ly_con.py", title="Quản Lý Con Em", icon="👨‍👩‍👦"),
            st.Page("pages/parent/nap_tien.py", title="Nạp Tiền Vào Ví", icon="💳"),
            st.Page("pages/student/cua_hang.py", title="Cửa Hàng iKids", icon="🛒"),
            st.Page("pages/parent/ket_qua.py", title="Báo Cáo Học Tập", icon="📊"),
            st.Page("pages/parent/ky_niem.py", title="Góc Kỷ Niệm", icon="📸"),
            st.Page("pages/parent/lien_he.py", title="Liên Hệ & Yêu Cầu", icon="📞"),
            st.Page("pages/student/trang_ca_nhan.py", title="Cài Đặt Tài Khoản", icon="⚙️")
        ])

    # Phân quyền menu cho Giáo viên
    elif role == "teacher":
        menu_pages.extend([
            st.Page("pages/teacher/danh_sach_lop.py", title="Quản Lý Lớp Học", icon="🏫"),
            st.Page("pages/teacher/cham_diem.py", title="Chấm Điểm & Nhận Xét", icon="✍️"),
            st.Page("pages/teacher/dang_ky_niem.py", title="Đăng Kỷ Niệm", icon="📸"),
            st.Page("pages/student/trang_ca_nhan.py", title="Trang Cá Nhân", icon="⚙️")
        ])

    # Khởi tạo Navigation sau khi đã lọc menu theo role
    pg = st.navigation(menu_pages)
    
    # Hiển thị thông tin người dùng ở Sidebar
    with st.sidebar:
        st.markdown("### 📝 Thông tin cá nhân")
        
        # Hiển thị ảnh đại diện thật từ Server nếu có
        avatar_url = user.get("avatar_url")
        if avatar_url:
            # Gọi qua link server Backend (mặc định localhost:8000)
            st.image(f"http://localhost:8000/{avatar_url}", width=100)
        else:
            st.info("Chưa có ảnh đại diện")
            
        st.markdown(f"Chào bạn, **{user['name']}**!")
        st.caption(f"Quyền hạn: {role.upper()}")
        
        st.divider()
        
        # Nút đăng xuất
        if st.button("🚪 Đăng Xuất", key="logout_sidebar", use_container_width=True):
            logout_user()
            
    pg.run()