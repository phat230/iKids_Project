import streamlit as st
from utils.role_guard import require_role

require_role(["student"])

st.set_page_config(page_title="Cửa Hàng Đổi Quà", page_icon="🎁", layout="wide")

st.title(" Cửa Hàng iKids")
st.write("Dùng xu học tập của bạn để đổi lấy những phần quà siêu hấp dẫn nhé!")

# Số dư hiện tại
st.success("💰 Số dư của bạn: **1,250 Xu**")
st.divider()

# Danh sách quà tặng
col1, col2, col3 = st.columns(3, gap="large")

with col1:
    with st.container(border=True):
        st.markdown("<h1 style='text-align: center;'>🎒</h1>", unsafe_allow_html=True)
        st.subheader("Balo iKids Cool")
        st.write("Balo siêu nhẹ, chống gù lưng.")
        st.error("Giá: 2,000 Xu")
        st.button("Đổi ngay", key="balo", disabled=True, help="Bạn chưa đủ xu")

with col2:
    with st.container(border=True):
        st.markdown("<h1 style='text-align: center;'>🧸</h1>", unsafe_allow_html=True)
        st.subheader("Gấu Bông Trí Tuệ")
        st.write("Người bạn đồng hành lúc học bài.")
        st.warning("Giá: 1,000 Xu")
        if st.button("Đổi ngay", key="gau_bong", type="primary"):
            st.toast("🎉 Bạn đã đổi thành công Gấu Bông!")

with col3:
    with st.container(border=True):
        st.markdown("<h1 style='text-align: center;'>🎟️</h1>", unsafe_allow_html=True)
        st.subheader("Voucher Gà Rán")
        st.write("Phiếu ăn KFC trị giá 50.000đ.")
        st.warning("Giá: 800 Xu")
        if st.button("Đổi ngay", key="kfc", type="primary"):
            st.toast("🎉 Bạn đã đổi thành công Voucher!")