from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_openai import OpenAIEmbeddings
from typing import List
from ..core.config import settings

class EmbeddingProvider:
    """
    Provider cho các embedding models
    """
    def __init__(self):
        self.model_name = settings.EMBEDDING_MODEL
        self._init_model()
    
    def _init_model(self):
        """
        Khởi tạo embedding model dựa trên cấu hình
        """
        if 'text-embedding-3' in self.model_name.lower() or 'openai' in self.model_name.lower():
            # Sử dụng OpenAI embedding models
            self.model = OpenAIEmbeddings(
                model=self.model_name,
                openai_api_key=settings.OPENAI_API_KEY,
                dimensions=3072 if 'large' in self.model_name.lower() else 1536
            )
        else:
            # Sử dụng Hugging Face model
            self.model = HuggingFaceEmbeddings(
                model_name=self.model_name,
                model_kwargs={'device': 'cpu'},
                encode_kwargs={'normalize_embeddings': True}
            )
    
    def get_embeddings(self, texts: List[str]) -> List[List[float]]:
        """
        Lấy embedding vectors cho một danh sách văn bản
        """
        return self.model.embed_documents(texts)
    
    def get_query_embedding(self, text: str) -> List[float]:
        """
        Lấy embedding vector cho một câu truy vấn
        """
        return self.model.embed_query(text)

# Singleton instance
embedding_provider = EmbeddingProvider() 