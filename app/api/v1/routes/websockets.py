# app/api/v1/routes/websockets.py
import asyncio
from typing import Dict, List, Any
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query, Depends, status
from sqlalchemy.orm import Session
from app.db.session import get_db, SessionLocal
from app.models.user import User
from app.core.security import decode_access_token 

from app.models.room import GameRoom, RoomPlayer
from app.models.question import QuestionOption

# ==========================================
# [ĐÃ FIX LỖI IMPORT]: Tách riêng 2 đường dẫn
# ==========================================
from app.models.game_session import GameSession
from app.models.player_answer import PlayerAnswer

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
            message = {"event": "room_state", "data": {"players": players_list}}
            
            for connection in list(self.active_connections[room_code]):
                try:
                    await connection["ws"].send_json(message)
                except Exception:
                    self.disconnect(connection["ws"], room_code)

    async def broadcast_to_room(self, room_code: str, message: dict):
        if room_code in self.active_connections:
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
            data = await websocket.receive_json()
            event = data.get("event") or data.get("type")
            payload = data.get("payload", {})
            
            # ===============================================
            # LOGIC START GAME (CỦA LEADER)
            # ===============================================
            if event == "start_game":
                room = db.query(GameRoom).filter(GameRoom.room_code == room_code).first()
                
                # Chỉ Host mới được start
                if not room or room.host_id != user.id:
                    continue 
                
                room.status = "playing"
                room.current_question_index = 0
                
                new_session = GameSession(
                    room_id=room.id,
                    quiz_id=room.quiz_id,
                    host_id=room.host_id
                )
                db.add(new_session)
                db.commit()
                db.refresh(new_session)
                
                # Báo cho Frontend chuyển trang
                await manager.broadcast_to_room(room_code, {
                    "event": "game_started",
                    "data": {"session_id": new_session.id}
                })

                # GỌI TRỌNG TÀI ẢO CỦA MEMBER C
                asyncio.create_task(start_game_loop(room_code, manager))

            # ===============================================
            # LOGIC SUBMIT ANSWER (CỦA LEADER)
            # ===============================================
            elif event == "submit_answer":
                db_local = SessionLocal()
                try:
                    room = db_local.query(GameRoom).filter(GameRoom.room_code == room_code).first()
                    if not room: continue
                    
                    question_id = payload.get("question_id")
                    option_id = payload.get("selected_option_id")
                    session_id = payload.get("game_session_id")
                    response_time_ms = payload.get("response_time_ms", 2000)
                    
                    # VALIDATE 1: Kiểm tra người này có thực sự trong phòng không?
                    player = db_local.query(RoomPlayer).filter(
                        RoomPlayer.room_id == room.id,
                        RoomPlayer.user_id == user.id
                    ).first()
                    if not player: continue
                    
                    # VALIDATE 3: Chống Duplicate
                    existing_answer = db_local.query(PlayerAnswer).filter(
                        PlayerAnswer.game_session_id == session_id,
                        PlayerAnswer.room_player_id == player.id,
                        PlayerAnswer.question_id == question_id
                    ).first()
                    if existing_answer: continue
                    
                    # TÍNH ĐIỂM & LƯU LẠI
                    option = db_local.query(QuestionOption).filter(QuestionOption.id == option_id).first()
                    is_correct = option.is_correct if option else False
                    
                    score_delta = 0
                    if is_correct:
                        raw_score = 1000 - int(response_time_ms / 100)
                        score_delta = max(100, raw_score)

                    new_answer = PlayerAnswer(
                        game_session_id=session_id,
                        room_player_id=player.id,
                        question_id=question_id,
                        selected_option_id=option_id,
                        is_correct=is_correct,
                        response_time_ms=response_time_ms,
                        score_delta=score_delta
                    )
                    db_local.add(new_answer)

                    # Cộng điểm vào tài khoản RoomPlayer
                    if score_delta > 0:
                        player.score = (player.score or 0) + score_delta

                    db_local.commit()
                except Exception as e:
                    db_local.rollback()
                finally:
                    db_local.close()
                
    except WebSocketDisconnect:
        manager.disconnect(websocket, room_code)
        await manager.broadcast_room_state(room_code)
    except Exception:
        pass