from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import desc
from app.db.session import get_db
from app.models.user import User
from app.api.v1.routes.auth import get_current_user 
from app.models.room import GameRoom, RoomPlayer
from app.models.game_session import GameSession

router = APIRouter()

@router.get("/{session_id}/result")
def get_final_result(session_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """
    API lấy bảng xếp hạng chung cuộc của một lượt chơi.
    """
    # [ĐÃ FIX]: Bỏ qua session_id lỗi từ Frontend. 
    # Tự động tìm xem user này vừa tham gia phòng nào gần nhất
    player = db.query(RoomPlayer).filter(RoomPlayer.user_id == current_user.id).order_by(desc(RoomPlayer.id)).first()
    
    if not player:
        raise HTTPException(status_code=404, detail="Bạn chưa tham gia phòng chơi nào!")

    room = db.query(GameRoom).filter(GameRoom.id == player.room_id).first()
    
    # Lấy ván game mới nhất của phòng đó
    game_session = db.query(GameSession).filter(GameSession.room_id == room.id).order_by(desc(GameSession.id)).first()

    if not game_session:
        raise HTTPException(status_code=404, detail="Không tìm thấy phiên chơi này!")

    # Lấy danh sách người chơi và sắp xếp điểm từ cao xuống thấp
    players = db.query(RoomPlayer).filter(RoomPlayer.room_id == room.id).order_by(desc(RoomPlayer.score)).all()

    leaderboard = [
        {
            "user_id": p.user_id,
            "display_name": p.display_name,
            "score": p.score
        }
        for p in players
    ]

    return {
        "success": True,
        "data": {
            "session_id": game_session.id,
            "room_code": room.room_code,
            "host_id": game_session.host_id,
            "ended_at": game_session.ended_at,
            "leaderboard": leaderboard
        },
        "message": "Lấy kết quả chung cuộc thành công!"
    }