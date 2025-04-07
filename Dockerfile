FROM python:3.10-slim

WORKDIR /app

# Cài đặt các dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Cài đặt các thư viện sentence transformers hỗ trợ tiếng Việt
RUN pip install --no-cache-dir transformers[sentencepiece]

# Copy toàn bộ mã nguồn
COPY . .

# Tạo thư mục lưu trữ vector database
RUN mkdir -p data/vector_db

# Expose cổng ứng dụng
EXPOSE 8000

# Khởi động ứng dụng
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"] 