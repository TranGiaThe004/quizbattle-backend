from fastapi import FastAPI

app = FastAPI(
    title="QuizBattle API",
    description="Backend API for realtime quiz battle platform",
    version="0.1.0",
)


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