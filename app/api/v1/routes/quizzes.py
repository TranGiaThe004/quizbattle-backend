# quizbattle-backend/app/api/v1/routes/quizzes.py

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db

from app.models.quiz import Quiz
from app.models.user import User
from app.models.question import Question
from app.models.question_option import QuestionOption

from app.schemas.quiz import (
    QuizUpdate,
    QuizCreate,
    QuizResponse,
    QuestionCreate
)

from app.schemas.common import StandardResponse

from app.core.security import get_current_user


router = APIRouter(
    prefix="/api/v1/quizzes",
    tags=["Quizzes"]
)


# =========================================
# CREATE QUIZ
# =========================================
@router.post(
    "",
    response_model=QuizResponse
)
def create_quiz(
    quiz_in: QuizCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    new_quiz = Quiz(
        owner_id=current_user.id,
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
def get_quizzes(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    quizzes = db.query(Quiz).filter(
        Quiz.owner_id == current_user.id
    ).all()

    return quizzes


# =========================================
# UPDATE QUIZ
# =========================================
@router.patch(
    "/{quiz_id}",
    response_model=StandardResponse
)
def update_quiz(
    quiz_id: int,
    quiz_in: QuizUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    # tìm quiz
    quiz = db.query(Quiz).filter(
        Quiz.id == quiz_id
    ).first()

    if not quiz:

        raise HTTPException(
            status_code=404,
            detail="Không tìm thấy Quiz."
        )

    # kiểm tra quyền owner
    if quiz.owner_id != current_user.id:

        raise HTTPException(
            status_code=403,
            detail="FORBIDDEN: Bạn không có quyền sửa quiz này."
        )

    # update data
    update_data = quiz_in.dict(
        exclude_unset=True
    )

    for key, value in update_data.items():

        setattr(quiz, key, value)

    db.commit()

    return StandardResponse(
        success=True,
        message="Cập nhật quiz thành công!"
    )


# =========================================
# DELETE QUIZ
# =========================================
@router.delete(
    "/{quiz_id}",
    response_model=StandardResponse
)
def delete_quiz(
    quiz_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    quiz = db.query(Quiz).filter(
        Quiz.id == quiz_id
    ).first()

    if not quiz:

        raise HTTPException(
            status_code=404,
            detail="Không tìm thấy Quiz."
        )

    # kiểm tra quyền
    if quiz.owner_id != current_user.id:

        raise HTTPException(
            status_code=403,
            detail="FORBIDDEN: Bạn không có quyền xóa quiz này."
        )

    # xóa quiz
    db.delete(quiz)

    db.commit()

    return StandardResponse(
        success=True,
        message="Xóa quiz thành công!"
    )


# =========================================
# CREATE MULTIPLE CHOICE QUESTION
# =========================================
@router.post("/{quiz_id}/questions")
def create_question(
    quiz_id: int,
    question_in: QuestionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    # validate số đáp án
    if len(question_in.options) < 2 or len(question_in.options) > 4:

        raise HTTPException(
            status_code=400,
            detail="Phải có từ 2 đến 4 đáp án"
        )

    # validate chỉ có 1 đáp án đúng
    correct_answers = 0

    for option in question_in.options:

        if option.is_correct:
            correct_answers += 1

    if correct_answers != 1:

        raise HTTPException(
            status_code=400,
            detail="Phải có đúng 1 đáp án đúng"
        )

    # kiểm tra quiz tồn tại
    quiz = db.query(Quiz).filter(
        Quiz.id == quiz_id
    ).first()

    if not quiz:

        raise HTTPException(
            status_code=404,
            detail="Quiz không tồn tại"
        )

    # kiểm tra owner
    if quiz.owner_id != current_user.id:

        raise HTTPException(
            status_code=403,
            detail="Bạn không có quyền thêm câu hỏi"
        )

    # tạo question
    new_question = Question(
        quiz_id=quiz_id,
        question_text=question_in.question_text,
        question_type="multiple_choice"
    )

    db.add(new_question)

    db.commit()

    db.refresh(new_question)

    # tạo options
    for option in question_in.options:

        new_option = QuestionOption(
            question_id=new_question.id,
            option_text=option.option_text,
            is_correct=option.is_correct
        )

        db.add(new_option)

    db.commit()

    return {
        "success": True,
        "message": "Tạo câu hỏi thành công"
    }