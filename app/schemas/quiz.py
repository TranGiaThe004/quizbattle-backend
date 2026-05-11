from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class QuizUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    is_public: Optional[bool] = None


class QuestionUpdate(BaseModel):
    question_text: Optional[str] = None
    time_limit_seconds: Optional[int] = None


# ====================================
# CREATE QUIZ
# ====================================
class QuizCreate(BaseModel):
    title: str
    description: str | None = None
    is_public: bool = False


# ====================================
# QUIZ RESPONSE
# ====================================
class QuizResponse(BaseModel):
    id: int
    title: str
    description: str | None = None
    is_public: bool
    created_at: datetime

    class Config:
        from_attributes = True


# ====================================
# QUESTION OPTIONS
# ====================================
class OptionCreate(BaseModel):
    option_text: str
    is_correct: bool


# ====================================
# CREATE QUESTION
# ====================================
class QuestionCreate(BaseModel):
    question_text: str
    options: list[OptionCreate]