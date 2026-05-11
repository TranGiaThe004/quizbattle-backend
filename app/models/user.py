from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.sql import func
from datetime import datetime
from app.db.base import Base
from sqlalchemy.orm import relationship

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    
    # Đổi server_default=func.now() → default=datetime.utcnow
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    quizzes = relationship("Quiz", back_populates="host", cascade="all, delete-orphan")
