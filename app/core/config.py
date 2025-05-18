import os
from pathlib import Path
from pydantic import BaseModel, ConfigDict, Field
from typing import Dict, List, Optional, Any
from pydantic_settings import BaseSettings

# Đảm bảo sử dụng đường dẫn tuyệt đối đến file .env
BASE_DIR = Path(__file__).resolve().parent.parent.parent
dotenv_path = os.path.join(BASE_DIR, ".env")

# Kiểm tra file .env có tồn tại không
if os.path.exists(dotenv_path):
    print(f"File .env được tìm thấy tại: {dotenv_path}")
else:
    print(f"Cảnh báo: Không tìm thấy file .env tại {dotenv_path}")
    print("Hệ thống sẽ sử dụng giá trị mặc định hoặc biến môi trường từ hệ thống.")

# Đảm bảo biến môi trường OPENAI_MODEL được đặt
if not os.environ.get("OPENAI_MODEL") and os.environ.get("CHAT_MODEL"):
    os.environ["OPENAI_MODEL"] = os.environ.get("CHAT_MODEL")
    print(f"Đã đặt OPENAI_MODEL = {os.environ.get('OPENAI_MODEL')}")

class Settings(BaseSettings):
    """
    Cấu hình cho ứng dụng - tự động load từ file .env và biến môi trường hệ thống
    """
    # App settings
    APP_NAME: str = Field(default="Cosmo bakery", validation_alias="APP_NAME")
    API_PREFIX: str = Field(default="/api/v1", validation_alias="API_PREFIX")
    DEBUG: bool = Field(default=False, validation_alias="DEBUG")
    PORT: int = Field(default=8000, validation_alias="PORT")
    CORS_ORIGINS: str = Field(default="http://localhost:3000,http://localhost:8080", validation_alias="CORS_ORIGINS")
    
    # API Keys
    OPENAI_API_KEY: str = Field(default="", validation_alias="OPENAI_API_KEY")
    
    # Spring Boot API settings
    SPRING_BOOT_API_URL: str = Field(default="http://localhost:8081", validation_alias="SPRING_BOOT_API_URL")
    SPRING_BOOT_TOKEN: str = Field(default="", validation_alias="SPRING_BOOT_TOKEN")
    
    # Vector DB settings
    VECTOR_DB_PATH: str = Field(default="./data/vector_db", validation_alias="VECTOR_DB_PATH")
    
    # Model settings
    CHAT_MODEL: str = Field(default="gpt-4o-mini-2024-07-18", validation_alias="CHAT_MODEL")
    
    # Chat settings
    MAX_TOKENS: int = Field(default=1024, validation_alias="MAX_TOKENS")
    TEMPERATURE: float = Field(default=0.7, validation_alias="TEMPERATURE")

    # MySQL Database URL
    DB_HOST: str = Field(default="localhost", validation_alias="DB_HOST")
    DB_PORT: str = Field(default="3306", validation_alias="DB_PORT")
    DB_USER: str = Field(default="root", validation_alias="DB_USER")
    DB_PASSWORD: str = Field(default="", validation_alias="DB_PASSWORD")
    DB_NAME: str = Field(default="hoangtu_pickleball", validation_alias="DB_NAME")
    
    @property
    def DATABASE_URL(self) -> str:
        return f"mysql+pymysql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
    
    # Milvus settings
    MILVUS_URI: str = Field(default="http://localhost:19530", validation_alias="MILVUS_URI")
    MILVUS_COLLECTION_NAME: str = Field(default="cosmoBakery", validation_alias="MILVUS_COLLECTION_NAME")
    MILVUS_FORCE_RECREATE: bool = Field(default=False, validation_alias="MILVUS_FORCE_RECREATE")
    
    # OpenAI settings
    OPENAI_EMBEDDING_MODEL: str = Field(default="text-embedding-3-large", validation_alias="OPENAI_EMBEDDING_MODEL")
    OPENAI_API_BASE: str = Field(default="https://api.openai.com/v1", validation_alias="OPENAI_API_BASE")
    OPENAI_API_TYPE: str = Field(default="open_ai", validation_alias="OPENAI_API_TYPE")
    OPENAI_API_VERSION: str = Field(default="2024-10-21", validation_alias="OPENAI_API_VERSION")

    API_KEY: str = Field(default="test-api-key", validation_alias="API_KEY")

    model_config = ConfigDict(
        env_file=dotenv_path,
        env_file_encoding="utf-8",
        extra="ignore",  # Cho phép các trường khác trong file .env mà không gây lỗi
        env_nested_delimiter="__"  # Hỗ trợ cấu trúc lồng nhau trong biến môi trường
    )

# Khởi tạo settings từ file .env và biến môi trường
settings = Settings()
print(f"Cấu hình đã được load thành công!")
print(f"CHAT_MODEL: {settings.CHAT_MODEL}")
print(f"DATABASE_URL: {settings.DATABASE_URL}")

# Đảm bảo OPENAI_MODEL và CHAT_MODEL nhất quán
if settings.CHAT_MODEL and settings.CHAT_MODEL != os.environ.get("OPENAI_MODEL"):
    os.environ["OPENAI_MODEL"] = settings.CHAT_MODEL
    print(f"Đã đồng bộ OPENAI_MODEL thành {os.environ.get('OPENAI_MODEL')}")