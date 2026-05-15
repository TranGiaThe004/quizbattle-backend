from sqlalchemy import Column, Integer, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.base import Base # Thay đổi đường dẫn import Base nếu team bạn để ở chỗ khác

class GameSession(Base):
    __tablename__ = "game_sessions"

    id = Column(Integer, primary_key=True, index=True)
    room_id = Column(Integer, ForeignKey("game_rooms.id", ondelete="CASCADE"), nullable=False)
    quiz_id = Column(Integer, ForeignKey("quizzes.id", ondelete="CASCADE"), nullable=False)
    host_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    ended_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    answers = relationship("PlayerAnswer", back_populates="session", cascade="all, delete-orphan")

class PlayerAnswer(Base):
    __tablename__ = "player_answers"

    id = Column(Integer, primary_key=True, index=True)
    game_session_id = Column(Integer, ForeignKey("game_sessions.id", ondelete="CASCADE"), nullable=False)
    room_player_id = Column(Integer, ForeignKey("room_players.id", ondelete="CASCADE"), nullable=False)
    question_id = Column(Integer, ForeignKey("questions.id", ondelete="CASCADE"), nullable=False)
    
    # Có thể null trong trường hợp hết giờ không kịp chọn đáp án
    selected_option_id = Column(Integer, ForeignKey("question_options.id", ondelete="CASCADE"), nullable=True) 
    
    is_correct = Column(Boolean, default=False)
    response_time_ms = Column(Integer, default=0)
    score_delta = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    session = relationship("GameSession", back_populates="answers")
