import streamlit as st
import time

st.set_page_config(page_title="Bài Tập AI", page_icon="📝")

st.title("📝 Trạm Huấn Luyện AI")
st.write("Hoàn thành các bài tập trắc nghiệm dưới đây để nhận iKids Xu nhé!")
st.divider()

# Giả lập một bài tập chưa hoàn thành
st.subheader("📌 Nhiệm vụ đang chờ: Phép toán cơ bản")
st.caption("Môn: Toán | Giáo viên: Cô Alice | Phần thưởng: 10 Xu")

with st.form("quiz_form"):
    q1 = st.radio(
        "Câu 1: Nếu con có 5 quả táo, bạn cho thêm 7 quả nữa. Hỏi con có mấy quả?",
        options=["10 quả", "11 quả", "12 quả", "13 quả"],
        index=None
    )
    
    q2 = st.radio(
        "Câu 2: Hình nào dưới đây có 3 cạnh?",
        options=["Hình vuông", "Hình tròn", "Hình tam giác", "Hình chữ nhật"],
        index=None
    )
    
    submit_quiz = st.form_submit_button("Nộp Bài & Nhận Thưởng", use_container_width=True)
    
    if submit_quiz:
        if not q1 or not q2:
            st.warning("Con hãy trả lời hết các câu hỏi trước khi nộp bài nhé!")
        else:
            with st.spinner("Hệ thống AI đang chấm bài..."):
                time.sleep(1) # Giả lập thời gian chờ API
                
                # Logic chấm điểm đơn giản
                if q1 == "12 quả" and q2 == "Hình tam giác":
                    st.success("Tuyệt vời! Con trả lời đúng 100%. Đã cộng 10 iKids Xu vào ví! 🎉")
                    st.balloons()
                    # Ghi chú cho Backend: Tại đây sẽ gọi api_clients.tv3_client.earn_coins()
                else:
                    st.error("Có câu sai mất rồi. Con hãy đọc kỹ đề và làm lại nhé!")