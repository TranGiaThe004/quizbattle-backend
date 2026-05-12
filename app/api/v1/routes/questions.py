# quizbattle-backend/app/api/v1/routes/questions.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.session import get_db

from app.models.quiz import Quiz
from app.models.question import Question, QuestionOption
from app.models.user import User

from app.schemas.quiz import QuestionUpdate
from app.schemas.common import StandardResponse
from app.core.security import get_current_user

router = APIRouter(prefix="/api/v1/questions", tags=["Questions"])

def verify_question_ownership(question_id: int, user_id: int, db: Session):
    """Hàm phụ trợ: Lấy câu hỏi ra và Join với Quiz để check xem user có phải chủ Quiz không"""
    question = db.query(Question).filter(Question.id == question_id).first()
    if not question:
        raise HTTPException(status_code=404, detail="Không tìm thấy câu hỏi.")
    
    quiz = db.query(Quiz).filter(Quiz.id == question.quiz_id).first()
    if quiz.owner_id != user_id:
        raise HTTPException(status_code=403, detail="FORBIDDEN: Bạn không có quyền thao tác trên câu hỏi này.")
    return question

@router.patch("/{question_id}", response_model=StandardResponse)
def update_question(question_id: int, question_in: QuestionUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    # Dùng hàm phụ trợ để check quyền và lấy câu hỏi
    question = verify_question_ownership(question_id, current_user.id, db)

    update_data = question_in.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(question, key, value)

    db.commit()
    return StandardResponse(success=True, message="Cập nhật câu hỏi thành công!")

@router.delete("/{question_id}", response_model=StandardResponse)
def delete_question(question_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    question = verify_question_ownership(question_id, current_user.id, db)

    db.delete(question)
    db.commit()
    return StandardResponse(success=True, message="Xóa câu hỏi thành công!")