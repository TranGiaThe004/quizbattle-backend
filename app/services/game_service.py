# app/services/game_service.py
import asyncio
from datetime import datetime, timezone
# Giả định bạn import SessionLocal từ cấu hình DB của team
from app.db.session import SessionLocal 
from app.models.room import GameRoom,RoomPlayer
from app.models.quiz import Quiz
from app.models.question import Question, QuestionOption
from sqlalchemy import desc

async def start_game_loop(room_code: str, websocket_manager):
    """
    Trọng tài ảo: Background task điều phối vòng lặp game.
    """
    # Mở một DB Session độc lập cho background task
    db = SessionLocal()
    
    try:
        # [ĐÃ SỬA]: Đổi "type" thành "event"
        await websocket_manager.broadcast_to_room(room_code, {
            "event": "game_started",
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

            # KẾT THÚC GAME: Nếu đã chạy hết câu hỏi
            if room.current_question_index >= len(questions):
                room.status = "finished" 
                
                # ==========================================
                # SPRINT 5: LẤY SESSION_ID ĐỂ GỬI CHO FRONTEND
                # ==========================================
                from app.models.game_session import GameSession
                game_session = db.query(GameSession).filter(GameSession.room_id == room.id).order_by(GameSession.id.desc()).first()
                
                db.commit()

                # Broadcast sự kiện kết thúc kèm session_id
                # [ĐÃ SỬA]: Đổi "type" thành "event"
                await websocket_manager.broadcast_to_room(room_code, {
                    "event": "game_finished",
                    "payload": {
                        "message": "Trò chơi đã kết thúc!",
                        "session_id": game_session.id if game_session else None
                    }
                })
                break

            current_question = questions[room.current_question_index]
            options = db.query(QuestionOption).filter(QuestionOption.question_id == current_question.id).all()

            # ==========================================
            # BƯỚC 1: BẮN SỰ KIỆN "QUESTION STARTED"
            # ==========================================
            # BẢO MẬT CHẶT CHẼ: Xóa trường is_correct để chống cheat qua DevTools
            safe_options = [
                {"id": opt.id, "text": opt.option_text} for opt in options
            ]

            server_started_at = datetime.now(timezone.utc)
            time_limit = current_question.time_limit_seconds
            # Nếu DB vô tình lưu là 0 hoặc Null, ép về mặc định 20 giây
            if not time_limit or time_limit <= 0:
                time_limit = 20

            question_payload = {
                # [ĐÃ SỬA]: Đổi "type" thành "event"
                "event": "question_started",
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
            # Server chủ động dừng task lại để chờ người chơi submit
            await asyncio.sleep(current_question.time_limit_seconds)

            # ==========================================
            # BƯỚC 3: AUTO NEXT QUESTION (CHỐT CÂU HỎI)
            # ==========================================
            # Hết giờ, tính toán và gửi đáp án đúng xuống Client
            correct_option_ids = [opt.id for opt in options if opt.is_correct]

            result_payload = {
                # [ĐÃ SỬA]: Đổi "type" thành "event"
                "event": "question_result",
                "payload": {
                    "question_id": current_question.id,
                    "correct_option_ids": correct_option_ids
                }
            }
            await websocket_manager.broadcast_to_room(room_code, result_payload)

            players = db.query(RoomPlayer).filter(RoomPlayer.room_id == room.id).order_by(desc(RoomPlayer.score)).all()
            leaderboard_data = [
                {
                    "user_id": p.user_id,
                    "display_name": p.display_name,
                    "score": p.score
                } for p in players
            ]
            
            # 3. Phát sự kiện leaderboard_updated cho toàn phòng
            # [ĐÃ SỬA]: Đổi "type" thành "event" và đẩy trực tiếp mảng leaderboard_data vào payload
            await websocket_manager.broadcast_to_room(room_code, {
                "event": "leaderboard_updated",
                "payload": leaderboard_data
            })

            is_last_question = (room.current_question_index == len(questions) - 1)
            if is_last_question:
                await websocket_manager.broadcast_to_room(room_code, {
                    "event": "last_question_warning", 
                    "data": {}
                })

            # Dừng 3 giây để Frontend hiển thị hiệu ứng Xanh/Đỏ
            await asyncio.sleep(8)

            # Tăng index câu hỏi lên 1 và lưu vào DB
            room.current_question_index += 1
            db.commit()

            # Vòng lặp while sẽ tự động quay lại đầu để phát câu hỏi tiếp theo
            
    finally:
        # Đảm bảo luôn đóng DB session khi task ngầm kết thúc để tránh leak connection
        db.close()