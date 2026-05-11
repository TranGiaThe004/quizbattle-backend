import secrets
from datetime import datetime, timedelta
from app.db.session import SessionLocal
from app.models.user import User
from app.models.token import RefreshToken # Chắc chắn bạn đã có file này từ Sprint 1
from app.core.security import get_token_hash, create_access_token

def generate_test_tokens():
    db = SessionLocal()
    try:
        # 1. Tìm user "host1" (user đã được tạo từ file seed.py)
        user = db.query(User).filter(User.username == "host1").first()
        if not user:
            print("❌ Không tìm thấy user 'host1'. Bạn hãy chạy 'python seed.py' trước nhé!")
            return

        # 2. Tạo Refresh Token thô (giống hệt cách làm thật lúc Login)
        raw_refresh_token = secrets.token_urlsafe(32)
        
        # 3. Cho token thô vào máy băm SHA-256
        hashed_token = get_token_hash(raw_refresh_token)
        
        # 4. Ghi đè vào Database (Hạn sử dụng 7 ngày)
        expires = datetime.utcnow() + timedelta(days=7)
        db_token = RefreshToken(
            user_id=user.id,
            token_hash=hashed_token,
            expires_at=expires
        )
        db.add(db_token)
        db.commit()

        # 5. Tiện tay tạo luôn Access Token (Vòng tay giấy)
        access_token = create_access_token(data={"sub": str(user.id)})

        print("✅ ĐÃ CẤP QUYỀN THÀNH CÔNG CHO:", user.username)
        print("-" * 50)
        print("🔑 ACCESS TOKEN (Copy chuỗi dưới đây dán vào nút Authorize trên Swagger):")
        print(f"Bearer {access_token}")
        print("-" * 50)
        print("🔄 REFRESH TOKEN (Copy chuỗi dưới dán vào Body của API /auth/refresh):")
        print(raw_refresh_token)
        print("-" * 50)

    except Exception as e:
        print("❌ Lỗi khi tạo token:", e)
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    generate_test_tokens()