# quizbattle-backend/app/api/v1/routes/rooms.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.session import get_db

from app.models.room import GameRoom, RoomPlayer
from app.models.quiz import Quiz
from app.models.user import User

from app.schemas.room import RoomCreate, RoomResponse
from app.utils.room_code import generate_room_code
from app.core.security import get_current_user

router = APIRouter(prefix="/api/v1/rooms", tags=["Rooms"])

@router.post("", response_model=RoomResponse)
def create_room(req: RoomCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    # 1. Kiểm tra Quiz có tồn tại không
    quiz = db.query(Quiz).filter(Quiz.id == req.quiz_id).first()
    if not quiz:
        raise HTTPException(status_code=404, detail="Không tìm thấy Quiz")
    
    # 2. Sinh mã phòng (đảm bảo không trùng)
    while True:
        code = generate_room_code()
        existing_room = db.query(GameRoom).filter(GameRoom.room_code == code).first()
        if not existing_room:
            break
            
    # 3. Tạo GameRoom mới (status mặc định là waiting)
    new_room = GameRoom(
        room_code=code,
        host_id=current_user.id,
        quiz_id=req.quiz_id
    )
    db.add(new_room)
    db.flush() # Lấy ID phòng ngay lập tức

    # 4. Thêm Host vào bảng room_players
    host_player = RoomPlayer(
        room_id=new_room.id,
        user_id=current_user.id,
        display_name=current_user.username # Lấy username làm tên hiển thị
    )
    db.add(host_player)
    db.commit()

    return {
        "success": True,
        "data": {
            "room_code": new_room.room_code,
            "quiz_id": new_room.quiz_id,
            "host_id": new_room.host_id,
            "status": new_room.status.value
        },
        "message": "Tạo phòng thành công"
    }