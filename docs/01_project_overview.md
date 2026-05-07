# QuizBattle - Project Overview

## 1. Mô tả dự án

QuizBattle là nền tảng web chơi quiz đấu trực tiếp thời gian thực, tương tự Kahoot hoặc Quizizz. Người dùng có thể tạo bộ câu hỏi, tạo phòng chơi, mời người khác tham gia bằng mã phòng 6 ký tự và thi đấu realtime với timer, leaderboard, kết quả từng câu và bảng xếp hạng cuối cùng.

## 2. Mục tiêu sản phẩm

- Người dùng đăng ký, đăng nhập, đăng xuất.
- Người dùng tạo, sửa, xóa quiz.
- Người dùng thêm câu hỏi Multiple Choice hoặc True/False.
- Mỗi câu hỏi có thời gian trả lời.
- Host tạo phòng chơi từ quiz.
- Player join phòng bằng mã phòng.
- Lobby hiển thị danh sách người chơi realtime.
- Host bắt đầu game.
- Server điều phối câu hỏi, timer, đáp án và điểm số.
- Leaderboard cập nhật realtime sau mỗi câu.
- Kết thúc game hiển thị final leaderboard.
- Kết quả game được lưu vào database.

## 3. Công nghệ sử dụng

Backend:
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

Frontend:
- Next.js
- TypeScript

Tools:
- Git
- GitHub
- Jira

## 4. Scope

### P0 - Must Have

- Authentication
- Quiz Management
- Question Management
- Game Room
- Lobby realtime
- Gameplay realtime
- Timer
- Submit answer
- Question result
- Live leaderboard
- Final result
- Save game result
- Docker Compose

### P1 - Nice to Have

- Chat realtime
- Public quiz library
- Personal statistics
- Sound effect
- Confetti
- Mobile-friendly

## 5. Demo chính

Register -> Login -> Create Quiz -> Add Questions -> Create Room -> Join Room -> Start Game -> Play Realtime -> Leaderboard -> Final Result.