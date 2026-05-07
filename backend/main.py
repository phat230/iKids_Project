from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

# Sửa lại các dòng import để đồng bộ với cấu trúc thư mục chạy từ backend/
# Lưu ý: Bỏ 'backend.' ở trước 'modules' để uvicorn tìm thấy file khi bạn chạy từ trong thư mục backend
from modules.auth.router import router as auth_router
from modules.tv3_community.router import router as tv3_router
from modules.tv1_scheduling.router import router as scheduling_router

app = FastAPI(title="iKids Education Portal API")

# Đăng ký các module vào hệ thống
app.include_router(auth_router) 

# Đăng ký router Scheduling (TV1) - Nơi xử lý đơn từ Giáo viên
# Giữ nguyên không prefix để khớp với URL: http://127.0.0.1:8000/pending-requests
app.include_router(scheduling_router)

app.include_router(tv3_router, prefix="/api/tv3", tags=["Thành viên 3 - Community"])

# Gắn thư mục static
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
def read_root():
    return {"message": "Welcome to iKids Portal API (Secured)"}