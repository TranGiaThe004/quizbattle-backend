# quizbattle-backend/app/utils/room_code.py
import random
import string

def generate_room_code(length: int = 6) -> str:
    """Sinh mã phòng ngẫu nhiên gồm chữ cái in hoa và số"""
    characters = string.ascii_uppercase + string.digits
    return ''.join(random.choices(characters, k=length))