from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv

load_dotenv() # Load biến môi trường từ file .env

SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL")

# Kết nối với PostgreSQL
engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Hàm Dependency dùng để tiêm database vào các API
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()