from sqlmodel import SQLModel, create_engine, Session
from app.core.config import settings
import logging
import time

logger = logging.getLogger(__name__)

# Tạo connection string
DATABASE_URL = settings.DATABASE_URL

# Thêm charset cho MySQL nếu cần
if "mysql" in DATABASE_URL:
    # Chỉ thêm charset, không thêm pool params vào URL
    if "?" not in DATABASE_URL:
        DATABASE_URL += "?charset=utf8mb4"
    else:
        DATABASE_URL += "&charset=utf8mb4"

logger.info(f"Connecting to database at {DATABASE_URL.split('@')[0].split('://')[0]}://*****@{DATABASE_URL.split('@')[1] if '@' in DATABASE_URL else 'localhost'}")

# Tạo engine với các tham số phù hợp cho MySQL
# Các tham số pool được truyền riêng biệt thay vì trong URL
engine = create_engine(
    DATABASE_URL,
    echo=settings.DEBUG,
    pool_size=5,
    max_overflow=10,
    pool_timeout=30,
    pool_recycle=3600,  # Thời gian tối đa connection được giữ trong pool
    pool_pre_ping=True  # Kiểm tra kết nối trước khi sử dụng
)


def create_db_and_tables():
    """Khởi tạo database và tạo bảng"""
    max_retries = 5
    retry_count = 0
    
    while retry_count < max_retries:
        try:
            logger.info("Tạo các bảng SQL...")
            SQLModel.metadata.create_all(engine)
            logger.info("Các bảng đã được tạo thành công!")
            break
        except Exception as e:
            retry_count += 1
            wait_time = 2 ** retry_count  # exponential backoff
            logger.error(f"Lỗi kết nối database (lần thử {retry_count}/{max_retries}): {str(e)}")
            logger.info(f"Thử lại sau {wait_time} giây...")
            time.sleep(wait_time)
            
            if retry_count == max_retries:
                logger.error("Không thể kết nối tới database sau nhiều lần thử. Vui lòng kiểm tra cấu hình kết nối.")
                raise


def get_session():
    """Lấy một phiên database"""
    with Session(engine) as session:
        yield session 