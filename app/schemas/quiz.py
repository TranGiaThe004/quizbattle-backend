from pydantic import BaseModel
from typing import Optional

class QuizUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    is_public: Optional[bool] = None

class QuestionUpdate(BaseModel):
    question_text: Optional[str] = None
    time_limit_seconds: Optional[int] = None