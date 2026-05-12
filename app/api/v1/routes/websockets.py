from typing import Dict, List, Any
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query, Depends, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.user import User
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
            # Tạm thời chưa cần nhận data gì từ client, chỉ lắng nghe
            data = await websocket.receive_text()
            
    except WebSocketDisconnect:
        # Có người tắt tab hoặc mất mạng -> Xóa khỏi list và báo cho cả phòng
        manager.disconnect(websocket, room_code)
        await manager.broadcast_room_state(room_code)