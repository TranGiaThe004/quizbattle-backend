from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime
from app.db.session import get_db
from app.models.token import RefreshToken
from app.schemas.auth import RefreshTokenRequest, LogoutRequest
from app.core.security import get_current_user, create_access_token, get_token_hash

router = APIRouter(prefix="/api/v1/auth", tags=["Authentication"])


@router.get("/me")
def get_me(current_user = Depends(get_current_user)):
    return {
        "success": True, 
        "data": {
            "id": current_user.id
        }
    }

@router.post("/refresh")
def refresh_token(req: RefreshTokenRequest, db: Session = Depends(get_db)):

    hashed_token = get_token_hash(req.refresh_token)
   
    db_token = db.query(RefreshToken).filter(RefreshToken.token_hash == hashed_token).first()
   
    if not db_token or db_token.revoked_at or db_token.expires_at < datetime.utcnow():
        raise HTTPException(status_code=401, detail="Refresh token không hợp lệ hoặc đã hết hạn")
  
    new_access_token = create_access_token(data={"sub": str(db_token.user_id)})
    return {"access_token": new_access_token, "token_type": "bearer"}

@router.post("/logout")
def logout(req: LogoutRequest, db: Session = Depends(get_db)):

    hashed_token = get_token_hash(req.refresh_token)
    db_token = db.query(RefreshToken).filter(RefreshToken.token_hash == hashed_token).first()
    if db_token and not db_token.revoked_at:
        db_token.revoked_at = datetime.utcnow()
        db.commit()
        
    return {"success": True, "message": "Đã đăng xuất thành công"}