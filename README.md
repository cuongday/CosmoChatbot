# Python Chatbot Service

Dịch vụ chatbot đa agent cho cửa hàng mỹ phẩm Cosmo, sử dụng OpenAI Assistant API và RAG (Retrieval Augmented Generation).

## Tính năng

- Kiến trúc đa agent chuyên biệt:
  - **Product Agent**: Tư vấn và cung cấp thông tin về sản phẩm
  - **Cart Agent**: Quản lý giỏ hàng và thanh toán
  - **Shop Agent**: Thông tin cửa hàng, chính sách và đơn hàng
  - **Manager Agent**: Điều phối giữa các agent

- RAG (Retrieval Augmented Generation) cho thông tin sản phẩm
- Tích hợp đầy đủ với Spring Boot backend thông qua API
- Hỗ trợ quản lý giỏ hàng và xử lý đơn hàng
- Hỗ trợ tiếng Việt hoàn toàn

## Kiến trúc tổng thể

```
[Frontend] <--> [Spring Boot Backend] <--> [Python Chatbot Service]
                      |                             |
                [MySQL Database]              [Qdrant Vector DB]
```

## Yêu cầu hệ thống

- Python 3.10+
- FastAPI
- OpenAI API Key
- Qdrant Vector Database 
- MySQL Database
- Spring Boot Backend (Hiện có)

## Cài đặt

### Bước 1: Clone repository

```bash
git clone <repository-url>
cd python-chatbot-service
```

### Bước 2: Cài đặt dependencies

```bash
pip install -r requirements.txt
```

### Bước 3: Cấu hình môi trường

Tạo file `.env` từ mẫu `.env.example`:

```bash
cp .env.example .env
```

Sửa file `.env` với các thông tin cấu hình của bạn:
- `OPENAI_API_KEY`: API key của OpenAI
- `SPRING_BOOT_API_URL`: URL của Spring Boot Backend
- `DB_USER, DB_PASSWORD, DB_HOST, DB_PORT, DB_NAME`: Thông tin kết nối MySQL
- `QDRANT_HOST, QDRANT_PORT`: Thông tin kết nối Qdrant

### Bước 4: Cài đặt Qdrant Vector Database

#### Sử dụng Docker (Khuyến nghị)
```bash
docker run -d -p 6333:6333 -p 6334:6334 \
    -v qdrant_storage:/qdrant/storage \
    --name qdrant_service \
    qdrant/qdrant
```

