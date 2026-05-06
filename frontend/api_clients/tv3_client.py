import requests
import streamlit as st

API_URL = "http://localhost:8000/api/tv3"

def get_gamification_profile(student_id):
    """Gọi API lấy thông tin Xu và Rank của học sinh"""
    try:
        res = requests.get(f"{API_URL}/gamification/profile/{student_id}")
        if res.status_code == 200:
            return res.json()
    except Exception:
        pass
    # Trả về mặc định nếu lỗi hoặc chưa có dữ liệu
    return {"total_coins": 0, "rank_level": "Beginner", "current_streak": 0}

def submit_contact(sender_id, receiver_id, subject, content):
    """Gọi API gửi yêu cầu xin nghỉ/liên hệ từ Phụ huynh"""
    payload = {
        "sender_id": sender_id,
        "receiver_id": receiver_id,
        "subject": subject,
        "content": content
    }
    try:
        res = requests.post(f"{API_URL}/contact/submit", json=payload)
        return res.status_code == 200, res.json()
    except Exception as e:
        return False, {"detail": str(e)}

def get_contact_history(parent_id):
    """Gọi API lấy lịch sử tin nhắn của Phụ huynh"""
    try:
        res = requests.get(f"{API_URL}/contact/history/{parent_id}")
        if res.status_code == 200:
            return res.json()
    except Exception:
        pass
    return []