import streamlit as st
from datetime import datetime, timedelta

def get_start_of_week(date):
    """Tính ngày Thứ 2 của tuần chứa ngày hiện tại để đồng bộ lịch"""
    return date - timedelta(days=date.weekday())

def get_sync_schedule():
    """Hàm lấy dữ liệu ĐỒNG BỘ với tuần hiện tại và LỌC logic thời gian"""
    today = datetime.now()
    start_of_week = get_start_of_week(today)
    
    # Dữ liệu mô phỏng lịch của nguyên 1 tuần (Khớp với Dashboard)
    weekly_schedule = [
        {"day_offset": 0, "time": "08:00 - 09:30", "subject": "Toán Tư Duy - 1A", "room": "Phòng 101"}, # Thứ 2
        {"day_offset": 1, "time": "14:00 - 15:30", "subject": "Lập trình Scratch", "room": "Phòng Máy 1"}, # Thứ 3
        # Tự động gán 1 lớp vào đúng ngày hiện tại (Hôm nay) để test
        {"day_offset": today.weekday(), "time": "18:00 - 19:30", "subject": "Tiếng Anh Giao Tiếp", "room": "Phòng 205"}, 
        {"day_offset": 4, "time": "09:00 - 10:30", "subject": "Khoa Học Vui - 2B", "room": "Phòng Lab"}, # Thứ 6
    ]
    
    sync_classes = []
    # Khử trùng lặp (trường hợp hôm nay vô tình rơi vào thứ 2, thứ 3, thứ 6)
    seen_offsets = set()
    
    for item in weekly_schedule:
        if item["day_offset"] in seen_offsets:
            continue
        seen_offsets.add(item["day_offset"])
            
        class_date = start_of_week + timedelta(days=item["day_offset"])
        
        # LOGIC QUAN TRỌNG: Chỉ hiện lớp của HÔM NAY hoặc TRƯỚC ĐÓ trong tuần
        # (Không ai ghi nhật ký cho lớp học của ngày mai cả)
        if class_date.date() <= today.date():
            date_str = class_date.strftime("%d/%m")
            
            # Làm nổi bật lớp của ngày hôm nay
            label = " 🟢 (HÔM NAY)" if class_date.date() == today.date() else ""
            
            class_str = f"{item['time']} ({date_str}){label} | {item['subject']} | {item['room']}"
            sync_classes.append(class_str)
            
    # Sắp xếp lại danh sách từ đầu tuần đến hôm nay
    sync_classes.sort()
    return sync_classes

def render_attendance_and_log():
    st.set_page_config(layout="wide")
    st.title("📝 Nhật Ký Dạy Học & Điểm Danh")
    st.markdown("Chọn một ca dạy đã/đang diễn ra để thực hiện điểm danh và ghi log hệ thống.")

    # --- 1. LẤY DỮ LIỆU ĐÃ ĐƯỢC LỌC LOGIC ---
    past_classes = get_sync_schedule()
    
    students = [
        {"id": "HS01", "name": "Nguyễn Văn A"},
        {"id": "HS02", "name": "Trần Thị B"},
        {"id": "HS03", "name": "Lê Hoàng C"},
        {"id": "HS04", "name": "Phạm Đăng D"}
    ]
    
    ai_videos = [
        "AI Video: Phép cộng trừ cơ bản",
        "AI Video: Vòng lặp For trong Python",
        "AI Video: Tư duy logic với Scratch"
    ]

    # --- 2. GIAO DIỆN ---
    selected_class = st.selectbox("📌 Chọn ca dạy cần ghi nhật ký:", ["-- Vui lòng chọn --"] + past_classes)

    if selected_class != "-- Vui lòng chọn --":
        st.divider()
        tab1, tab2 = st.tabs(["📋 Điểm Danh Học Viên", "📖 Báo Cáo & Nhật Ký Giảng Dạy"])

        with tab1:
            class_name = selected_class.split('|')[1].strip()
            st.markdown(f"### Danh sách học viên lớp: {class_name}")
            st.caption("Ghi chú: Đánh giá thái độ và điểm danh học viên. Thông tin này sẽ được cập nhật lên hệ thống để phụ huynh theo dõi.")
            
            with st.form("attendance_form"):
                col_name, col_status, col_emoji, col_remark = st.columns([2, 2, 1, 3])
                col_name.write("**Tên học viên**")
                col_status.write("**Trạng thái**")
                col_emoji.write("**Thái độ**")
                col_remark.write("**Nhận xét chi tiết**")
                st.markdown("---")
                
                for hs in students:
                    c1, c2, c3, c4 = st.columns([2, 2, 1, 3])
                    c1.markdown(f"<p style='padding-top: 10px;'>{hs['id']} - <b>{hs['name']}</b></p>", unsafe_allow_html=True)
                    
                    c2.radio("Trạng thái", ["Có mặt", "Đi trễ", "Vắng mặt"], key=f"status_{hs['id']}", horizontal=True, label_visibility="collapsed")
                    c3.selectbox("Emoji", ["⭐", "👍", "🔥", "🤔", "😴"], key=f"emoji_{hs['id']}", label_visibility="collapsed")
                    c4.text_input("Nhận xét", placeholder="VD: Rất hăng hái phát biểu...", key=f"remark_{hs['id']}", label_visibility="collapsed")
                
                st.markdown("---")
                if st.form_submit_button("Lưu Điểm Danh Lên Hệ Thống", type="primary"):
                    st.success("✅ Đã lưu điểm danh và nhận xét thành công! Dữ liệu đã được cập nhật cho Phụ huynh.")

        with tab2:
            st.markdown("### Nội dung buổi học")
            with st.form("academic_log_form"):
                taught_content = st.text_area("Nội dung đã giảng dạy trong ca này (Bắt buộc):", placeholder="Nhập các khái niệm, bài tập đã hướng dẫn...")
                used_videos = st.multiselect("📚 Video AI đã sử dụng trong lớp:", ai_videos)
                
                st.markdown("**Giao bài tập về nhà (Tự động chấm):**")
                assign_quiz = st.checkbox("Đính kèm bộ câu hỏi Quiz của các Video AI đã chọn cho học viên.")
                
                if st.form_submit_button("Gửi Báo Cáo Giảng Dạy", type="primary"):
                    if not taught_content:
                        st.error("⚠️ Vui lòng nhập nội dung đã giảng dạy!")
                    else:
                        st.success("✅ Đã lưu Nhật Ký Giảng Dạy!")
                        if assign_quiz and used_videos:
                            st.info(f"Đã tự động gửi bài tập Quiz của {len(used_videos)} video đến phụ huynh và học viên.")

if __name__ == "__main__":
    render_attendance_and_log()