from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.db.session import get_db
from app.models.user import User
from app.models.room import RoomPlayer, GameRoom
from app.api.v1.routes.auth import get_current_user

router = APIRouter(prefix="/api/v1/me/statistics", tags=["Statistics"])

@router.get("")
def get_my_statistics(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """
    API lấy thống kê cá nhân: tổng trận, tổng điểm và thứ hạng trung bình.
    """
    # 1. Tổng số trận đã chơi (Dựa trên số lần xuất hiện trong bảng room_players)
    total_games = db.query(RoomPlayer).filter(RoomPlayer.user_id == current_user.id).count()

    # 2. Tổng điểm tích lũy
    total_score = db.query(func.sum(RoomPlayer.score)).filter(RoomPlayer.user_id == current_user.id).scalar() or 0

    # 3. Tính thứ hạng trung bình (Logic: Với mỗi phòng đã chơi, tìm hạng của mình rồi chia trung bình)
    # Đây là logic nâng cao giúp báo cáo của bạn chuyên nghiệp hơn
    my_rooms = db.query(RoomPlayer.room_id).filter(RoomPlayer.user_id == current_user.id).all()
    
    total_ranks = 0
    games_counted = 0

    for (r_id,) in my_rooms:
        # Lấy danh sách điểm trong phòng đó sắp xếp giảm dần
        all_players_in_room = db.query(RoomPlayer.user_id).filter(
            RoomPlayer.room_id == r_id
        ).order_by(RoomPlayer.score.desc()).all()
        
        # Tìm vị trí của mình (index + 1)
        try:
            rank = [p[0] for p in all_players_in_room].index(current_user.id) + 1
            total_ranks += rank
            games_counted += 1
        except ValueError:
            continue

    avg_rank = round(total_ranks / games_counted, 1) if games_counted > 0 else 0

    return {
        "success": True,
        "data": {
            "total_games": total_games,
            "total_score": int(total_score),
            "average_rank": avg_rank
        }
    }