import os
from dotenv import load_dotenv
from pydantic import BaseModel
from typing import Dict, List, Optional, Any
from pydantic_settings import BaseSettings

# Load environment variables
load_dotenv()

class Settings(BaseSettings):
    """
    Cấu hình cho ứng dụng
    """
    # App settings
    APP_NAME: str = "Cosmetic Shop Chatbot"
    API_PREFIX: str = "/api"
    DEBUG: bool = os.getenv("DEBUG", "False").lower() == "true"
    PORT: int = int(os.getenv("PORT", "8000"))
    CORS_ORIGINS: str = os.getenv("CORS_ORIGINS", "http://localhost:3000,http://localhost:8080")
    
    # API Keys
    OPENAI_API_KEY: str = os.environ.get("OPENAI_API_KEY", "")
    
    # Spring Boot API settings
    SPRING_BOOT_API_URL: str = os.environ.get("SPRING_BOOT_API_URL", "http://localhost:8081")
    SPRING_BOOT_TOKEN: str = os.getenv("SPRING_BOOT_TOKEN", "")
    
    # Vector DB settings
    VECTOR_DB_PATH: str = os.getenv("VECTOR_DB_PATH", "./data/vector_db")
    
    # Model settings
    EMBEDDING_MODEL: str = os.getenv("EMBEDDING_MODEL", "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")
    CHAT_MODEL: str = os.getenv("CHAT_MODEL", "gpt-3.5-turbo")
    
    # Chat settings
    MAX_TOKENS: int = int(os.getenv("MAX_TOKENS", "1024"))
    TEMPERATURE: float = float(os.getenv("TEMPERATURE", "0.7"))

    # MySQL Database URL
    DB_HOST: str = os.environ.get("DB_HOST", "localhost")
    DB_PORT: str = os.environ.get("DB_PORT", "3306")
    DB_USER: str = os.environ.get("DB_USER", "root")
    DB_PASSWORD: str = os.environ.get("DB_PASSWORD", "")
    DB_NAME: str = os.environ.get("DB_NAME", "cosmetic_chatbot")
    DATABASE_URL: str = os.environ.get(
        "DATABASE_URL", 
        f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    )
    
    # Cấu hình khác
    QDRANT_HOST: str = os.environ.get("QDRANT_HOST", "localhost")
    QDRANT_PORT: int = int(os.environ.get("QDRANT_PORT", "6333"))
    QDRANT_COLLECTION_NAME: str = os.environ.get("QDRANT_COLLECTION_NAME", "cosmo")
    QDRANT_FORCE_RECREATE: bool = os.environ.get("QDRANT_FORCE_RECREATE", "False").lower() == "true"
    OPENAI_EMBEDDING_MODEL: str = os.environ.get("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")

    OPENAI_API_BASE: str = os.environ.get("OPENAI_API_BASE", "")
    OPENAI_API_TYPE: str = os.environ.get("OPENAI_API_TYPE", "")
    OPENAI_API_VERSION: str = os.environ.get("OPENAI_API_VERSION", "")

    API_KEY: str = os.environ.get("API_KEY", "test-api-key")

    class Config:
        env_file = ".env"
        extra = "ignore"  # Cho phép các trường khác trong file .env mà không gây lỗi

settings = Settings() 