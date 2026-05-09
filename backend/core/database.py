from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv

load_dotenv()

# Chuỗi kết nối bạn cung cấp
MONGO_DETAILS = "mongodb+srv://phay123321_db_user:13251900Phat@cluster0.v6iwegp.mongodb.net/?retryWrites=true&w=majorit"

client = AsyncIOMotorClient(MONGO_DETAILS)

# Tên database dự án
database = client.iKids_Project_DB

# Hàm helper để lấy database trong các route FastAPI
def get_db():
    return database