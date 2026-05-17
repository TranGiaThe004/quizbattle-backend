# app/api/v1/routes/websockets.py
import asyncio
from typing import Dict, List, Any
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query, Depends, status
from sqlalchemy.orm import Session
from app.db.session import get_db, SessionLocal
from app.models.user import User
import json
from app.models.room import GameRoom, RoomPlayer
from app.models.question import QuestionOption
from app.models.game_session import GameSession, PlayerAnswer
from app.core.security import decode_access_token 

# Import Game Loop của Member C
from app.services.game_service import start_game_loop

router = APIRouter()

# --- 1. CLASS CONNECTION MANAGER ---
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, List[Dict[str, Any]]] = {}

    async def connect(self, websocket: WebSocket, room_code: str, user_data: dict):
        await websocket.accept()
        if room_code not in self.active_connections:
            self.active_connections[room_code] = []
        self.active_connections[room_code].append({"ws": websocket, "user": user_data})

    def disconnect(self, websocket: WebSocket, room_code: str):
        if room_code in self.active_connections:
            self.active_connections[room_code] = [
                conn for conn in self.active_connections[room_code] if conn["ws"] != websocket
            ]
            if not self.active_connections[room_code]:
                del self.active_connections[room_code]

    async def broadcast_room_state(self, room_code: str):
        if room_code in self.active_connections:
            unique_players = {}
            for connection in self.active_connections[room_code]:
                user_data = connection.get("user")
                if user_data:
                    unique_players[user_data["id"]] = user_data

            players_list = list(unique_players.values())
            # CHUẨN ĐANG DÙNG LÀ event VÀ data
            message = {"event": "room_state", "data": {"players": players_list}}
            
            dead_connections = []
            for connection in self.active_connections[room_code]:
                try:
                    await connection["ws"].send_json(message)
                except Exception:
                    dead_connections.append(connection["ws"])
            
            for dead_ws in dead_connections:
                self.disconnect(dead_ws, room_code)

    async def broadcast_to_room(self, room_code: str, message: dict):
        """
        Gửi thông điệp tới toàn bộ phòng và tự động dọn dẹp các kết nối đứt.
        """
        if room_code in self.active_connections:
            dead_connections = []
            
            for connection in self.active_connections[room_code]:
                try:
                    ws = connection.get("ws") if isinstance(connection, dict) else connection
                    await ws.send_json(message)
                except Exception as e:
                    dead_connections.append(connection)
            
            for dead in dead_connections:
                try:
                    self.active_connections[room_code].remove(dead)
                except ValueError:
                    pass

    async def handle_client_message(self, room_code: str, user_id: int, message: dict):
        """
        Hàm xử lý TẤT CẢ các sự kiện gửi từ Client lên Server
        """
        # Hứng từ khóa 'event' và 'data' cho đồng bộ với lúc gửi xuống
        event_type = message.get("event")
        payload_data = message.get("data", {})

        # --- LOGIC 1: CHẤM ĐIỂM (CŨ) ---
        if event_type == "submit_answer":
            db = SessionLocal()
            try:
                question_id = payload_data.get("question_id")
                selected_option_id = payload_data.get("selected_option_id")
                response_time_ms = payload_data.get("response_time_ms", 0)

                room = db.query(GameRoom).filter(GameRoom.room_code == room_code).first()
                player = db.query(RoomPlayer).filter(
                    RoomPlayer.room_id == room.id, 
                    RoomPlayer.user_id == user_id
                ).first()
                
                game_session = db.query(GameSession).filter(GameSession.room_id == room.id).order_by(GameSession.id.desc()).first()

                if not room or not player or not game_session:
                    return

                existing_answer = db.query(PlayerAnswer).filter(
                    PlayerAnswer.game_session_id == game_session.id,
                    PlayerAnswer.room_player_id == player.id,
                    PlayerAnswer.question_id == question_id
                ).first()

                if existing_answer:
                    return 

                selected_option = db.query(QuestionOption).filter(QuestionOption.id == selected_option_id).first()
                is_correct = selected_option.is_correct if selected_option else False
                score_delta = 0

                if is_correct:
                    raw_score = 1000 - int(response_time_ms / 100)
                    score_delta = max(100, raw_score)

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

                if score_delta > 0:
                    player.score += score_delta
                
                db.commit()

            except Exception as e:
                print(f"Lỗi khi xử lý submit_answer: {e}")
                db.rollback()
            finally:
                db.close()

        # --- LOGIC 2: CHAT REALTIME (ĐÃ CHUYỂN VÀO ĐÂY) ---
        elif event_type == "send_chat":
            message_text = payload_data.get("message", "").strip()
            
            if message_text:
                # Tìm tên của người gửi (Lấy từ danh sách kết nối hiện tại cho nhanh, khỏi query DB)
                display_name = "Player"
                if room_code in self.active_connections:
                    for conn in self.active_connections[room_code]:
                        if conn["user"]["id"] == user_id:
                            display_name = conn["user"]["name"]
                            break

                # Đóng gói tin nhắn theo chuẩn event/data để gửi đi
                broadcast_event = {
                    "event": "chat_message",
                    "data": {
                        "user_id": user_id,
                        "display_name": display_name,
                        "message": message_text
                    }
                }
                
                print(f"🚀 [Chat] {display_name} -> {room_code}: {message_text}")
                await self.broadcast_to_room(room_code, broadcast_event)


manager = ConnectionManager()

# --- 2. WEBSOCKET ENDPOINT ---
@router.websocket("/ws/rooms/{room_code}")
async def room_lobby_websocket(
    websocket: WebSocket,
    room_code: str,
    token: str = Query(...), 
    db: Session = Depends(get_db)
):
    try:
        payload = decode_access_token(token)
        user_id = int(payload.get("sub"))
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise ValueError("User not found")
    except Exception:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    user_data = {
        "id": user.id,
        "name": getattr(user, 'username', None) or user.email.split("@")[0],
    }

    await manager.connect(websocket, room_code, user_data)
    await manager.broadcast_room_state(room_code)

    try:
        while True:
            # Chờ nhận tin nhắn JSON từ Client 
            data = await websocket.receive_json()
            
            # Đẩy toàn bộ dữ liệu vào hàm xử lý
            await manager.handle_client_message(room_code, user_id, data)
                
    except WebSocketDisconnect:
        manager.disconnect(websocket, room_code)
        if room_code in manager.active_connections:
            await manager.broadcast_room_state(room_code)
    except Exception as e:
        print(f"Lỗi WebSocket Endpoint: {e}")