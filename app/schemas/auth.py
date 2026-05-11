from pydantic import BaseModel, EmailStr, ConfigDict
from datetime import datetime

# --- PHẦN CỦA TV C ---
class RefreshTokenRequest(BaseModel):
    refresh_token: str


class LogoutRequest(BaseModel):
    refresh_token: str


# --- PHẦN CỦA MEMBER A (ĐĂNG KÝ) ---
class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    id: int
    username: str
    email: EmailStr
    created_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


# --- PHẦN LOGIN CỦA MEMBER B ---
class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str