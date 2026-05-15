from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import desc
from app.db.session import get_db
# Thay đổi đường dẫn import User/get_current_user theo đúng cấu trúc file của team bạn
from app.models.user import User
from app.api.v1.routes.auth import get_current_user 
from app.models.room import GameRoom, RoomPlayer
from app.models.game_session import GameSession

router = APIRouter()

@router.get("/{session_id}/result")
def get_final_result(session_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
  """
    API lấy bảng xếp hạng chung cuộc của một lượt chơi. Yêu cầu đăng nhập.
  """
  # 1. Tìm game_session
  game_session = db.query(GameSession).filter(GameSession.id == session_id).first()
  if not game_session:
      raise HTTPException(status_code=404, detail="Không tìm thấy phiên chơi này!")

  # 2. Tìm room tương ứng
  room = db.query(GameRoom).filter(GameRoom.id == game_session.room_id).first()
  if not room:
      raise HTTPException(status_code=404, detail="Không tìm thấy phòng chơi liên kết!")
  # 3. Truy vấn bảng room_players và sắp xếp theo score giảm dần để tạo Leaderboard
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