# quizbattle-backend/app/api/v1/routes/rooms.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from pydantic import BaseModel
from app.models.room import GameRoom, RoomPlayer
from app.models.quiz import Quiz
from app.models.user import User
from app.models.question import Question
import asyncio
from app.schemas.room import RoomCreate, RoomResponse
from app.utils.room_code import generate_room_code
from app.core.security import get_current_user
from app.services.game_service import start_game_loop
from app.api.v1.routes.websockets import manager as websocket_manager

# Lược đồ dữ liệu nhận từ Player khi nhập mã Code
class RoomJoin(BaseModel):
    room_code: str

router = APIRouter(prefix="/api/v1/rooms", tags=["Rooms"])

# ==========================================
# 1. API CREATE ROOM (CỦA LEADER)
# ==========================================

# Lược đồ dữ liệu nhận từ Frontend
class RoomCreate(BaseModel):
    quiz_id: int

# Hàm sinh mã phòng ngẫu nhiên (VD: X7B9A)

@router.post("", response_model=RoomResponse)
def create_room(req: RoomCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    # 1. Kiểm tra Quiz có tồn tại không
    quiz = db.query(Quiz).filter(Quiz.id == req.quiz_id).first()
    if not quiz:
        raise HTTPException(status_code=404, detail="Không tìm thấy Quiz")
    question_count = db.query(Question).filter(Question.quiz_id == quiz.id).count()
    if question_count == 0:
        raise HTTPException(status_code=400, detail="Quiz chưa có câu hỏi nào! Không thể tạo phòng.")
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
        display_name=getattr(current_user, 'username', None) or current_user.email.split("@")[0],
        is_connected=True
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

# ==========================================
# 2. API JOIN ROOM (CỦA MEMBER B)
# ==========================================
@router.post("/join")
def join_room(req: RoomJoin, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    # 1. Ép mã phòng viết hoa để query DB chuẩn xác nhất
    upper_room_code = req.room_code.strip().upper()

    # 2. Kiểm tra phòng có tồn tại không
    room = db.query(GameRoom).filter(GameRoom.room_code == upper_room_code).first()
    if not room:
        raise HTTPException(status_code=404, detail="Mã phòng không tồn tại. Vui lòng kiểm tra lại!")
    
    # 3. Kiểm tra trạng thái (Chỉ cho join khi đang waiting)
    if room.status.value != "waiting":
        raise HTTPException(status_code=400, detail="Phòng đang chơi hoặc đã kết thúc. Không thể tham gia!")
        
    # 4. Kiểm tra xem player đã ở trong phòng chưa (tránh duplicate)
    existing_player = db.query(RoomPlayer).filter(
        RoomPlayer.room_id == room.id,
        RoomPlayer.user_id == current_user.id
    ).first()
    
    # 5. Nếu chưa có thì thêm player vào phòng
    if not existing_player:
        new_player = RoomPlayer(
            room_id=room.id,
            user_id=current_user.id,
            display_name=getattr(current_user, 'username', None) or current_user.email.split("@")[0],
            is_connected=True
        )
        db.add(new_player)
        db.commit()
        
    return {
        "success": True,
        "data": {"room_code": room.room_code},
        "message": "Tham gia phòng thành công"
    }

@router.post("/{room_code}/start")
async def start_game(room_code: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    room = db.query(GameRoom).filter(GameRoom.room_code == room_code).first()
    
    # Validation: Chỉ host mới được start game
    if not room or room.host_id != current_user.id:
        raise HTTPException(status_code=403, detail="Bạn không có quyền bắt đầu game này")

    # Đánh dấu game bắt đầu
    room.status = "playing"
    room.current_question_index = 0
    db.commit()

    # Kích hoạt Trọng tài ảo chạy ngầm (Non-blocking)
    asyncio.create_task(start_game_loop(room_code, websocket_manager))

    return {"success": True, "message": "Game started!"}
