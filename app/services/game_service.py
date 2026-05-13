import asyncio
from datetime import datetime, timezone
# Giả định bạn import SessionLocal từ cấu hình DB của team
from app.db.session import SessionLocal 
from app.models.room import GameRoom
from app.models.quiz import Quiz
from app.models.question import Question, QuestionOption

async def start_game_loop(room_code: str, websocket_manager):
    """
    Trọng tài ảo: Background task điều phối vòng lặp game.
    """
    # Mở một DB Session độc lập cho background task
    db = SessionLocal()
    
    try:
        await websocket_manager.broadcast_to_room(room_code, {
            "type": "game_started",
            "payload": {"message": "Game chuẩn bị bắt đầu!"}
        })
        
        # 2. Bắt Server ĐỢI 3 GIÂY để Frontend có thời gian load trang và nối lại WebSocket
        await asyncio.sleep(3)

        while True:
            # 1. Lấy trạng thái phòng mới nhất
            room = db.query(GameRoom).filter(GameRoom.room_code == room_code).first()
            if not room or room.status.value != "playing":
                break

            quiz = db.query(Quiz).filter(Quiz.id == room.quiz_id).first()
            questions = db.query(Question).filter(Question.quiz_id == quiz.id).order_by(Question.order_index).all()

            # KẾT THÚC GAME: Nếu đã chạy hết câu hỏi [cite: 463]
            if room.current_question_index >= len(questions):
                room.status = "finished" 
                db.commit()

                # Broadcast sự kiện kết thúc [cite: 263, 463]
                await websocket_manager.broadcast_to_room(room_code, {
                    "type": "game_finished",
                    "payload": {"message": "Trò chơi đã kết thúc!"}
                })
                break

            current_question = questions[room.current_question_index]
            options = db.query(QuestionOption).filter(QuestionOption.question_id == current_question.id).all()

            # ==========================================
            # BƯỚC 1: BẮN SỰ KIỆN "QUESTION STARTED"
            # ==========================================
            # BẢO MẬT CHẶT CHẼ: Xóa trường is_correct để chống cheat qua DevTools [cite: 429, 473]
            safe_options = [
                {"id": opt.id, "text": opt.option_text} for opt in options
            ]

            server_started_at = datetime.now(timezone.utc)
            time_limit = current_question.time_limit_seconds
            # Nếu DB vô tình lưu là 0 hoặc Null, ép về mặc định 20 giây
            if not time_limit or time_limit <= 0:
                time_limit = 20

            question_payload = {
                "type": "question_started",
                "payload": {
                    "question_id": current_question.id,
                    "question_text": current_question.question_text,
                    "options": safe_options,
                    "time_limit_seconds": current_question.time_limit_seconds,
                    "server_started_at": server_started_at.isoformat()
                }
            }

            await websocket_manager.broadcast_to_room(room_code, question_payload)

            # ==========================================
            # BƯỚC 2: AUTO TIMEOUT (ĐẾM GIỜ NGẦM)
            # ==========================================
            # Server chủ động dừng task lại để chờ người chơi submit [cite: 459]
            await asyncio.sleep(current_question.time_limit_seconds)

            # ==========================================
            # BƯỚC 3: AUTO NEXT QUESTION (CHỐT CÂU HỎI)
            # ==========================================
            # Hết giờ, tính toán và gửi đáp án đúng xuống Client [cite: 460, 461]
            correct_option_ids = [opt.id for opt in options if opt.is_correct]

            result_payload = {
                "type": "question_result",
                "payload": {
                    "question_id": current_question.id,
                    "correct_option_ids": correct_option_ids
                }
            }
            await websocket_manager.broadcast_to_room(room_code, result_payload)

            # (Ở đây bạn có thể chèn hàm broadcast leaderboard_updated nếu đã làm xong chức năng chấm điểm)

            # Dừng 3 giây để Frontend hiển thị hiệu ứng Xanh/Đỏ [cite: 462]
            await asyncio.sleep(3)

            # Tăng index câu hỏi lên 1 và lưu vào DB
            room.current_question_index += 1
            db.commit()

            # Vòng lặp while sẽ tự động quay lại đầu để phát câu hỏi tiếp theo
            
    finally:
        # Đảm bảo luôn đóng DB session khi task ngầm kết thúc để tránh leak connection
        db.close()