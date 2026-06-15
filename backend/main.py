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
from modules.finance.router import router as finance_router

app = FastAPI(title="iKids Education Portal API")

# 1. CẤU HÌNH CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 2. ĐĂNG KÝ CÁC ROUTER VỚI PREFIX ĐỒNG BỘ
# Bây giờ tất cả API đều nằm dưới namespace /api/...
app.include_router(auth_router, prefix="/api/auth", tags=["Authentication"])
app.include_router(notification_router, prefix="/api/notifications", tags=["Notifications"])
app.include_router(finance_router, prefix="/api/finance", tags=["Finance"])
app.include_router(tv1_router, prefix="/api/tv1", tags=["TV1 - Scheduling"])
app.include_router(tv2_router, prefix="/api/tv2", tags=["TV2 - Academic"])
app.include_router(tv3_router, prefix="/api/tv3", tags=["TV3 - Community"])

# 3. CẤU HÌNH STATIC FILES
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