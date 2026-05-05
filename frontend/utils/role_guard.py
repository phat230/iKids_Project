import streamlit as st

def require_role(allowed_roles: list):
    """Kiểm tra quyền truy cập của trang"""
    if "token" not in st.session_state:
        st.warning("🔒 Vui lòng đăng nhập để xem trang này.")
        st.stop() # Dừng vẽ giao diện
        
    current_role = st.session_state.get("role")
    if current_role not in allowed_roles:
        st.error("🚫 Truy cập bị từ chối. Bạn không có quyền xem trang này.")
        st.stop()