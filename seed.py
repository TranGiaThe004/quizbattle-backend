from app.db.session import SessionLocal
from app.models.user import User
from app.models.quiz import Quiz # Giả sử Member B đã tạo
from app.models.question import Question, QuestionOption, QuestionType
from app.core.security import get_password_hash # Nếu bạn dùng hàm băm từ trước

def seed_data():
    db = SessionLocal()
    try:
        # 1. Tạo 1 User test
        test_user = User(username="host1", email="host@test.com", password_hash=get_password_hash("123456"))
        db.add(test_user)
        db.flush()

        # 2. Tạo 1 Quiz
        test_quiz = Quiz(host_id=test_user.id, title="Quiz Demo Realtime", description="Test cho Sprint 4", is_public=True)
        db.add(test_quiz)
        db.flush()

        # 3. Tạo 1 câu hỏi True/False
        tf_question = Question(quiz_id=test_quiz.id, question_text="1 + 1 = 3?", question_type=QuestionType.true_false)
        db.add(tf_question)
        db.flush()

        # 4. Tạo Options cho câu hỏi
        db.add(QuestionOption(question_id=tf_question.id, option_text="True", is_correct=False))
        db.add(QuestionOption(question_id=tf_question.id, option_text="False", is_correct=True))

        db.commit()
        print("✅ Seed dữ liệu thành công! Đã có sẵn 1 User, 1 Quiz và 1 Câu hỏi.")
    except Exception as e:
        print("❌ Lỗi khi seed data:", e)
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    seed_data()