#### Hoặc cài đặt trực tiếp
Tham khảo [tài liệu chính thức của Qdrant](https://qdrant.tech/documentation/guides/installation/).

### Bước 5: Chuẩn bị MySQL Database
```sql
CREATE DATABASE cosmetic_chatbot CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

### Bước 6: Khởi động ứng dụng

```bash
uvicorn main:app --reload
```

Ứng dụng sẽ chạy tại `http://localhost:8000`

## Cấu trúc dự án

```
python-chatbot-service/
├── app/
│   ├── api/              # API endpoints
│   │   ├── endpoints.py  # API routes
│   │   ├── agents/       # Các agent xử lý
│   │   │   ├── product_agent.py
│   │   │   ├── cart_agent.py 
│   │   │   ├── shop_agent.py
│   │   │   └── manager_agent.py
│   │   ├── rag/          # RAG components
│   │   │   ├── embeddings.py
│   │   │   ├── retriever.py
│   │   │   └── vector_store.py
│   │   ├── tools/        # Tool functions
│   │   │   ├── product_tools.py
│   │   │   ├── cart_tools.py
│   │   │   ├── checkout_tools.py
│   │   │   └── shop_tools.py
│   │   ├── client/       # Spring Boot API clients
│   │   │   └── spring_client.py
│   │   ├── core/         # Core configurations
│   │   │   ├── config.py
│   │   │   └── security.py
│   │   ├── db/           # Database models và kết nối
│   │   │   └── database.py
│   │   └── models/       # Pydantic models
│   │       └── api_models.py
│   ├── prompts/          # Agent prompts
│   ├── data/             # Vector DB data
│   ├── tests/            # Unit tests
│   └── main.py           # Entry point
```

## API Endpoints

### Chat API

```
POST /api/chat
```

Request:
```json
{
  "message": "Tôi muốn tìm kem dưỡng da",
  "thread_id": "thread_123",
  "user_id": "user_456"
}
```

Response:
```json
{
  "message": "Chúng tôi có nhiều loại kem dưỡng da phù hợp với nhiều loại da khác nhau. Bạn có thể cho tôi biết loại da của bạn là gì không?",
  "source_documents": [...],
  "conversation_id": "conv_789"
}
```

### Sync API

```
POST /api/sync
```

Request:
```json
{
  "type": "products",
  "data": [...]
}
```

Response:
```json
{
  "status": "success",
  "count": 10,
  "message": "Đã đồng bộ 10 sản phẩm"
}
```

### Auto-Sync API

```
POST /api/auto-sync
```

Request:
```json
{
  "type": "products",
  "limit": 100
}
```

Response:
```json
{
  "status": "success",
  "count": 100,
  "message": "Đã đồng bộ 100 sản phẩm từ Spring Boot API"
}
```

## Tích hợp với Spring Boot

### API được sử dụng từ Spring Boot Backend

#### API Sản phẩm
- **GET /api/v1/products**: Lấy danh sách sản phẩm (phân trang)
- **GET /api/v1/products/{id}**: Lấy thông tin sản phẩm theo ID
- **GET /api/v1/products/category/{categoryId}**: Lấy sản phẩm theo danh mục

#### API Giỏ hàng
- **POST /api/v1/carts/add**: Thêm sản phẩm vào giỏ hàng
- **PUT /api/v1/carts/update/{cartDetailId}**: Cập nhật số lượng sản phẩm
- **DELETE /api/v1/carts/remove/{cartDetailId}**: Xóa sản phẩm khỏi giỏ hàng
- **GET /api/v1/carts**: Lấy thông tin giỏ hàng
- **DELETE /api/v1/carts/clear**: Xóa tất cả sản phẩm trong giỏ hàng

#### API Đơn hàng
- **POST /api/v1/orders**: Tạo đơn hàng mới
- **GET /api/v1/orders/my-orders**: Lấy danh sách đơn hàng của người dùng
- **GET /api/v1/orders/{id}/details**: Lấy chi tiết đơn hàng

## Các Agent và Công cụ

### Product Agent
- Tìm kiếm và cung cấp thông tin sản phẩm
- So sánh sản phẩm
- Đề xuất sản phẩm theo loại da và nhu cầu

### Cart Agent
- Quản lý giỏ hàng (thêm, cập nhật, xóa sản phẩm)
- Tạo đơn hàng
- Hỗ trợ thanh toán COD và TRANSFER

### Shop Agent
- Cung cấp thông tin cửa hàng
- Thông tin về chính sách bán hàng
- Tra cứu thông tin đơn hàng

### Manager Agent
- Điều phối yêu cầu đến đúng agent chuyên biệt
- Xử lý đa dạng loại truy vấn

## Vector Database (Qdrant)

Dự án sử dụng Qdrant làm vector database để:
- Lưu trữ embeddings của thông tin sản phẩm
- Thực hiện tìm kiếm ngữ nghĩa (semantic search)
- Hỗ trợ RAG để cung cấp thông tin chính xác về sản phẩm

Qdrant cung cấp hiệu suất cao, khả năng mở rộng tốt và linh hoạt trong việc truy vấn dữ liệu vector.

## Cách deploy với Docker

### Bước 1: Build Docker image

```bash
docker build -t cosmetic-chatbot .
```

### Bước 2: Chạy container

```bash
docker run -d -p 8000:8000 --env-file .env --name chatbot cosmetic-chatbot
```

### Bước 3: Docker Compose (Tùy chọn)

Tạo file `docker-compose.yml`:

```yaml
version: '3'
services:
  chatbot:
    build: .
    ports:
      - "8000:8000"
    env_file: .env
    depends_on:
      - qdrant

  qdrant:
    image: qdrant/qdrant
    ports:
      - "6333:6333"
      - "6334:6334"
    volumes:
      - qdrant_storage:/qdrant/storage

volumes:
  qdrant_storage:
```

Chạy với Docker Compose:
```bash
docker-compose up -d
```

## Đóng góp

Vui lòng tạo issue hoặc pull request nếu bạn muốn đóng góp cho dự án.