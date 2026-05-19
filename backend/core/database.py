from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv

# Load file .env
load_dotenv()

# Lấy thông tin từ .env
MONGO_URI = os.getenv("MONGO_URI")
DATABASE_NAME = os.getenv("DATABASE_NAME")

if not MONGO_URI:
    raise ValueError("⚠️ CẢNH BÁO: Không tìm thấy MONGO_URI trong file .env")

# Kết nối
client = AsyncIOMotorClient(MONGO_URI)
database = client[DATABASE_NAME]

def get_db():
    return database