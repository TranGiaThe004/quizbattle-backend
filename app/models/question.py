# quizbattle-backend/app/models/question.py
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, Enum
from sqlalchemy.orm import relationship
import enum
from app.db.base import Base

class QuestionType(str, enum.Enum):
    multiple_choice = "multiple_choice"
    true_false = "true_false"

class Question(Base):
    __tablename__ = "questions"

    id = Column(Integer, primary_key=True, index=True)
    quiz_id = Column(Integer, ForeignKey("quizzes.id", ondelete="CASCADE"), nullable=False)
    question_text = Column(String, nullable=False)
    question_type = Column(Enum(QuestionType), nullable=False)
    time_limit_seconds = Column(Integer, default=30)
    order_index = Column(Integer, default=0)
    
    quiz = relationship("Quiz", back_populates="questions")
    options = relationship("QuestionOption", back_populates="question", cascade="all, delete-orphan")

class QuestionOption(Base):
    __tablename__ = "question_options"

    id = Column(Integer, primary_key=True, index=True)
    question_id = Column(Integer, ForeignKey("questions.id", ondelete="CASCADE"), nullable=False)
    option_text = Column(String, nullable=False)
    is_correct = Column(Boolean, default=False)
    order_index = Column(Integer, default=0)

    question = relationship("Question", back_populates="options")