# QuizBattle - Use Cases

## UC-01: Register Account

Actor: Guest

Main Flow:
1. Guest mở trang Register.
2. Nhập username, email, password.
3. Frontend validate dữ liệu cơ bản.
4. Backend kiểm tra email đã tồn tại chưa.
5. Backend hash password.
6. Backend lưu user vào database.
7. Hệ thống báo đăng ký thành công.

Acceptance Criteria:
- User đăng ký được tài khoản.
- Email không được trùng.
- Password không lưu plain text.

---

## UC-02: Login

Actor: Guest

Main Flow:
1. Guest mở trang Login.
2. Nhập email và password.
3. Backend kiểm tra user và password.
4. Backend tạo access token và refresh token.
5. Frontend lưu token.
6. User được chuyển vào Dashboard.

Acceptance Criteria:
- Login đúng thì vào Dashboard.
- Login sai thì báo lỗi.
- Token dùng được để gọi API protected.

---

## UC-03: Create Quiz

Actor: Authenticated User

Main Flow:
1. User vào Dashboard.
2. Click Create Quiz.
3. Nhập title và description.
4. Backend gắn owner_id là user hiện tại.
5. Backend lưu quiz.
6. User thấy quiz trong My Quizzes.

Acceptance Criteria:
- Quiz được lưu trong database.
- Quiz thuộc đúng owner.
- User thấy quiz trong danh sách của mình.

---

## UC-04: Add Question

Actor: Quiz Owner

Main Flow:
1. Owner mở trang edit quiz.
2. Chọn Add Question.
3. Chọn loại câu hỏi Multiple Choice hoặc True/False.
4. Nhập nội dung câu hỏi.
5. Nhập đáp án.
6. Chọn đáp án đúng.
7. Nhập thời gian trả lời.
8. Backend lưu question và options.

Acceptance Criteria:
- Câu hỏi được thêm vào quiz.
- Mỗi câu hỏi có time limit.
- Có đúng một đáp án đúng trong MVP.

---

## UC-05: Create Room

Actor: Host

Main Flow:
1. Host chọn quiz.
2. Click Create Room.
3. Backend kiểm tra quiz hợp lệ.
4. Backend tạo room code 6 ký tự.
5. Room status = waiting.
6. Host vào lobby.

Acceptance Criteria:
- Room code có 6 ký tự.
- Room được tạo với status waiting.
- Host vào lobby thành công.

---

## UC-06: Join Room

Actor: Player

Main Flow:
1. Player nhập room code.
2. Backend kiểm tra room tồn tại.
3. Backend kiểm tra room đang waiting.
4. Backend thêm player vào room.
5. Server broadcast danh sách player mới.

Acceptance Criteria:
- Player join được bằng room code đúng.
- Room code sai thì báo lỗi.
- Lobby cập nhật realtime.

---

## UC-07: Gameplay Realtime

Actor: Host, Player, System

Main Flow:
1. Host start game.
2. Server tạo game session.
3. Server gửi câu hỏi đầu tiên.
4. Frontend hiển thị câu hỏi và timer.
5. Player chọn đáp án.
6. Server lưu đáp án.
7. Hết giờ, server chấm điểm.
8. Server gửi question result.
9. Server gửi leaderboard.
10. Server chuyển câu tiếp theo.

Acceptance Criteria:
- Server kiểm soát timer.
- Frontend không tự chấm đúng/sai.
- Mỗi player chỉ trả lời một lần mỗi câu.
- Leaderboard cập nhật sau mỗi câu.

---

## UC-08: Finish Game

Actor: System

Main Flow:
1. Server phát hiện hết câu hỏi.
2. Server tính final ranking.
3. Server lưu kết quả.
4. Server broadcast game_finished.
5. Frontend hiển thị final leaderboard.

Acceptance Criteria:
- Có bảng xếp hạng cuối cùng.
- Kết quả được lưu.
- Reload vẫn xem được result.