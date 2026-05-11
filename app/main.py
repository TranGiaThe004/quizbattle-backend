from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# SỬA LẠI ĐƯỜNG DẪN IMPORT CHUẨN Ở ĐÂY:
from app.api.v1.routes import auth, quizzes, questions

app = FastAPI(
    title="QuizBattle API",
    description="Backend API for realtime quiz battle platform",
    version="0.1.0",
)

# --- CẤU HÌNH CORS ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Cho phép Frontend gọi API
    allow_credentials=True,
    allow_methods=["*"],  # Cho phép mọi phương thức GET, POST, PUT, DELETE...
    allow_headers=["*"],  # Cho phép mọi header
)
# --------------------------------

# --- ĐĂNG KÝ CÁC ROUTER VÀO ĐÂY ---
app.include_router(auth.router)
app.include_router(quizzes.router)
app.include_router(questions.router)

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