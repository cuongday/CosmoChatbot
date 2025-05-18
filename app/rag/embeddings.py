from langchain_openai import OpenAIEmbeddings
from typing import List
from ..core.config import settings
import logging
import os
import traceback

# Cấu hình logging
logger = logging.getLogger(__name__)

class EmbeddingProvider:
    """
    Provider cho các embedding models - chỉ sử dụng OpenAI
    """
    def __init__(self):
        self._init_model()
    
    def _init_model(self):
        """
        Khởi tạo OpenAI embedding model
        """
        try:
            embedding_model_name = settings.OPENAI_EMBEDDING_MODEL
            logger.info(f"Sử dụng OpenAI Embedding model: {embedding_model_name}")
            print(f"[EMBEDDING] Sử dụng OpenAI Embedding model: {embedding_model_name}")
            
            # Xác định kích thước embedding dựa trên model
            dimensions = 3072 if 'large' in embedding_model_name.lower() else 1536
            logger.info(f"Kích thước embedding: {dimensions}")
            
            # Đảm bảo API base URL luôn có protocol prefix
            api_base = settings.OPENAI_API_BASE
            
            if not api_base:
                api_base = "https://api.openai.com/v1"
                logger.warning(f"OPENAI_API_BASE không được thiết lập, sử dụng mặc định: {api_base}")
                print(f"[EMBEDDING] OPENAI_API_BASE không được thiết lập, sử dụng mặc định: {api_base}")
            
            # Đảm bảo URL có https://
            if api_base and not (api_base.startswith('http://') or api_base.startswith('https://')):
                api_base = f"https://{api_base}"
                logger.info(f"Đã thêm protocol 'https://' vào API base URL: {api_base}")
                print(f"[EMBEDDING] Đã thêm protocol 'https://' vào API base URL: {api_base}")
            
            # Log thông tin kết nối
            logger.info(f"Kết nối OpenAI API với URL: {api_base}")
            print(f"[EMBEDDING] Kết nối OpenAI API với URL: {api_base}")
            
            # Thiết lập OpenAI API key từ settings
            api_key = settings.OPENAI_API_KEY
            if not api_key:
                logger.warning("OPENAI_API_KEY không được thiết lập, hãy kiểm tra .env hoặc biến môi trường")
                print("[EMBEDDING] CẢNH BÁO: OPENAI_API_KEY không được thiết lập, hãy kiểm tra .env hoặc biến môi trường")
            
            # Thiết lập các tham số tùy chọn một cách chi tiết
            api_type = settings.OPENAI_API_TYPE
            api_version = settings.OPENAI_API_VERSION
            
            logger.info(f"Thiết lập OpenAIEmbeddings với model={embedding_model_name}, dimensions={dimensions}, api_type={api_type}, api_version={api_version}")
            print(f"[EMBEDDING] Thiết lập OpenAIEmbeddings với model={embedding_model_name}, dimensions={dimensions}, api_type={api_type}, api_version={api_version}")
            
            # Đảm bảo URL có thể sử dụng
            if api_base.endswith('/'):
                api_base = api_base[:-1]  # Loại bỏ dấu / cuối nếu có
                
            # Khởi tạo model
            self.model = OpenAIEmbeddings(
                model=embedding_model_name,
                openai_api_key=api_key,
                openai_api_base=api_base,
                openai_api_type=api_type,
                openai_api_version=api_version,
                dimensions=dimensions
            )
            
            logger.info("OpenAI Embedding model khởi tạo thành công")
            print("[EMBEDDING] OpenAI Embedding model khởi tạo thành công")
        
        except Exception as e:
            logger.error(f"Lỗi khi khởi tạo OpenAI Embedding model: {str(e)}")
            print(f"[EMBEDDING] Lỗi khi khởi tạo OpenAI Embedding model: {str(e)}")
            traceback.print_exc()
            raise
    
    def get_embeddings(self, texts: List[str]) -> List[List[float]]:
        """
        Lấy embedding vectors cho một danh sách văn bản
        """
        try:
            return self.model.embed_documents(texts)
        except Exception as e:
            logger.error(f"Lỗi khi tạo embeddings: {str(e)}")
            print(f"[EMBEDDING] Lỗi khi tạo embeddings: {str(e)}")
            traceback.print_exc()
            raise
    
    def get_query_embedding(self, text: str) -> List[float]:
        """
        Lấy embedding vector cho một câu truy vấn
        """
        try:
            return self.model.embed_query(text)
        except Exception as e:
            logger.error(f"Lỗi khi tạo query embedding: {str(e)}")
            print(f"[EMBEDDING] Lỗi khi tạo query embedding: {str(e)}")
            traceback.print_exc()
            raise

# Singleton instance
embedding_provider = EmbeddingProvider() 