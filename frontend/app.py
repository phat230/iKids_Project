import streamlit as st
from utils.auth_state import logout_user

st.set_page_config(page_title="iKids Portal", layout="centered", page_icon="🚀")

# 1. Khai báo các trang tĩnh
home_page = st.Page("home.py", title="Trang Chủ", icon="🏠", default=True)

# Trỏ trực tiếp tới 2 file trong thư mục auth thay vì dùng hàm
login_page = st.Page("auth/login.py", title="Đăng Nhập", icon="🔐")
register_page = st.Page("auth/register.py", title="Đăng Ký", icon="📝")

# 2. Xử lý điều hướng
if "token" not in st.session_state:
    # Chưa đăng nhập -> Hiển thị Trang chủ, Đăng nhập, Đăng ký
    pg = st.navigation([home_page, login_page, register_page])
    pg.run()

else:
    # Đã đăng nhập -> Đọc role và điều hướng
    role = st.session_state["role"]
    user = st.session_state["user_info"]
    
    menu_pages = [home_page] 
    
    if role == "student":
        menu_pages.append(st.Page("pages/student/dashboard.py", title="Bảng Điều Khiển", icon="🚀"))
        menu_pages.append(st.Page("pages/student/lich_hoc.py", title="Lịch Học Của Tôi", icon="📅"))
        menu_pages.append(st.Page("pages/student/quiz.py", title="Bài Tập AI", icon="📝"))
        menu_pages.append(st.Page("pages/student/ket_qua.py", title="Bảng Điểm", icon="📈"))
        menu_pages.append(st.Page("pages/student/cua_hang.py", title="Cửa Hàng Đổi Xu", icon="🎁"))
        menu_pages.append(st.Page("pages/student/ky_niem.py", title="Góc Kỷ Niệm", icon="📸"))
        
    elif role == "parent":
        menu_pages.append(st.Page("pages/parent/quan_ly_con.py", title="Quản Lý Con Em", icon="👨‍👩‍👦"))
        menu_pages.append(st.Page("pages/parent/ket_qua.py", title="Báo Cáo Học Tập", icon="📊"))
        menu_pages.append(st.Page("pages/parent/ky_niem.py", title="Góc Kỷ Niệm", icon="📸"))
        menu_pages.append(st.Page("pages/parent/lien_he.py", title="Liên Hệ & Yêu Cầu", icon="📞"))
    pg = st.navigation(menu_pages)
    
    with st.sidebar:
        st.divider()
        st.markdown(f"👤 **{user['name']}**")
        st.caption(f"Role: {role.upper()}")
        if st.button("🚪 Đăng Xuất", use_container_width=True):
            logout_user()
            
    pg.run()