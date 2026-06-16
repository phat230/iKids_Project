# frontend/api_clients/tv2_client.py
import os
import requests
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

# ĐÃ SỬA: Đổi "/academic" thành "/api/tv2" để khớp với Backend
BASE_URL = f"{os.getenv('API_URL', 'http://localhost:8000')}/api/tv2"

def get_headers():
    """Lấy token từ session state để xác thực"""
    token = st.session_state.get("access_token")
    if token:
        return {"Authorization": f"Bearer {token}"}
    return {}

def submit_journal(journal_data: dict):
    """Gửi dữ liệu nhật ký giảng dạy xuống Backend"""
    try:
        response = requests.post(
            f"{BASE_URL}/journal",
            json=journal_data,
            headers=get_headers()
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Lỗi kết nối máy chủ: {e}")
        return None

def generate_quiz_via_ai(topic: str, num_questions: int = 5):
    """Gọi Backend yêu cầu AI sinh câu hỏi trắc nghiệm"""
    try:
        response = requests.post(
            f"{BASE_URL}/generate-quiz",
            json={"topic": topic, "num_questions": num_questions},
            headers=get_headers()
        )
        if response.status_code == 200:
            return response.json()
        return None
    except Exception as e:
        st.error(f"Lỗi gọi AI: {e}")
        return None

def save_quiz(quiz_data: dict):
    """Lưu bộ Quiz vào database"""
    try:
        response = requests.post(
            f"{BASE_URL}/quiz",
            json=quiz_data,
            headers=get_headers()
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        st.error(f"Lỗi lưu Quiz: {e}")
        return None
    
def assign_quiz_to_class(data: dict):
    """Gửi yêu cầu giao bài tập lên Backend"""
    try:
        response = requests.post(
            f"{BASE_URL}/assign-quiz", 
            json=data,
            headers=get_headers()
        )
        return response.status_code == 200
    except Exception as e:
        st.error(f"Lỗi giao bài: {e}")
        return False