from typing import Dict, List, Any
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query, Depends, status
from sqlalchemy.orm import Session
from app.db.session import get_db,SessionLocal
from app.models.user import User
from app.models.room import GameRoom,RoomPlayer
from app.models.question import QuestionOption
from app.models.game_session import GameSession,PlayerAnswer
# Giả sử bạn có hàm giải mã token, nếu tên khác hãy sửa lại nhé:
from app.core.security import decode_access_token 

router = APIRouter()

# --- 1. CLASS CONNECTION MANAGER ---
class ConnectionManager:
    def __init__(self):
        # Cấu trúc: { "room_code": [ {"ws": WebSocket, "user": dict}, ... ] }
        self.active_connections: Dict[str, List[Dict[str, Any]]] = {}

    async def connect(self, websocket: WebSocket, room_code: str, user_data: dict):
        await websocket.accept()
        if room_code not in self.active_connections:
            self.active_connections[room_code] = []
            
        # Thêm người chơi vào danh sách phòng
        self.active_connections[room_code].append({
            "ws": websocket,
            "user": user_data
        })

    def disconnect(self, websocket: WebSocket, room_code: str):
        if room_code in self.active_connections:
            self.active_connections[room_code] = [
                conn for conn in self.active_connections[room_code] 
                if conn["ws"] != websocket
            ]
            # Nếu phòng trống thì dọn dẹp luôn
            if not self.active_connections[room_code]:
                del self.active_connections[room_code]

    async def broadcast_room_state(self, room_code: str):
        if room_code in self.active_connections:
            # Dùng Dictionary để lọc trùng: Mỗi user_id chỉ được lấy 1 lần
            unique_players = {}
            
            for connection in self.active_connections[room_code]:
                user_data = connection.get("user")
                if user_data:
                    # Ghi đè vào dict, trùng ID sẽ tự động bị thay thế
                    unique_players[user_data["id"]] = user_data

            # Chuyển lại thành list để gửi đi
            players_list = list(unique_players.values())

            message = {
                "event": "room_state",
                "data": {"players": players_list}
            }
            for connection in self.active_connections[room_code]:
                await connection["ws"].send_json(message)
    async def handle_client_message(self, room_code: str, user_id: int, message: dict):
        """
        Hàm xử lý các sự kiện gửi từ Client lên Server
        """
        event_type = message.get("type")
        payload = message.get("payload", {})

        if event_type == "submit_answer":
            # Mở DB Session để xử lý
            db = SessionLocal()
            try:
                question_id = payload.get("question_id")
                selected_option_id = payload.get("selected_option_id")
                response_time_ms = payload.get("response_time_ms", 0)

                # 1. Tìm thông tin phòng, player và game_session hiện tại
                room = db.query(GameRoom).filter(GameRoom.room_code == room_code).first()
                player = db.query(RoomPlayer).filter(
                    RoomPlayer.room_id == room.id, 
                    RoomPlayer.user_id == user_id
                ).first()
                
                # Giả định MVP: 1 room có 1 game_session đang active
                game_session = db.query(GameSession).filter(GameSession.room_id == room.id).order_by(GameSession.id.desc()).first()

                if not room or not player or not game_session:
                    return

                # 2. Chống Cheat: Kiểm tra xem đã trả lời câu này chưa (tránh submit nhiều lần)
                existing_answer = db.query(PlayerAnswer).filter(
                    PlayerAnswer.game_session_id == game_session.id,
                    PlayerAnswer.room_player_id == player.id,
                    PlayerAnswer.question_id == question_id
                ).first()

                if existing_answer:
                    # Gửi cảnh báo về cho client gian lận (hoặc bỏ qua)
                    return 

                # 3. Chấm điểm (Xác định đúng/sai)
                selected_option = db.query(QuestionOption).filter(QuestionOption.id == selected_option_id).first()
                
                is_correct = selected_option.is_correct if selected_option else False
                score_delta = 0

                if is_correct:
                    # Công thức tính điểm MVP chuẩn từ SRS
                    raw_score = 1000 - int(response_time_ms / 100)
                    score_delta = max(100, raw_score)

                # 4. Lưu lịch sử trả lời vào DB
                new_answer = PlayerAnswer(
                    game_session_id=game_session.id,
                    room_player_id=player.id,
                    question_id=question_id,
                    selected_option_id=selected_option_id,
                    is_correct=is_correct,
                    response_time_ms=response_time_ms,
                    score_delta=score_delta
                )
                db.add(new_answer)

                # 5. Cộng điểm trực tiếp cho Player
                if score_delta > 0:
                    player.score += score_delta
                
                db.commit()

                # (Tuỳ chọn) Xác nhận lại với client là server đã nhận đáp án
                # await self.send_personal_message({"type": "answer_received"}, websocket)

            except Exception as e:
                print(f"Lỗi khi xử lý submit_answer: {e}")
                db.rollback()
            finally:
                db.close()
    async def broadcast_to_room(self, room_code: str, message: dict):
        """
        Gửi một thông điệp (JSON) tới tất cả người chơi đang kết nối trong một phòng.
        """
        if room_code in self.active_connections:
            for connection in self.active_connections[room_code]:
                try:
                    # Truy cập vào object WebSocket để gửi dữ liệu
                    # Tùy theo cấu trúc của team bạn, nó có thể là connection["ws"] hoặc chính là connection
                    ws = connection.get("ws") if isinstance(connection, dict) else connection
                    await ws.send_json(message)
                except Exception as e:
                    print(f"Lỗi khi broadcast tới 1 client: {e}")

manager = ConnectionManager()

# --- 2. WEBSOCKET ENDPOINT ---
# Lưu ý: Trình duyệt không hỗ trợ gửi Header chuẩn trong WebSocket, 
# nên ta phải truyền token qua Query Parameter (?token=...)
@router.websocket("/ws/rooms/{room_code}")
async def room_lobby_websocket(
    websocket: WebSocket,
    room_code: str,
    token: str = Query(...), 
    db: Session = Depends(get_db)
):
    # Xác thực người dùng qua token
    try:
        payload = decode_access_token(token)
        user_id = int(payload.get("sub"))
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise ValueError("User not found")
    except Exception:
        # Đóng kết nối lập tức nếu token lởm
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    # Chuẩn bị dữ liệu user để gửi cho mọi người
    user_data = {
        "id": user.id,
        "name": getattr(user, 'username', None) or user.email.split("@")[0],
    }

    # Kết nối và thông báo cho cả phòng biết có người mới
    await manager.connect(websocket, room_code, user_data)
    await manager.broadcast_room_state(room_code)

    try:
        while True:
            # Ở Sảnh chờ (Lobby), ta chỉ cần giữ kết nối sống (keep-alive)
            # Chờ nhận tin nhắn từ Client (ví dụ Client gửi {"type": "submit_answer", "payload": {...}})
            data = await websocket.receive_json()
            
            # Đẩy vào hàm xử lý
            await manager.handle_client_message(room_code, user_id, data)
            # Tạm thời chưa cần nhận data gì từ client, chỉ lắng nghe
            data = await websocket.receive_text()
            
    except WebSocketDisconnect:
        # Có người tắt tab hoặc mất mạng -> Xóa khỏi list và báo cho cả phòng
        manager.disconnect(websocket, room_code)
        await manager.broadcast_room_state(room_code)