import os
import logging
from typing import List, Dict, Any, Optional
from langchain_community.vectorstores import Qdrant
from langchain.schema import Document
from .embeddings import embedding_provider
from ..core.config import settings
import qdrant_client
from qdrant_client.models import Distance, VectorParams
import traceback

# Cấu hình logging
logger = logging.getLogger(__name__)

class VectorStore:
    """
    Lớp quản lý vector database cho RAG
    """
    def __init__(self):
        self.persist_directory = settings.VECTOR_DB_PATH
        self._ensure_directory()
        self.embedding_function = embedding_provider.model
        
        # Lấy giá trị cấu hình từ settings
        self.host = settings.QDRANT_HOST
        self.port = settings.QDRANT_PORT
        self.collection_name = settings.QDRANT_COLLECTION_NAME
        
        logger.info(f"Vector Store được khởi tạo với: host={self.host}, port={self.port}, collection={self.collection_name}")
        print(f"[QDRANT] Khởi tạo Qdrant client với host={self.host}, port={self.port}, collection={self.collection_name}")
        
        self._init_db()
    
    def _ensure_directory(self):
        """
        Đảm bảo thư mục lưu trữ vector db tồn tại
        """
        os.makedirs(self.persist_directory, exist_ok=True)
        logger.info(f"Thư mục {self.persist_directory} đã được tạo hoặc đã tồn tại")
    
    def _check_collection_exists(self):
        """
        Kiểm tra xem collection đã tồn tại chưa
        """
        try:
            collections = self.client.get_collections().collections
            collection_names = [collection.name for collection in collections]
            exists = self.collection_name in collection_names
            logger.info(f"Kiểm tra collection '{self.collection_name}': {'Tồn tại' if exists else 'Không tồn tại'}")
            print(f"[QDRANT] Kiểm tra collection '{self.collection_name}': {'Tồn tại' if exists else 'Không tồn tại'}")
            return exists
        except Exception as e:
            error_msg = f"Lỗi khi kiểm tra collection: {str(e)}"
            logger.error(error_msg)
            print(f"[QDRANT] {error_msg}")
            traceback.print_exc()
            return False
    
    def _create_collection(self):
        """
        Tạo collection mới trong Qdrant
        """
        try:
            # Lấy kích thước vector từ embedding model
            logger.info("Tạo vector test để xác định kích thước...")
            print("[QDRANT] Đang tạo vector test để xác định kích thước...")
            vector_size = len(self.embedding_function.embed_query("Test query"))
            
            logger.info(f"Tạo mới collection '{self.collection_name}' với vector_size={vector_size}")
            print(f"[QDRANT] Tạo mới collection '{self.collection_name}' với vector_size={vector_size}")
            
            # Tạo collection với các tham số phù hợp
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(
                    size=vector_size,
                    distance=Distance.COSINE
                )
            )
            logger.info(f"Đã tạo mới collection '{self.collection_name}' thành công")
            print(f"[QDRANT] Đã tạo mới collection '{self.collection_name}' thành công")
            return True
        except Exception as e:
            error_msg = f"Lỗi khi tạo collection: {str(e)}"
            logger.error(error_msg)
            print(f"[QDRANT] {error_msg}")
            traceback.print_exc()
            return False
    
    def _init_db(self):
        """
        Khởi tạo vector database
        """
        try:
            # Tạo Qdrant client
            logger.info(f"Kết nối tới Qdrant server: {self.host}:{self.port}")
            print(f"[QDRANT] Kết nối tới Qdrant server: {self.host}:{self.port}")
            
            self.client = qdrant_client.QdrantClient(
                host=self.host,
                port=self.port
            )
            
            # Kiểm tra kết nối bằng cách lấy danh sách collections thay vì dùng get_cluster_info
            try:
                collections = self.client.get_collections()
                logger.info(f"Kết nối thành công, có {len(collections.collections)} collections")
                print(f"[QDRANT] Kết nối thành công, có {len(collections.collections)} collections")
            except Exception as e:
                logger.error(f"Không thể kết nối tới Qdrant server: {str(e)}")
                print(f"[QDRANT] Không thể kết nối tới Qdrant server: {str(e)}")
                raise
            
            # Kiểm tra xem có cần xóa và tạo lại collection không
            if settings.QDRANT_FORCE_RECREATE and self._check_collection_exists():
                logger.warning(f"Cài đặt QDRANT_FORCE_RECREATE=True, xóa collection '{self.collection_name}' hiện tại...")
                print(f"[QDRANT] Cài đặt QDRANT_FORCE_RECREATE=True, xóa collection '{self.collection_name}' hiện tại...")
                self.client.delete_collection(collection_name=self.collection_name)
                logger.info(f"Đã xóa collection '{self.collection_name}' để tạo mới")
                print(f"[QDRANT] Đã xóa collection '{self.collection_name}' để tạo mới")
            
            # Kiểm tra và tạo collection nếu chưa tồn tại
            if not self._check_collection_exists():
                logger.info(f"Collection '{self.collection_name}' không tồn tại. Đang tạo mới...")
                print(f"[QDRANT] Collection '{self.collection_name}' không tồn tại. Đang tạo mới...")
                self._create_collection()
            
            # Kết nối với Qdrant và khởi tạo vector store
            logger.info(f"Khởi tạo Langchain Qdrant vector store với collection '{self.collection_name}'")
            print(f"[QDRANT] Khởi tạo Langchain Qdrant vector store với collection '{self.collection_name}'")
            
            # Sử dụng embeddings thay vì embedding_function theo API mới
            self.db = Qdrant(
                client=self.client,
                collection_name=self.collection_name,
                embeddings=self.embedding_function
            )
            logger.info("Vector store đã sẵn sàng")
            print("[QDRANT] Vector store đã sẵn sàng")
            
        except Exception as e:
            error_msg = f"Lỗi khi khởi tạo Vector Store: {str(e)}"
            logger.error(error_msg)
            print(f"[QDRANT] {error_msg}")
            traceback.print_exc()
            raise
    
    def add_products(self, products: List[Dict[str, Any]]):
        """
        Thêm các sản phẩm vào vector database
        """
        logger.info(f"Bắt đầu thêm {len(products) if products else 0} sản phẩm vào vector database")
        print(f"[QDRANT] Bắt đầu thêm {len(products) if products else 0} sản phẩm vào vector database")
        
        if not products:
            logger.warning("Không có sản phẩm nào để thêm vào vector database")
            print("[QDRANT] Không có sản phẩm nào để thêm vào vector database")
            return
        
        try:    
            documents = []
            for idx, product in enumerate(products):
                try:
                    # Lấy ID của sản phẩm để log
                    product_id = product.get("id", "không có ID")
                    
                    # Tạo văn bản phong phú từ thông tin sản phẩm
                    product_text = f"Sản phẩm {product.get('name', '')} có mã số {product.get('id', '')}. "
                    product_text += f"Mô tả: {product.get('description', '')}. "
                    product_text += f"Giá bán: {product.get('sell_price', product.get('price', 0))} VNĐ. "
                    
                    if product.get('quantity') is not None:
                        product_text += f"Số lượng tồn kho: {product.get('quantity')}. "
                    
                    if product.get('status') is not None:
                        product_text += f"Trạng thái: {product.get('status')}. "
                    
                    if product.get('category_id') is not None:
                        product_text += f"Thuộc danh mục: {product.get('category_id')}. "
                    
                    # Log mẫu cho vài sản phẩm đầu tiên
                    if idx < 2:
                        logger.info(f"Mẫu sản phẩm {product_id}: {product_text[:100]}...")
                        print(f"[QDRANT] Mẫu sản phẩm {product_id}: {product_text[:100]}...")
                    
                    # Tạo document với metadata
                    doc = Document(
                        page_content=product_text,
                        metadata={
                            "product_id": str(product.get("id", "")),  # Đảm bảo ID dạng string
                            "name": product.get("name", ""),
                            "price": float(product.get("sell_price", product.get("price", 0))),
                            "image_url": product.get("image", product.get("image_url", "")),
                            "category": str(product.get("category_id", "")),
                            "status": product.get("status", ""),
                            "quantity": int(product.get("quantity", 0)),
                            "created_at": str(product.get("created_at", "")),
                            "updated_at": str(product.get("updated_at", ""))
                        }
                    )
                    documents.append(doc)
                except Exception as e:
                    logger.error(f"Lỗi khi xử lý sản phẩm {product.get('id', 'không có ID')}: {str(e)}")
                    print(f"[QDRANT] Lỗi khi xử lý sản phẩm {product.get('id', 'không có ID')}: {str(e)}")
                    # Tiếp tục với sản phẩm tiếp theo
            
            if not documents:
                logger.warning("Không có documents nào được tạo từ sản phẩm")
                print("[QDRANT] Không có documents nào được tạo từ sản phẩm")
                return
                
            logger.info(f"Đã chuẩn bị {len(documents)} documents để thêm vào collection '{self.collection_name}'")
            print(f"[QDRANT] Đã chuẩn bị {len(documents)} documents để thêm vào collection '{self.collection_name}'")
            
            # Kiểm tra và tạo collection nếu chưa tồn tại
            if not self._check_collection_exists():
                logger.warning(f"Collection '{self.collection_name}' không tồn tại. Đang tạo mới...")
                print(f"[QDRANT] Collection '{self.collection_name}' không tồn tại. Đang tạo mới...")
                self._create_collection()
                # Tạo lại kết nối
                self._init_db()
            
            # Tạo embedding cho một document để kiểm tra
            logger.info("Kiểm tra embedding với document đầu tiên...")
            print("[QDRANT] Kiểm tra embedding với document đầu tiên...")
            test_embedding = self.embedding_function.embed_documents([documents[0].page_content])[0]
            logger.info(f"Test embedding size: {len(test_embedding)}")
            print(f"[QDRANT] Test embedding size: {len(test_embedding)}")
            
            # Thêm documents vào vector database
            logger.info(f"Bắt đầu thêm {len(documents)} documents vào Qdrant...")
            print(f"[QDRANT] Bắt đầu thêm {len(documents)} documents vào Qdrant...")
            
            self.db.add_documents(documents)
            
            logger.info(f"Đã thêm thành công {len(documents)} documents vào collection '{self.collection_name}'")
            print(f"[QDRANT] Đã thêm thành công {len(documents)} documents vào collection '{self.collection_name}'")
            
        except Exception as e:
            error_msg = f"Lỗi khi thêm sản phẩm vào vector database: {str(e)}"
            logger.error(error_msg)
            print(f"[QDRANT] {error_msg}")
            traceback.print_exc()
            raise
    
    def search(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Tìm kiếm sản phẩm tương tự với query
        """
        logger.info(f"Tìm kiếm với query: '{query}', top_k={top_k}")
        print(f"[QDRANT] Tìm kiếm với query: '{query}', top_k={top_k}")
        
        # Kiểm tra xem collection có tồn tại không
        if not self._check_collection_exists():
            logger.warning(f"Collection '{self.collection_name}' không tồn tại. Không thể tìm kiếm.")
            print(f"[QDRANT] Collection '{self.collection_name}' không tồn tại. Không thể tìm kiếm.")
            return []
        
        try:
            # Thực hiện similarity search
            logger.info("Đang thực hiện similarity search...")
            print("[QDRANT] Đang thực hiện similarity search...")
            
            docs_with_scores = self.db.similarity_search_with_score(query, k=top_k)
            
            # Chuyển đổi kết quả sang định dạng phù hợp
            results = []
            for doc, score in docs_with_scores:
                product = {
                    "id": doc.metadata["product_id"],
                    "name": doc.metadata["name"],
                    "price": doc.metadata["price"],
                    "description": doc.page_content,
                    "image_url": doc.metadata.get("image_url", ""),
                    "category": doc.metadata.get("category", ""),
                    "status": doc.metadata.get("status", ""),
                    "quantity": doc.metadata.get("quantity", 0),
                    "relevance_score": 1 - score  # Convert distance to similarity score
                }
                results.append(product)
            
            logger.info(f"Tìm thấy {len(results)} kết quả")
            print(f"[QDRANT] Tìm thấy {len(results)} kết quả")
            return results
            
        except Exception as e:
            error_msg = f"Lỗi khi thực hiện tìm kiếm: {str(e)}"
            logger.error(error_msg)
            print(f"[QDRANT] {error_msg}")
            return []
    
    def clear(self):
        """
        Xóa toàn bộ dữ liệu trong vector database
        """
        logger.info(f"Bắt đầu xóa collection '{self.collection_name}'")
        print(f"[QDRANT] Bắt đầu xóa collection '{self.collection_name}'")
        
        try:
            if self._check_collection_exists():
                logger.info(f"Đang xóa collection '{self.collection_name}'...")
                print(f"[QDRANT] Đang xóa collection '{self.collection_name}'...")
                
                self.client.delete_collection(collection_name=self.collection_name)
                
                logger.info(f"Đã xóa collection '{self.collection_name}'")
                print(f"[QDRANT] Đã xóa collection '{self.collection_name}'")
            else:
                logger.warning(f"Collection '{self.collection_name}' không tồn tại, không cần xóa")
                print(f"[QDRANT] Collection '{self.collection_name}' không tồn tại, không cần xóa")
            
            # Tạo lại collection
            self._create_collection()
            self._init_db()
            
        except Exception as e:
            error_msg = f"Lỗi khi xóa collection: {str(e)}"
            logger.error(error_msg)
            print(f"[QDRANT] {error_msg}")
            traceback.print_exc()

# Singleton instance
vector_store = VectorStore() 