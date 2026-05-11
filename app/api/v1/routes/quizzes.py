# quizbattle-backend/app/api/v1/routes/quizzes.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.quiz import Quiz
from app.models.user import User
from app.schemas.quiz import QuizUpdate
from app.schemas.common import StandardResponse
from app.core.security import get_current_user

router = APIRouter(prefix="/api/v1/quizzes", tags=["Quizzes"])

@router.patch("/{quiz_id}", response_model=StandardResponse)
def update_quiz(quiz_id: int, quiz_in: QuizUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    # 1. Tìm quiz
    quiz = db.query(Quiz).filter(Quiz.id == quiz_id).first()
    if not quiz:
        raise HTTPException(status_code=404, detail="Không tìm thấy Quiz.")
    
    # 2. KIỂM TRA QUYỀN (Owner Permission) - QUAN TRỌNG NHẤT
    if quiz.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="FORBIDDEN: Bạn không có quyền sửa quiz này.")

    # 3. Cập nhật dữ liệu
    update_data = quiz_in.dict(exclude_unset=True) # Chỉ lấy các field được truyền lên
    for key, value in update_data.items():
        setattr(quiz, key, value)

    db.commit()
    return StandardResponse(success=True, message="Cập nhật quiz thành công!")

@router.delete("/{quiz_id}", response_model=StandardResponse)
def delete_quiz(quiz_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    quiz = db.query(Quiz).filter(Quiz.id == quiz_id).first()
    if not quiz:
        raise HTTPException(status_code=404, detail="Không tìm thấy Quiz.")
    
    # Kiểm tra quyền
    if quiz.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="FORBIDDEN: Bạn không có quyền xóa quiz này.")

    # Xóa (Vì đã cài cascade, nó sẽ xóa sạch các câu hỏi bên trong)
    db.delete(quiz)
    db.commit()
    return StandardResponse(success=True, message="Xóa quiz thành công!")