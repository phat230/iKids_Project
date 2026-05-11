import requests
import streamlit as st

API_URL = "http://localhost:8000"

def get_headers():
    token = st.session_state.get("access_token")

    return {
        "Authorization": f"Bearer {token}"
    }

# Lấy danh sách user
def get_all_users():

    try:
        res = requests.get(
            f"{API_URL}/staff",
            headers=get_headers()
        )

        if res.status_code == 200:
            return res.json()

        return []

    except Exception:
        return []

# Xóa tài khoản
def delete_user(user_id):

    try:
        res = requests.delete(
            f"{API_URL}/staff/{user_id}",
            headers=get_headers()
        )

        return res.status_code == 200

    except Exception:
        return False

# Khóa tài khoản
def disable_user(user_id):

    try:
        res = requests.put(
            f"{API_URL}/staff/{user_id}/disable",
            headers=get_headers()
        )

        return res.status_code == 200

    except Exception:
        return False

# Mở khóa tài khoản
def enable_user(user_id):

    try:
        res = requests.put(
            f"{API_URL}/staff/{user_id}/enable",
            headers=get_headers()
        )

        return res.status_code == 200

    except Exception:
        return False