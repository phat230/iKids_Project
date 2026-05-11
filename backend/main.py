from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

# Import các router
from modules.auth.router import router as auth_router
from modules.tv3_community.router import router as tv3_router
from modules.tv1_scheduling.router import router as scheduling_router
# Nhúng thêm router của TV2
from modules.tv2_academic.router import router as tv2_router

app = FastAPI(title="iKids Education Portal API")

# CẤU HÌNH CORS (Để Frontend Streamlit có thể gọi API mà không bị chặn)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Đăng ký các module vào hệ thống
app.include_router(auth_router) 

# Module TV1: Lịch dạy & Vận hành
app.include_router(scheduling_router)

# Module TV2: Học liệu & Giáo viên
app.include_router(tv2_router)

# Module TV3: Phụ huynh & Học sinh
app.include_router(tv3_router, prefix="/api/tv3", tags=["Thành viên 3 - Community"])

# Gắn thư mục static
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
def read_root():
    return {"message": "Welcome to iKids Portal API (Secured)"}