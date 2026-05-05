import requests

API_URL = "http://localhost:8000/api/tv3"

def get_dashboard_data(student_id):
    response = requests.get(f"{API_URL}/dashboard/{student_id}")
    return response.json() if response.status_code == 200 else None

def earn_coins(student_id, action, ref_id):
    params = {"student_id": student_id, "action": action, "reference_id": ref_id}
    return requests.post(f"{API_URL}/earn-coins", params=params).json()