from typing import List, Dict, Any
from .vector_store import vector_store
from ..client.spring_client import spring_boot_client

class ProductRetriever:
    """
    Truy xuất thông tin sản phẩm cho RAG
    """
    def __init__(self):
        self.vector_store = vector_store
    
    def retrieve(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Truy xuất sản phẩm từ vector database và trả về kết quả
        """
        # Tìm kiếm trong vector database
        vector_results = self.vector_store.search(query, top_k)
        
        # Nếu không có kết quả từ vector database, thử sử dụng Spring Boot API
        if not vector_results:
            api_results = spring_boot_client.search_products(query, top_k)
            return api_results
        
        return vector_results
    
    def get_product_by_id(self, product_id: str) -> Dict[str, Any]:
        """
        Lấy thông tin chi tiết của sản phẩm theo ID
        """
        # Lấy thông tin từ Spring Boot API
        return spring_boot_client.get_product_by_id(product_id)

# Singleton instance
product_retriever = ProductRetriever()