from fastapi import FastAPI
from app.api import auth

app = FastAPI(
    title="QuizBattle API",
    description="Backend API for realtime quiz battle platform",
    version="0.1.0",
)

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