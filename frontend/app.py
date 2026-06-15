# frontend/app.py
import streamlit as st
import os
import time
from utils.auth_state import logout_user
from locales import UI_LOCALES

# ================= CRITICAL 1: CẤU HÌNH TRANG LUÔN ĐỂ ĐẦU FILE =================
st.set_page_config(
    page_title="iKids Portal - Hệ thống học tập thông minh",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Khởi tạo trạng thái ngôn ngữ mặc định (Bảo vệ session state)
if "lang" not in st.session_state:
    st.session_state["lang"] = "vi"

if "view_mode" not in st.session_state:
    st.session_state["view_mode"] = "week"


# ================= 2. BỘ CHUYỂN ĐỔI NGÔN NGỮ TẠI SIDEBAR (SỬA LỖI RE-RUN) =================
with st.sidebar:
    st.markdown(f"### {UI_LOCALES[st.session_state['lang']]['sidebar_lang_title']}")
    
    # Sử dụng cơ chế an toàn để lấy index dropdown tránh crash
    current_lang_idx = 0 if st.session_state["lang"] == "vi" else 1
    
    lang_choice = st.selectbox(
        UI_LOCALES[st.session_state['lang']]['sidebar_lang_select'],
        options=["Tiếng Việt", "English"],
        index=current_lang_idx,
        key="global_lang_selector"
    )
    
    # Tạo logic kiểm tra: Chỉ cập nhật và ép tải lại khi người dùng thực sự click đổi ngôn ngữ
    new_lang_code = "vi" if lang_choice == "Tiếng Việt" else "en"
    if st.session_state["lang"] != new_lang_code:
        st.session_state["lang"] = new_lang_code
        st.rerun()

# Lấy mã ngôn ngữ hiện hành để áp dụng đồng bộ xuống dưới form
lang = st.session_state["lang"]


# ================= 3. ĐỊNH NGHĨA CÁC TRANG DỊCH THEO NGÔN NGỮ ĐÃ CHỌN =================
home_page = st.Page("home.py", title=UI_LOCALES[lang]["menu_home"], default=True)
login_page = st.Page("auth/login.py", title=UI_LOCALES[lang]["auth_tab_login"])
register_page = st.Page("auth/register.py", title=UI_LOCALES[lang]["auth_tab_register"])
forgot_page = st.Page("auth/forgot_password.py", title="Quên Mật Khẩu" if lang == "vi" else "Forgot Password")
giao_dich_tien_page = st.Page("pages/operator/giao_dich_tien.py", title="Giao Dịch Tiền" if lang == "vi" else "Finance Transactions",icon="💰")

# Nhãn phân vùng nhóm danh mục trên menu
section_system = "Hệ thống" if lang == "vi" else "System"
section_account = "Tài khoản" if lang == "vi" else "Account"


# ================= 4. XỬ LÝ ĐIỀU HƯỚNG THEO TRẠNG THÁI LOGIN =================
if "token" not in st.session_state or st.session_state.token is None:
    # --- GIAO DIỆN KHI CHƯA ĐĂNG NHẬP (DẠNG DICT PHÂN VÙNG CHUẨN) ---
    pg = st.navigation({
        section_system: [home_page],
        section_account: [login_page, register_page, forgot_page]
    })
    
    # CSS Ẩn thanh Quên mật khẩu khỏi Sidebar nếu bạn không muốn hiện link thô
    st.markdown("""
        <style>
            [data-testid="stSidebarNav"] ul li:has(span:contains("Quên Mật Khẩu")),
            [data-testid="stSidebarNav"] ul li:has(span:contains("Forgot Password")) {
                display: none !important;
            }
        </style>
    """, unsafe_allow_html=True)
    pg.run()

else:
    # --- GIAO DIỆN KHI ĐÃ ĐĂNG NHẬP ---
    role = st.session_state.get("role", "").lower()
    user = st.session_state.get("user_info", {})
    
    # Định nghĩa động trang thông báo dùng chung (Shared)
    noti_title = "Hộp Thư & Thông Báo" if lang == "vi" else "Inbox & Notifications"
    notification_page = st.Page("pages/shared/thong_bao.py", title=noti_title)
    
    # Khởi tạo danh mục trang chính mặc định sau khi đăng nhập
    menu_pages = [home_page, notification_page] 
    
    # --- PHÂN QUYỀN MENU CHI TIẾT (FIX LỖI PATH VÀ COMPONENT DI CHUYỂN) ---
    
    # 1. Quyền hạn: Admin
    if role == "admin":
        menu_pages.extend([
            st.Page("pages/admin/dashboard.py", title="Bảng Điều Khiển Admin" if lang == "vi" else "Admin Dashboard"),
            giao_dich_tien_page,
            st.Page("pages/admin/quan_ly_nhan_su.py", title="Quản Lý Nhân Sự" if lang == "vi" else "Staff Management"),
            st.Page("pages/operator/quan_ly_cua_hang.py", title="Quản Lý Cửa Hàng iKids" if lang == "vi" else "iKids Store Management"),
            st.Page("pages/student/trang_ca_nhan.py", title="Cài Đặt Hệ Thống" if lang == "vi" else "System Settings")
        ])

    # 2. Quyền hạn: Operator (Vận hành)
    elif role == "operator":
        menu_pages.extend([
            # FIX DỨT ĐIỂM: Operator không có file dashboard.py riêng, sử dụng đúng các trang chức năng cốt lõi của họ
            giao_dich_tien_page,
            st.Page("pages/operator/xep_lich.py", title="Xếp Lịch Dạy" if lang == "vi" else "Schedule Teaching"),
            st.Page("pages/operator/quan_ly_lop.py", title="Quản Lý Lớp Học" if lang == "vi" else "Class Management"), 
            st.Page("pages/operator/quan_ly_cua_hang.py", title="Quản Lý Cửa Hàng iKids" if lang == "vi" else "iKids Store Management"),
            st.Page("pages/student/trang_ca_nhan.py", title="Trang Cá Nhân" if lang == "vi" else "My Profile")
        ])

    # 3. Quyền hạn: Teacher (Giáo viên)
    elif role == "teacher":
        menu_pages.extend([
            st.Page("pages/teacher/dashboard.py", title="Bảng Tin Giáo Viên" if lang == "vi" else "Teacher Dashboard"),
            st.Page("pages/teacher/nhat_ky.py", title="Nhật Ký & Điểm Danh" if lang == "vi" else "Class Journal"),
            st.Page("pages/teacher/tao_quiz.py", title="Quản Lý Bài Tập AI" if lang == "vi" else "AI Quiz Management"),
            st.Page("pages/teacher/kho_hoc_lieu.py", title="Kho Học Liệu" if lang == "vi" else "Learning Resources"),
            st.Page("pages/teacher/giao_bai.py", title="Giao Bài Tập" if lang == "vi" else "Assign Homework"),
            st.Page("pages/teacher/quan_ly_diem.py", title="Quản Lý & Ghi Điểm" if lang == "vi" else "Grade Management"),
            st.Page("pages/student/trang_ca_nhan.py", title="Trang Cá Nhân" if lang == "vi" else "My Profile")        
        ])

    # 4. Quyền hạn: Student (Học sinh)
    elif role == "student":
        menu_pages.extend([
            st.Page("pages/student/dashboard.py", title="Góc Học Tập" if lang == "vi" else "Learning Corner"),
            st.Page("pages/student/lich_hoc.py", title="Lịch Học" if lang == "vi" else "Class Schedule"),
            st.Page("pages/student/quiz.py", title="Trạm Quiz AI" if lang == "vi" else "AI Quiz Station"),
            st.Page("pages/student/cua_hang.py", title="Cửa Hàng iKids" if lang == "vi" else "iKids Store"),
            st.Page("pages/student/video.py", title="Rạp Chiếu Video AI" if lang == "vi" else "AI Video Cinema"),
            st.Page("pages/student/ket_qua.py", title="Bảng Điểm Cá Nhân" if lang == "vi" else "My Report Card"), # ĐÃ BỔ SUNG TẠI ĐÂY
            st.Page("pages/student/trang_ca_nhan.py", title="Trang Cá Nhân" if lang == "vi" else "My Profile")
        ])

    # 5. Quyền hạn: Parent (Phụ huynh)
    elif role == "parent":
        menu_pages.extend([
            st.Page("pages/parent/quan_ly_con.py", title="Quản Lý Con Em" if lang == "vi" else "Children Management"),
            st.Page("pages/parent/chon_lop.py", title="Đăng Ký Lớp Học" if lang == "vi" else "Class Enrollment"), 
            st.Page("pages/parent/ket_qua.py", title="Báo Cáo Học Tập" if lang == "vi" else "Learning Report"),
            st.Page("pages/parent/nap_tien.py", title="Nạp Tiền & Ví" if lang == "vi" else "Wallet & Deposit"),
            st.Page("pages/parent/cua_hang.py", title="Mua Đồ Cho Con" if lang == "vi" else "Buy Rewards for Kid"),
            st.Page("pages/parent/lien_he.py", title="Liên Hệ & Xin Nghỉ" if lang == "vi" else "Contact & Leave Request"),
            st.Page("pages/student/trang_ca_nhan.py", title="Cài Đặt Tài Khoản" if lang == "vi" else "Account Settings")
        ])

    # Khởi tạo Navigation động dựa trên mảng danh sách trang đã phân phối quyền thành công
    pg = st.navigation(menu_pages)
    
    # Hiển thị thông tin định danh ở góc thanh Sidebar menu
    with st.sidebar:
        welcome_txt = "Chào" if lang == "vi" else "Welcome"
        st.write(f"### {welcome_txt}, {user.get('full_name', user.get('name', 'Member'))}! ")
        
        BACKEND_URL = os.getenv("API_URL", "http://localhost:8000")
        if avatar_url:
            if avatar_url.startswith("/"):
               st.image(f"{BACKEND_URL}{avatar_url}", width=100)
            else:
                st.image(avatar_url, width=100)
        else:
            st.image("https://api.dicebear.com/7.x/avataaars/svg?seed=" + user.get('email', 'ikids'), width=100)
            
        st.caption(f"{UI_LOCALES[lang]['sidebar_role']}: {role.upper()}")
        st.divider()
        
        if st.button(UI_LOCALES[lang]['btn_logout'], key="logout_sidebar", use_container_width=True, type="primary"):
            logout_user()
            st.rerun()
            
    pg.run()