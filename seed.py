# quizbattle-backend/seed.py
from app.db.session import SessionLocal
from app.models.user import User
from app.models.quiz import Quiz
from app.models.question import Question, QuestionOption, QuestionType
from app.core.security import get_password_hash 

def seed_data():
    db = SessionLocal()
    try:
        # 1. Tạo 1 User test
        test_user = User(username="host1", email="host@test.com", password_hash=get_password_hash("password123"))
        db.add(test_user)
        db.flush()

        # 2. Tạo 1 Quiz (ĐÃ SỬA host_id THÀNH owner_id)
        test_quiz = Quiz(owner_id=test_user.id, title="Quiz Lập trình Python & Next.js", description="Bộ câu hỏi test data Sprint 2", is_public=True)
        db.add(test_quiz)
        db.flush()

        # 3. Tạo 5 câu hỏi theo đúng yêu cầu SRS
        questions_data = [
            {
                "text": "1 + 1 = 3?",
                "type": QuestionType.true_false,
                "options": [("True", False), ("False", True)]
            },
            {
                "text": "FastAPI được viết bằng ngôn ngữ nào?",
                "type": QuestionType.multiple_choice,
                "options": [("Python", True), ("Java", False), ("C#", False), ("JavaScript", False)]
            },
            {
                "text": "Trái Đất hình vuông đúng hay sai?",
                "type": QuestionType.true_false,
                "options": [("True", False), ("False", True)]
            },
            {
                "text": "Next.js là framework của library nào?",
                "type": QuestionType.multiple_choice,
                "options": [("Vue", False), ("Angular", False), ("React", True), ("Svelte", False)]
            },
            {
                "text": "Lệnh nào dùng để push code lên GitHub?",
                "type": QuestionType.multiple_choice,
                "options": [("git pull", False), ("git push", True), ("git clone", False), ("git commit", False)]
            }
        ]

        # Vòng lặp insert 5 câu hỏi và các đáp án
        for idx, q_data in enumerate(questions_data):
            q = Question(quiz_id=test_quiz.id, question_text=q_data["text"], question_type=q_data["type"], order_index=idx+1)
            db.add(q)
            db.flush()
            
            for o_idx, (opt_text, is_correct) in enumerate(q_data["options"]):
                opt = QuestionOption(question_id=q.id, option_text=opt_text, is_correct=is_correct, order_index=o_idx+1)
                db.add(opt)

        db.commit()
        print("✅ Seed dữ liệu thành công! Đã có sẵn 1 User (host@test.com / password123), 1 Quiz và 5 Câu hỏi.")
    except Exception as e:
        print("❌ Lỗi khi seed data:", e)
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    seed_data()