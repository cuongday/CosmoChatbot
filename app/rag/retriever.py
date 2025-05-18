from typing import List, Dict, Any
import logging
from .vector_store import vector_store
from ..client.spring_client import spring_boot_client
from ..core.config import settings

# Cấu hình logging
logger = logging.getLogger(__name__)

class ProductRetriever:
    """
    Truy xuất thông tin sản phẩm cho RAG - sử dụng OpenAI embedding
    """
    def __init__(self):
        self.vector_store = vector_store
        logger.info(f"ProductRetriever khởi tạo với OpenAI model: {settings.OPENAI_EMBEDDING_MODEL}")
        print(f"[RETRIEVER] Khởi tạo với OpenAI embedding model: {settings.OPENAI_EMBEDDING_MODEL}")
    
    def retrieve(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Truy xuất sản phẩm từ vector database và trả về kết quả
        """
        # Làm phong phú query để cải thiện kết quả tìm kiếm
        enriched_query = self._enrich_query(query)
        
        logger.info(f"Tìm kiếm sản phẩm với query gốc: '{query}'")
        logger.info(f"Query đã làm phong phú: '{enriched_query}'")
        print(f"[RETRIEVER] Tìm kiếm với query gốc: '{query}'")
        print(f"[RETRIEVER] Query đã làm phong phú: '{enriched_query}'")
        
        # Tìm kiếm trong vector database với query đã làm phong phú
        vector_results = self.vector_store.search(enriched_query, top_k)
        
        # Nếu không có kết quả từ vector database, thử sử dụng Spring Boot API
        if not vector_results:
            logger.info("Không tìm thấy kết quả từ vector DB, sử dụng Spring Boot API")
            print(f"[RETRIEVER] Không tìm thấy kết quả từ vector DB, sử dụng Spring Boot API")
            api_results = spring_boot_client.search_products(query, top_k)
            return api_results
        
        logger.info(f"Tìm thấy {len(vector_results)} kết quả từ vector DB")
        return vector_results
    
    def _enrich_query(self, query: str) -> str:
        """
        Làm phong phú query để cải thiện kết quả tìm kiếm
        """
        # Nếu query quá ngắn (ví dụ: chỉ là "bánh"), thêm thông tin để tìm kiếm tốt hơn
        if len(query.split()) <= 2:
            return f"sản phẩm {query} thông tin chi tiết mô tả đặc điểm"
        return query
    
    def get_product_by_id(self, product_id: str) -> Dict[str, Any]:
        """
        Lấy thông tin chi tiết của sản phẩm theo ID
        """
        logger.info(f"Lấy thông tin sản phẩm ID: {product_id}")
        # Lấy thông tin từ Spring Boot API
        return spring_boot_client.get_product_by_id(product_id)

# Singleton instance
product_retriever = ProductRetriever()