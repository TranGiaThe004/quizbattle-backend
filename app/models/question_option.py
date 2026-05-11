from sqlalchemy import Column, Integer
from sqlalchemy import ForeignKey, String
from sqlalchemy import Boolean
from sqlalchemy.orm import relationship

from app.db.base import Base


class QuestionOption(Base):

    __tablename__ = "question_options"

    id = Column(Integer, primary_key=True)

    question_id = Column(
        Integer,
        ForeignKey("questions.id")
    )

    option_text = Column(String(255))

    is_correct = Column(
        Boolean,
        default=False
    )

    question = relationship(
        "Question",
        back_populates="options"
    )