# QuizBattle Backend

Backend service for QuizBattle realtime quiz battle platform.

## Tech Stack

- Python 3.13
- Miniconda
- FastAPI
- WebSocket
- PostgreSQL
- SQLAlchemy 2.0
- Alembic
- Redis
- JWT Authentication
- Docker Compose

## Branch Workflow

````txt
main    = stable/demo branch
develop = working branch for team



## Câu lệnh khởi chạy backend
cd /d "D:\Odin Intern\QuizBattle Project\quizbattle-backend"
conda activate quizbattle
python --version
python -m uvicorn app.main:app --reload

## khơi chạy docker
docker compose up -d
docker compose down
docker ps
=======
### Cách tạo dữ liệu mẫu (Seed Data)
Sau khi setup database và chạy migration, bạn có thể tạo ngay một bộ dữ liệu có sẵn (User, Quiz, Question) để test nhanh giao diện bằng lệnh sau:

```bash
# Đảm bảo đang đứng ở thư mục quizbattle-backend và trong môi trường miniconda
python seed.py
````
