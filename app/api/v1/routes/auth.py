# quizbattle-backend/app/api/v1/routes/auth.py
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm  # <-- THÊM DÒNG NÀY
from sqlalchemy.orm import Session
from datetime import datetime, timezone
from app.db.session import get_db

# Import các Models
from app.models.token import RefreshToken
from app.models.user import User

# Import Schemas
from app.schemas.auth import (
    RefreshTokenRequest,
    LogoutRequest,
    UserCreate,
    UserResponse,
    TokenResponse
)

# Import logic Security
from app.core.security import (
    get_current_user,
    create_access_token,
    create_refresh_token,
    get_token_hash,
    get_password_hash,
    verify_password
)

router = APIRouter(prefix="/api/v1/auth", tags=["Authentication"])

# ----------------------------------------------------
# 1. API CỦA MEMBER A (REGISTER)
# ----------------------------------------------------
@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(user_in: UserCreate, db: Session = Depends(get_db)):
    # Kiểm tra Email trùng
    if db.query(User).filter(User.email == user_in.email).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email đã tồn tại."
        )
    
    # Kiểm tra Username trùng
    if db.query(User).filter(User.username == user_in.username).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tên đăng nhập đã tồn tại."
        )

    # Hash password và lưu
    hashed_password = get_password_hash(user_in.password)
    new_user = User(
        username=user_in.username,
        email=user_in.email,
        password_hash=hashed_password
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    return new_user

# ----------------------------------------------------
# 2. API CỦA TV C ĐÃ LÀM SẴN
# ----------------------------------------------------
@router.get("/me")
def get_me(current_user: User = Depends(get_current_user)):
    return {
        "success": True, 
        "data": {
            "id": current_user.id,
            "username": current_user.username,
            "email": current_user.email
        }
    }

@router.post("/refresh")
def refresh_token(req: RefreshTokenRequest, db: Session = Depends(get_db)):
    hashed_token = get_token_hash(req.refresh_token)
    db_token = db.query(RefreshToken).filter(RefreshToken.token_hash == hashed_token).first()
    if not db_token or db_token.revoked_at or db_token.expires_at < datetime.now(timezone.utc):
        raise HTTPException(status_code=401, detail="Refresh token không hợp lệ hoặc đã hết hạn")
  
    new_access_token = create_access_token(data={"sub": str(db_token.user_id)})
    return {"access_token": new_access_token, "token_type": "bearer"}

@router.post("/logout")
def logout(req: LogoutRequest, db: Session = Depends(get_db)):
    hashed_token = get_token_hash(req.refresh_token)
    db_token = db.query(RefreshToken).filter(RefreshToken.token_hash == hashed_token).first()
    if db_token and not db_token.revoked_at:
        db_token.revoked_at = datetime.now(timezone.utc)
        db.commit()
        
    return {"success": True, "message": "Đã đăng xuất thành công"}

# ----------------------------------------------------
# LOGIN (ĐÃ SỬA CHUẨN FORM DATA THEO TV C)
# ----------------------------------------------------
@router.post("/login", response_model=TokenResponse)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    # Sử dụng form_data.username (thay vì email) để khớp với chuẩn OAuth2 của FastAPI
    user = db.query(User).filter(
        User.email == form_data.username
    ).first()

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Sai email hoặc password",
        headers={"WWW-Authenticate": "Bearer"},
    )

    if not user:
        raise credentials_exception

    is_valid_password = verify_password(
        form_data.password,
        user.password_hash
    )

    if not is_valid_password:
        raise credentials_exception

    access_token = create_access_token(
        data={
            "sub": str(user.id),
            "email": user.email
        }
    )

    refresh_token = create_refresh_token(
        data={
            "sub": str(user.id)
        }
    )

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }