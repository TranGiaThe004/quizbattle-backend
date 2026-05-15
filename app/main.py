from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.db.base import Base
from app.db.session import engine

from app.api.v1.routes import auth, quizzes, questions, websockets, rooms, results


app = FastAPI(
    title="QuizBattle API",
    description="Backend API for realtime quiz battle platform",
    version="0.1.0",
)

# Tạo bảng database tự động
Base.metadata.create_all(bind=engine)

# --- CẤU HÌNH CORS ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- ROUTERS ---
app.include_router(auth.router)
app.include_router(quizzes.router)
app.include_router(questions.router)
app.include_router(websockets.router)
app.include_router(rooms.router)
app.include_router(results.router, prefix="/api/v1/game-sessions", tags=["Results"])

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