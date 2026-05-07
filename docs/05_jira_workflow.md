# QuizBattle - Jira Workflow

## 1. Issue Types

Epic = Module lớn.
Story = Chức năng theo góc nhìn người dùng.
Task = Việc kỹ thuật hoặc setup.
Sub-task = Việc nhỏ bên trong Story/Task.
Bug = Lỗi phát sinh.

## 2. Workflow

Backlog
-> Selected for Development
-> In Progress
-> Code Review
-> Testing
-> Done

## 3. Definition of Ready

Một task/story chỉ bắt đầu khi rõ:

- Mục tiêu là gì.
- Ai là actor.
- API/WebSocket cần gì.
- Database có cần thêm bảng không.
- UI cần màn hình/component nào.
- Acceptance Criteria là gì.

## 4. Definition of Done

Một task được coi là Done khi:

- Code chạy được local.
- Không có lỗi console nghiêm trọng.
- API test được bằng Swagger/Postman nếu có API.
- Frontend gọi API thành công nếu có UI.
- Đã push code lên GitHub.
- Có người khác review hoặc test chéo.
- Jira task có comment kết quả.