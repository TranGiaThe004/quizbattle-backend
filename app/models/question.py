from sqlalchemy import Column, Integer, String
from sqlalchemy import ForeignKey, Text
from sqlalchemy.orm import relationship

from app.db.base import Base


class Question(Base):

    __tablename__ = "questions"

    id = Column(Integer, primary_key=True)

    quiz_id = Column(
        Integer,
        ForeignKey("quizzes.id")
    )

    question_text = Column(
        Text,
        nullable=False
    )

    question_type = Column(
        String(50),
        default="multiple_choice"
    )

    quiz = relationship(
        "Quiz",
        back_populates="questions"
    )

    options = relationship(
        "QuestionOption",
        back_populates="question",
        cascade="all, delete-orphan"
    )