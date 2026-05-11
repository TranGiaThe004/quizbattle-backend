from pydantic import BaseModel, ConfigDict,Field
from typing import List, Optional
from enum import Enum

class QuestionTypeEnum(str, Enum):
    multiple_choice = "multiple_choice"
    true_false = "true_false"

class TrueFalseQuestionCreate(BaseModel):
    question_text: str = Field(..., min_length=3, description="Câu hỏi không được để trống")
    # Đặt giới hạn cứng: lớn hơn 0 (gt=0) và nhỏ hơn hoặc bằng 120 (le=120)
    time_limit_seconds: int = Field(..., gt=0, le=120, description="Thời gian phải từ 1 đến 120 giây")
    is_true_correct: bool


class QuestionOptionResponse(BaseModel):
    id: int
    option_text: str
    is_correct: bool
    order_index: int

    model_config = ConfigDict(from_attributes=True)

class QuestionResponse(BaseModel):
    id: int
    question_text: str
    question_type: QuestionTypeEnum
    time_limit_seconds: int
    order_index: int
    options: List[QuestionOptionResponse] = []

    model_config = ConfigDict(from_attributes=True)