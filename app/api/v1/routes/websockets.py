# app/api/v1/routes/websockets.py
from typing import Dict, List, Any
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query, Depends, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.user import User
from app.core.security import decode_access_token 

# [THÊM IMPORT CHO SPRINT 4]
from app.models.room import GameRoom, RoomPlayer
from app.models.game_session import GameSession
from app.models.player_answer import PlayerAnswer
from app.models.question import QuestionOption
import time

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
            message = {"event": "room_state", "data": {"players": players_list}}
            
            # [ĐÃ FIX LỖI 500] Dùng list() copy mảng và bọc try...except để bỏ qua các client đã disconnect
            for connection in list(self.active_connections[room_code]):
                try:
                    await connection["ws"].send_json(message)
                except Exception:
                    self.disconnect(connection["ws"], room_code)

    # [THÊM MỚI Ở SPRINT 4] Hàm broadcast event chung (ví dụ: game_started)
    async def broadcast_to_room(self, room_code: str, message: dict):
        if room_code in self.active_connections:
            # [ĐÃ FIX LỖI 500] Dùng list() và bọc try...except
            for connection in list(self.active_connections[room_code]):
                try:
                    await connection["ws"].send_json(message)
                except Exception:
                    self.disconnect(connection["ws"], room_code)

manager = ConnectionManager()

# --- 2. WEBSOCKET ENDPOINT ---
@router.websocket("/ws/rooms/{room_code}")
async def room_lobby_websocket(
    websocket: WebSocket,
    room_code: str,
    token: str = Query(...), 
    db: Session = Depends(get_db)
):
    # Xác thực Token
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
            # [SỬA LẠI Ở SPRINT 4] Chuyển thành receive_json để nhận Event Payload
            data = await websocket.receive_json()
            event = data.get("event")
            payload = data.get("payload", {})
            
            # ===============================================
            # LOGIC START GAME (Chỉ Host mới được gọi)
            # ===============================================
            if event == "start_game":
                room = db.query(GameRoom).filter(GameRoom.room_code == room_code).first()
                
                # VALIDATE 1: Bắt buộc là Host
                if not room or room.host_id != user.id:
                    continue 
                
                # Đổi trạng thái phòng
                room.status = "playing"
                
                # Tạo Session Game mới
                new_session = GameSession(
                    room_id=room.id,
                    quiz_id=room.quiz_id,
                    host_id=room.host_id
                )
                db.add(new_session)
                db.commit()
                db.refresh(new_session)
                
                # Báo cho toàn phòng biết Game đã bắt đầu (Frontend sẽ hứng event này để chuyển trang Play)
                await manager.broadcast_to_room(room_code, {
                    "event": "game_started",
                    "data": {"session_id": new_session.id}
                })

            # ===============================================
            # LOGIC SUBMIT ANSWER (Player nộp đáp án)
            # ===============================================
            elif event == "submit_answer":
                room = db.query(GameRoom).filter(GameRoom.room_code == room_code).first()
                if not room: continue
                
                question_id = payload.get("question_id")
                option_id = payload.get("selected_option_id")
                session_id = payload.get("game_session_id")
                
                # VALIDATE 1: Kiểm tra người này có thực sự trong phòng không?
                player = db.query(RoomPlayer).filter(
                    RoomPlayer.room_id == room.id,
                    RoomPlayer.user_id == user.id
                ).first()
                if not player: continue
                
                # VALIDATE 2 & 4: (Dành cho TV C - Kiểm tra index câu hỏi và Timeout từ Redis/State)
                # Tạm thời bỏ qua ở bước MVP này chờ TV C ráp Game Loop vào.
                
                # VALIDATE 3: Chống Duplicate (Check xem user đã nộp đáp án câu này chưa)
                existing_answer = db.query(PlayerAnswer).filter(
                    PlayerAnswer.game_session_id == session_id,
                    PlayerAnswer.room_player_id == player.id,
                    PlayerAnswer.question_id == question_id
                ).first()
                if existing_answer: continue
                
                # TÍNH ĐIỂM & LƯU LẠI
                option = db.query(QuestionOption).filter(QuestionOption.id == option_id).first()
                is_correct = option.is_correct if option else False
                
                new_answer = PlayerAnswer(
                    game_session_id=session_id,
                    room_player_id=player.id,
                    question_id=question_id,
                    selected_option_id=option_id,
                    is_correct=is_correct,
                    response_time_ms=2000, # (MVP gán cứng 2s, sẽ nối với time thật của TV C sau)
                    score_delta=1000 if is_correct else 0
                )
                db.add(new_answer)
                db.commit()
                
    except WebSocketDisconnect:
        manager.disconnect(websocket, room_code)
        await manager.broadcast_room_state(room_code)
    except Exception as e:
        # Bắt các lỗi JSON decode nếu có
        pass