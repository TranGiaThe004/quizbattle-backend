import os
import hashlib
import bcrypt  # SỬ DỤNG TRỰC TIẾP BCRYPT, BỎ PASSLIB
from datetime import datetime, timedelta
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.user import User


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

SECRET_KEY = os.getenv("SECRET_KEY", "quizbattle_secret_key_2026")
ALGORITHM = os.getenv("ALGORITHM", "HS256")


def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Token không hợp lệ hoặc đã hết hạn",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    user = db.query(User).filter(User.id == int(user_id)).first()
    if user is None:
        raise credentials_exception
    return user


def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta if expires_delta else timedelta(minutes=15))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

# Thời gian sống token
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7


def create_refresh_token(data: dict):
    to_encode = data.copy()

    expire = datetime.utcnow() + timedelta(
        days=REFRESH_TOKEN_EXPIRE_DAYS
    )

    to_encode.update({
        "exp": expire,
        "type": "refresh"
    })

    return jwt.encode(
        to_encode,
        SECRET_KEY,
        algorithm=ALGORITHM
    )

# --- HÀM BĂM TOKEN CỦA TV C ---
def get_token_hash(token: str) -> str:
    """Băm token bằng thuật toán SHA-256 để lưu vào database."""
    return hashlib.sha256(token.encode()).hexdigest()

# =====================================================================
# --- HÀM XỬ LÝ MẬT KHẨU MỚI (KHÔNG DÙNG PASSLIB) ---
# =====================================================================

def get_password_hash(password: str) -> str:
    """Mã hóa mật khẩu bằng bcrypt trực tiếp."""
    # Chuyển string thành byte
    pwd_bytes = password.encode('utf-8')
    # Tạo chuỗi muối (salt)
    salt = bcrypt.gensalt()
    # Băm mật khẩu
    hashed_password = bcrypt.hashpw(password=pwd_bytes, salt=salt)
    # Chuyển byte thành string để lưu vào DB
    return hashed_password.decode('utf-8')

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Hàm này sẽ dùng cho bạn Huy (Member B) làm Login sau này"""
    password_byte_enc = plain_password.encode('utf-8')
    hashed_password_byte_enc = hashed_password.encode('utf-8')
    return bcrypt.checkpw(password=password_byte_enc, hashed_password=hashed_password_byte_enc)

