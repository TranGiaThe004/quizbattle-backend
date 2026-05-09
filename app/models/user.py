from sqlalchemy import Column, Integer
from app.db.base import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    # Các cột khác Member A sẽ tự thêm vào sau