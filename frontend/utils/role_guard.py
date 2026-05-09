import streamlit as st

def require_role(allowed_roles: list):
    """
    Kiểm tra quyền truy cập của trang dựa trên vai trò người dùng.
    Mục tiêu 4.3: Đảm bảo an toàn phân quyền trong app.py.
    """
    # 1. Kiểm tra trạng thái đăng nhập
    if "token" not in st.session_state or not st.session_state.get("token"):
        st.warning("🔒 Phiên làm việc đã hết hạn hoặc bạn chưa đăng nhập.")
        if st.button("Đi tới trang Đăng nhập"):
            st.switch_page("app.py") # Hoặc trang login của bạn
        st.stop()
        
    # 2. Kiểm tra vai trò (Role)
    current_role = st.session_state.get("role")
    
    if current_role not in allowed_roles:
        st.error(f"🚫 Truy cập bị từ chối!")
        st.info(f"Trang này dành cho: **{', '.join(allowed_roles).upper()}**. \n\nVai trò hiện tại của bạn là: **{current_role.upper() if current_role else 'N/A'}**")
        
        if st.button("Quay về Trang chủ"):
            st.switch_page("app.py")
        st.stop()

def is_admin():
    """Hàm bổ trợ nhanh để kiểm tra nếu là Admin (TV1)"""
    return st.session_state.get("role") == "admin"