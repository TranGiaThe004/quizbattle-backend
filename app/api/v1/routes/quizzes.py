# quizbattle-backend/app/api/v1/routes/quizzes.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session,joinedload 
from app.db.session import get_db
from app.models.quiz import Quiz
from app.models.user import User
from app.schemas.quiz import QuizUpdate
from app.schemas.common import StandardResponse
from app.core.security import get_current_user
from app.models.question import Question, QuestionOption, QuestionType
from app.schemas.question import TrueFalseQuestionCreate, QuestionResponse
from typing import List


router = APIRouter(prefix="/api/v1/quizzes", tags=["Quizzes & Questions"])



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

# 1. API: Lấy chi tiết 1 Quiz kèm theo toàn bộ câu hỏi và options
@router.get("/{quiz_id}", response_model=dict)
def get_quiz_detail(quiz_id: int, db: Session = Depends(get_db)):
    # Dùng joinedload để query một lần lấy cả Quiz -> Questions -> Options (Tránh N+1 query)
    quiz = db.query(Quiz).options(
        joinedload(Quiz.questions).joinedload(Question.options)
    ).filter(Quiz.id == quiz_id).first()

    if not quiz:
        raise HTTPException(status_code=404, detail="Không tìm thấy Quiz")

    # Serialize dữ liệu trả về
    return {
        "success": True,
        "data": {
            "id": quiz.id,
            "title": quiz.title,
            "description": quiz.description,
            "is_public": quiz.is_public,
            "questions": [QuestionResponse.model_validate(q).model_dump() for q in quiz.questions]
        }
    }

# 2. API: Tạo câu hỏi True/False
@router.post("/{quiz_id}/questions/true-false")
def create_true_false_question(
    quiz_id: int, 
    req: TrueFalseQuestionCreate, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user) # Bắt buộc phải có token
):
    # Kiểm tra quiz có tồn tại không
    quiz = db.query(Quiz).filter(Quiz.id == quiz_id).first()
    if not quiz:
        raise HTTPException(status_code=404, detail="Không tìm thấy Quiz để thêm câu hỏi")

    # Đếm số câu hỏi hiện tại để gán order_index
    current_count = db.query(Question).filter(Question.quiz_id == quiz_id).count()

    # Tạo câu hỏi gốc
    new_question = Question(
        quiz_id=quiz_id,
        question_text=req.question_text,
        question_type=QuestionType.true_false,
        time_limit_seconds=req.time_limit_seconds,
        order_index=current_count + 1
    )
    db.add(new_question)
    db.flush() # Lấy ID của new_question ngay lập tức mà chưa cần commit

    # Tự động sinh ra 2 Option
    option_true = QuestionOption(
        question_id=new_question.id, 
        option_text="True", 
        is_correct=req.is_true_correct, 
        order_index=1
    )
    option_false = QuestionOption(
        question_id=new_question.id, 
        option_text="False", 
        is_correct=not req.is_true_correct, 
        order_index=2
    )
    
    db.add_all([option_true, option_false])
    db.commit()

    return {"success": True, "message": "Đã thêm câu hỏi True/False thành công"}