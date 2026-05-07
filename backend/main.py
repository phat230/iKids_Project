from fastapi import FastAPI
from modules.auth.router import router as auth_router
from modules.tv3_community.router import router as tv3_router
from fastapi.staticfiles import StaticFiles
app = FastAPI(title="iKids Education Portal API")

# Đăng ký các module vào hệ thống
app.include_router(auth_router) 
app.include_router(tv3_router, prefix="/api/tv3", tags=["Thành viên 3 - Community"])
app.mount("/static", StaticFiles(directory="static"), name="static")
@app.get("/")
def read_root():
    return {"message": "Welcome to iKids Portal API (Secured)"}