from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import auth

app = FastAPI(
    title="QuizBattle API",
    description="Backend API for realtime quiz battle platform",
    version="0.1.0",
)

# --- THÊM CẤU HÌNH CORS Ở ĐÂY ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Cho phép Frontend gọi API
    allow_credentials=True,
    allow_methods=["*"],  # Cho phép mọi phương thức GET, POST, PUT, DELETE...
    allow_headers=["*"],  # Cho phép mọi header
)
# --------------------------------

app.include_router(auth.router)

@app.get("/")
def root():
    return {
        "message": "Welcome to QuizBattle API"
    }

@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "service": "quizbattle-backend"
    }