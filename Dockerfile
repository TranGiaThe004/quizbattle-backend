# quizbattle-backend/Dockerfile
FROM python:3.13-slim

WORKDIR /app

# Copy file requirements và cài đặt thư viện
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# FIX LỖI: Cài thêm thư viện đọc Form Login của FastAPI
RUN pip install --no-cache-dir python-multipart

# Copy toàn bộ source code vào container
COPY . .

# Chạy server FastAPI bằng Uvicorn
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]