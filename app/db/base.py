# quizbattle-backend/app/db/base.py
from sqlalchemy.orm import declarative_base

# 1. KHỞI TẠO BIẾN BASE ĐẦU TIÊN
Base = declarative_base()

# 2. SAU KHI BASE ĐÃ ĐƯỢC TẠO XONG, MỚI IMPORT TẤT CẢ CÁC MODELS Ở DƯỚI CÙNG
from app.models.user import User
from app.models.quiz import Quiz
from app.models.question import Question, QuestionOption
from app.models.room import GameRoom, RoomPlayer 

# [THÊM MỚI Ở SPRINT 4]
from app.models.game_session import GameSession
from app.models.player_answer import PlayerAnswer