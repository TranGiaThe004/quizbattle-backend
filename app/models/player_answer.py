# app/models/player_answer.py
from sqlalchemy import Column, Integer, ForeignKey, Boolean, DateTime, UniqueConstraint
from sqlalchemy.sql import func
from app.db.base import Base

class PlayerAnswer(Base):
    __tablename__ = "player_answers"

    id = Column(Integer, primary_key=True, index=True)
    game_session_id = Column(Integer, ForeignKey("game_sessions.id", ondelete="CASCADE"), nullable=False)
    room_player_id = Column(Integer, ForeignKey("room_players.id", ondelete="CASCADE"), nullable=False)
    question_id = Column(Integer, ForeignKey("questions.id", ondelete="CASCADE"), nullable=False)
    selected_option_id = Column(Integer, ForeignKey("question_options.id", ondelete="CASCADE"), nullable=False)
    
    is_correct = Column(Boolean, default=False)
    response_time_ms = Column(Integer, nullable=False)
    score_delta = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # [Quan trọng] Ràng buộc chống submit nhiều lần cho cùng 1 câu hỏi
    __table_args__ = (
        UniqueConstraint('game_session_id', 'room_player_id', 'question_id', name='uix_player_answer'),
    )