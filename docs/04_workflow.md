# QuizBattle - Workflow

## 1. Authentication Workflow

Guest
-> Register/Login
-> Backend xác thực
-> Trả access token + refresh token
-> User vào Dashboard

## 2. Quiz Workflow

User login
-> Dashboard
-> Create Quiz
-> Add Questions
-> Save Quiz

## 3. Room Workflow

Host chọn Quiz
-> Create Room
-> Backend generate room code
-> Room status = waiting
-> Host vào Lobby

## 4. Join Workflow

Player nhập room code
-> Backend validate
-> Player vào Lobby
-> WebSocket connect
-> Broadcast player list

## 5. Gameplay Workflow

Host Start Game
-> Server tạo game session
-> Server gửi question_started
-> Frontend hiển thị câu hỏi + timer
-> Player submit answer
-> Server lưu answer
-> Hết giờ
-> Server chấm điểm
-> Server gửi question_result
-> Server gửi leaderboard_updated
-> Server chuyển câu tiếp theo

## 6. End Game Workflow

Câu cuối kết thúc
-> Server tính final ranking
-> Server lưu result
-> Server broadcast game_finished
-> Frontend hiển thị final leaderboard

## 7. Nguyên tắc quan trọng

- Backend là source of truth.
- Frontend không tự tính đúng/sai.
- Frontend không tự tính điểm.
- Không gửi is_correct xuống frontend khi câu hỏi đang chạy.
- PostgreSQL lưu dữ liệu chính thức.
- Redis lưu state realtime tạm thời.