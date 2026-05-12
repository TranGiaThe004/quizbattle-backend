# quizbattle-backend/app/models/room.py
import enum
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime, Enum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.db.base import Base

# Khai báo Enum trạng thái phòng theo đúng SRS
class RoomStatus(str, enum.Enum):
    waiting = "waiting"
    playing = "playing"
    finished = "finished"

class GameRoom(Base):
    __tablename__ = "game_rooms"

    id = Column(Integer, primary_key=True, index=True)
    room_code = Column(String(6), unique=True, index=True, nullable=False)
    host_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    quiz_id = Column(Integer, ForeignKey("quizzes.id", ondelete="CASCADE"), nullable=False)
    status = Column(Enum(RoomStatus), default=RoomStatus.waiting)
    current_question_index = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Quan hệ
    host = relationship("User")
    quiz = relationship("Quiz")
    players = relationship("RoomPlayer", back_populates="room", cascade="all, delete-orphan")

class RoomPlayer(Base):
    __tablename__ = "room_players"

    id = Column(Integer, primary_key=True, index=True)
    room_id = Column(Integer, ForeignKey("game_rooms.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    display_name = Column(String, nullable=False)
    score = Column(Integer, default=0)
    is_connected = Column(Boolean, default=True)
    joined_at = Column(DateTime(timezone=True), server_default=func.now())

    # Quan hệ
    room = relationship("GameRoom", back_populates="players")
    user = relationship("User")