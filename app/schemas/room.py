# quizbattle-backend/app/schemas/room.py
from pydantic import BaseModel
from typing import Optional

class RoomCreate(BaseModel):
    quiz_id: int

class RoomResponseData(BaseModel):
    room_code: str
    quiz_id: int
    host_id: int
    status: str

class RoomResponse(BaseModel):
    success: bool
    data: RoomResponseData
    message: str