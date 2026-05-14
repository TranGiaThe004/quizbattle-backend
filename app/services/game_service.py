# app/services/game_service.py
import asyncio
from datetime import datetime, timezone
from app.db.session import SessionLocal 
from app.models.room import GameRoom
from app.models.quiz import Quiz
from app.models.question import Question, QuestionOption

# [THÊM Ở SPRINT 5]: Import model GameSession để cập nhật thời gian kết thúc
from app.models.game_session import GameSession 

async def start_game_loop(room_code: str, websocket_manager):
    """
    Trọng tài ảo: Background task điều phối vòng lặp game.
    """
    # Mở DB Session độc lập cho task ngầm
    db = SessionLocal()
    
    try:
        # Chờ 3 giây đầu game để mọi Frontend kịp load sang trang Play
        await asyncio.sleep(3)

        while True:
            # 1. Lấy trạng thái phòng mới nhất
            room = db.query(GameRoom).filter(GameRoom.room_code == room_code).first()
            if not room or room.status.value != "playing":
                break

            quiz = db.query(Quiz).filter(Quiz.id == room.quiz_id).first()
            questions = db.query(Question).filter(Question.quiz_id == quiz.id).order_by(Question.order_index).all()

            # =========================================================
            # [SPRINT 5 - TASK TTGT-75 CỦA LEADER]: XỬ LÝ KẾT THÚC GAME
            # =========================================================
            if room.current_question_index >= len(questions):
                # 1. Đổi trạng thái phòng thành finished để khóa join/submit
                room.status = "finished" 
                
                # 2. Tìm Game Session hiện tại và cập nhật thời gian kết thúc
                game_session = db.query(GameSession).filter(
                    GameSession.room_id == room.id
                ).order_by(GameSession.id.desc()).first()
                
                session_id = None
                if game_session:
                    game_session.ended_at = datetime.now(timezone.utc)
                    session_id = game_session.id
                
                # Lưu thay đổi xuống Database
                db.commit()
                
                # 3. Broadcast sự kiện game_finished kèm session_id
                await websocket_manager.broadcast_to_room(room_code, {
                    "event": "game_finished",
                    "payload": {
                        "message": "Trò chơi đã kết thúc!",
                        "session_id": session_id # Rất quan trọng để TV B và C gọi API
                    }
                })
                break
            # =========================================================

            current_question = questions[room.current_question_index]
            options = db.query(QuestionOption).filter(QuestionOption.question_id == current_question.id).all()

            # ==========================================
            # BƯỚC 1: BẮN SỰ KIỆN "QUESTION STARTED"
            # ==========================================
            safe_options = [
                {"id": opt.id, "text": opt.option_text} for opt in options
            ]

            server_started_at = datetime.now(timezone.utc)
            time_limit = current_question.time_limit_seconds
            if not time_limit or time_limit <= 0:
                time_limit = 20 # Mặc định nếu bị Null

            question_payload = {
                "event": "question_started",
                "payload": {
                    "question_id": current_question.id,
                    "question_text": current_question.question_text,
                    "options": safe_options,
                    "time_limit_seconds": time_limit,
                    "server_started_at": server_started_at.isoformat()
                }
            }

            await websocket_manager.broadcast_to_room(room_code, question_payload)

            # ==========================================
            # BƯỚC 2: AUTO TIMEOUT (ĐẾM GIỜ NGẦM)
            # ==========================================
            await asyncio.sleep(time_limit)

            # ==========================================
            # BƯỚC 3: AUTO NEXT QUESTION (CHỐT CÂU HỎI)
            # ==========================================
            correct_option_ids = [opt.id for opt in options if opt.is_correct]

            result_payload = {
                "event": "question_result",
                "payload": {
                    "question_id": current_question.id,
                    "correct_option_ids": correct_option_ids
                }
            }
            await websocket_manager.broadcast_to_room(room_code, result_payload)

            # Chờ Frontend hiển thị kết quả Xanh/Đỏ và Live Leaderboard trong 3 giây
            await asyncio.sleep(3)

            # Tăng index câu hỏi, lặp lại cho câu tiếp theo
            room.current_question_index += 1
            db.commit()

    except Exception as e:
        print(f"Lỗi Game Loop phòng {room_code}: {e}")
    finally:
        db.close()