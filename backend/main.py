from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import os

# Import các router
from modules.auth.router import router as auth_router
from modules.notification.router import router as notification_router
from modules.tv1_scheduling.router import router as tv1_router
from modules.tv2_academic.router import router as tv2_router
from modules.tv3_community.router import router as tv3_router

app = FastAPI(title="iKids Education Portal API")

# 1. CẤU HÌNH CORS (Quan trọng để Streamlit không bị chặn)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 2. ĐĂNG KÝ CÁC ROUTER (Module)
# Auth & Notifications
app.include_router(auth_router)
app.include_router(notification_router)

# TV1: Lịch dạy & Vận hành
app.include_router(tv1_router)

# TV2: Học liệu & Giáo viên (Academic)
app.include_router(tv2_router)

# TV3: Phụ huynh & Cộng đồng (Community)
# LƯU Ý: Nếu bên trong router.py của TV3 đã có "/api/tv3", thì bỏ prefix ở đây.
# Nếu bên trong router.py chỉ để là "/posts", thì giữ nguyên prefix này.
app.include_router(tv3_router, prefix="/api/tv3", tags=["Thành viên 3 - Community"])

# 3. CẤU HÌNH STATIC FILES (Tạo thư mục nếu chưa có để tránh lỗi crash)
if not os.path.exists("static"):
    os.makedirs("static")
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
def read_root():
    return {
        "status": "online",
        "message": "iKids Education Portal API is running",
        "docs": "/docs"
    }