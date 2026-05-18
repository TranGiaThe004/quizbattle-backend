# quizbattle-backend/app/api/v1/routes/quizzes.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload
from app.db.session import get_db

from app.models.quiz import Quiz
from app.models.user import User
from app.models.question import Question, QuestionOption, QuestionType

from app.schemas.quiz import QuizUpdate, QuizCreate, QuizResponse, QuestionCreate
from app.schemas.question import TrueFalseQuestionCreate, QuestionResponse
from app.schemas.common import StandardResponse
from app.core.security import get_current_user
from typing import List

from fastapi import Query
from app.schemas.quiz import QuizPublicOut

router = APIRouter(prefix="/api/v1/quizzes", tags=["Quizzes"])

# =========================================
# CREATE QUIZ
# =========================================
@router.post("", response_model=QuizResponse)
def create_quiz(quiz_in: QuizCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    new_quiz = Quiz(
        host_id=current_user.id,
        title=quiz_in.title,
        description=quiz_in.description,
        is_public=quiz_in.is_public
    )
    db.add(new_quiz)
    db.commit()
    db.refresh(new_quiz)
    return new_quiz

# =========================================
# GET USER QUIZZES
# =========================================
@router.get("")
def get_quizzes(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    quizzes = db.query(Quiz).filter(Quiz.host_id == current_user.id).all()
    return quizzes

# =========================================
# LẤY CHI TIẾT 1 QUIZ KÈM THEO CÂU HỎI VÀ OPTIONS
# =========================================
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

# =========================================
# UPDATE QUIZ
# =========================================
@router.patch("/{quiz_id}", response_model=StandardResponse)
def update_quiz(quiz_id: int, quiz_in: QuizUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    quiz = db.query(Quiz).filter(Quiz.id == quiz_id).first()
    if not quiz:
        raise HTTPException(status_code=404, detail="Không tìm thấy Quiz.")

    if quiz.host_id != current_user.id:
        raise HTTPException(status_code=403, detail="FORBIDDEN: Bạn không có quyền sửa quiz này.")

    update_data = quiz_in.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(quiz, key, value)

    db.commit()
    return StandardResponse(success=True, message="Cập nhật quiz thành công!")

# =========================================
# DELETE QUIZ
# =========================================
@router.delete("/{quiz_id}", response_model=StandardResponse)
def delete_quiz(quiz_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    quiz = db.query(Quiz).filter(Quiz.id == quiz_id).first()
    if not quiz:
        raise HTTPException(status_code=404, detail="Không tìm thấy Quiz.")

    if quiz.host_id != current_user.id:
        raise HTTPException(status_code=403, detail="FORBIDDEN: Bạn không có quyền xóa quiz này.")

    db.delete(quiz)
    db.commit()
    return StandardResponse(success=True, message="Xóa quiz thành công!")

# =========================================
# CREATE MULTIPLE CHOICE QUESTION
# =========================================
@router.post("/{quiz_id}/questions")
def create_question(quiz_id: int, question_in: QuestionCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if len(question_in.options) < 2 or len(question_in.options) > 4:
        raise HTTPException(status_code=400, detail="Phải có từ 2 đến 4 đáp án")

    correct_answers = sum(1 for option in question_in.options if option.is_correct)
    if correct_answers != 1:
        raise HTTPException(status_code=400, detail="Phải có đúng 1 đáp án đúng")

    quiz = db.query(Quiz).filter(Quiz.id == quiz_id).first()
    if not quiz:
        raise HTTPException(status_code=404, detail="Quiz không tồn tại")

    # THÊM DÒNG NÀY ĐỂ DEBUG:
    print(f"--- DEBUG PHÂN QUYỀN: ID Chủ phòng: {quiz.host_id} | ID Người gọi API: {current_user.id} ---")
    if quiz.host_id != current_user.id:
        raise HTTPException(status_code=403, detail="Bạn không có quyền thêm câu hỏi")
    

    new_question = Question(
        quiz_id=quiz_id,
        question_text=question_in.question_text,
        question_type=QuestionType.multiple_choice
    )
    db.add(new_question)
    db.commit()
    db.refresh(new_question)

    for option in question_in.options:
        new_option = QuestionOption(
            question_id=new_question.id,
            option_text=option.option_text,
            is_correct=option.is_correct
        )
        db.add(new_option)

    db.commit()
    return {"success": True, "message": "Tạo câu hỏi thành công"}

# =========================================
# CREATE TRUE/FALSE QUESTION
# =========================================
@router.post("/{quiz_id}/questions/true-false")
def create_true_false_question(quiz_id: int, req: TrueFalseQuestionCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    quiz = db.query(Quiz).filter(Quiz.id == quiz_id).first()
    if not quiz:
        raise HTTPException(status_code=404, detail="Không tìm thấy Quiz để thêm câu hỏi")
    
    if quiz.host_id != current_user.id:
        raise HTTPException(status_code=403, detail="Bạn không có quyền thêm câu hỏi")

    current_count = db.query(Question).filter(Question.quiz_id == quiz_id).count()

    new_question = Question(
        quiz_id=quiz_id,
        question_text=req.question_text,
        question_type=QuestionType.true_false,
        time_limit_seconds=req.time_limit_seconds,
        order_index=current_count + 1
    )
    db.add(new_question)
    db.flush()

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

@router.get("/public-quizzes", response_model=list[QuizPublicOut])
def get_public_quizzes(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, le=100),
    db: Session = Depends(get_db),
):
    return (
        db.query(Quiz)
        .filter(Quiz.is_public == True)
        .order_by(Quiz.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )