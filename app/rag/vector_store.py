import os
import logging
from typing import List, Dict, Any, Optional
from langchain_milvus import Milvus
from langchain.schema import Document
from .embeddings import embedding_provider
from ..core.config import settings
from pymilvus import utility, Collection, connections
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
        self.uri = settings.MILVUS_URI
        
        # Đảm bảo URI có định dạng đúng với protocol
        if self.uri and not (self.uri.startswith('http://') or self.uri.startswith('https://')):
            self.uri = f"http://{self.uri}"
            logger.info(f"Đã thêm protocol 'http://' vào Milvus URI: {self.uri}")
            print(f"[MILVUS] Đã thêm protocol 'http://' vào Milvus URI: {self.uri}")
            
        self.collection_name = settings.MILVUS_COLLECTION_NAME
        self.force_recreate = settings.MILVUS_FORCE_RECREATE
        
        logger.info(f"Vector Store được khởi tạo với: uri={self.uri}, collection={self.collection_name}")
        print(f"[MILVUS] Khởi tạo Milvus client với uri={self.uri}, collection={self.collection_name}")
        
        # Kết nối đến Milvus
        self.connection_name = "default"
        self._connect_to_milvus()
        
        # Khởi tạo vector store
        self._init_vector_store()
    
    def _ensure_directory(self):
        """
        Đảm bảo thư mục tồn tại
        """
        os.makedirs(self.persist_directory, exist_ok=True)
        logger.info(f"Thư mục {self.persist_directory} đã được tạo hoặc đã tồn tại")
        
    def _connect_to_milvus(self):
        """
        Kết nối đến Milvus server
        """
        try:
            logger.info(f"Kết nối tới Milvus server: {self.uri}")
            print(f"[MILVUS] Kết nối tới Milvus server: {self.uri}")
            
            # Đảm bảo URI có định dạng đúng (http://host:port)
            connections.connect(
                alias=self.connection_name,
                uri=self.uri
            )
            logger.info(f"Kết nối thành công đến Milvus: {self.uri}")
            print(f"[MILVUS] Kết nối thành công đến Milvus: {self.uri}")
        except Exception as e:
            logger.error(f"Lỗi kết nối đến Milvus: {str(e)}")
            print(f"[MILVUS] Lỗi kết nối đến Milvus: {str(e)}")
            traceback.print_exc()
            raise
    
    def _check_collection_exists(self) -> bool:
        """
        Kiểm tra xem collection đã tồn tại chưa
        """
        try:
            # Sử dụng PyMilvus utility để kiểm tra collection
            exists = utility.has_collection(self.collection_name)
            logger.info(f"Kiểm tra collection '{self.collection_name}': {'Tồn tại' if exists else 'Không tồn tại'}")
            print(f"[MILVUS] Kiểm tra collection '{self.collection_name}': {'Tồn tại' if exists else 'Không tồn tại'}")
            return exists
        except Exception as e:
            logger.error(f"Lỗi kiểm tra collection: {str(e)}")
            print(f"[MILVUS] Lỗi kiểm tra collection: {str(e)}")
            return False
    
    def _init_vector_store(self):
        """
        Khởi tạo vector store
        """
        try:
            logger.info(f"Khởi tạo Langchain Milvus vector store với collection '{self.collection_name}'")
            print(f"[MILVUS] Khởi tạo Langchain Milvus vector store với collection '{self.collection_name}'")
            
            # Kiểm tra collection tồn tại
            exists = self._check_collection_exists()
            
            # Xóa collection cũ nếu force_recreate=True
            if exists and self.force_recreate:
                logger.info(f"Xóa collection '{self.collection_name}' cũ theo yêu cầu force_recreate")
                print(f"[MILVUS] Xóa collection '{self.collection_name}' cũ theo yêu cầu force_recreate")
                utility.drop_collection(self.collection_name)
                exists = False
            
            # Tạo mới collection nếu chưa tồn tại
            if not exists:
                logger.info(f"Collection '{self.collection_name}' không tồn tại. Đang tạo mới...")
                print(f"[MILVUS] Collection '{self.collection_name}' không tồn tại. Đang tạo mới...")
                
                # Sử dụng langchain_milvus để tạo vector store mới
                # Kết nối đã được thiết lập ở trên, chỉ cần chỉ định connection_args cho rõ ràng
                connection_args = {"uri": self.uri}
                
                self.vector_store = Milvus(
                    embedding_function=self.embedding_function,
                    collection_name=self.collection_name,
                    connection_args=connection_args,
                    auto_id=True  # Tự động tạo ID cho văn bản
                )
                
                print(f"[MILVUS] Đã tạo mới collection '{self.collection_name}' thành công")
            else:
                # Kết nối đến collection đã tồn tại
                connection_args = {"uri": self.uri}
                
                self.vector_store = Milvus(
                    embedding_function=self.embedding_function,
                    collection_name=self.collection_name,
                    connection_args=connection_args,
                    auto_id=True  # Tự động tạo ID cho văn bản
                )
            
            logger.info("Vector store đã sẵn sàng")
            print("[MILVUS] Vector store đã sẵn sàng")
        except Exception as e:
            logger.error(f"Lỗi khởi tạo vector store: {str(e)}")
            print(f"[MILVUS] Lỗi khởi tạo vector store: {str(e)}")
            traceback.print_exc()
            raise
    
    def add_documents(self, documents: List[Document]):
        """
        Thêm tài liệu vào vector store
        """
        try:
            # Tạo IDs cho documents nếu cần
            ids = [str(i) for i in range(len(documents))]
            self.vector_store.add_documents(documents, ids=ids)
            return True
        except Exception as e:
            logger.error(f"Lỗi khi thêm tài liệu: {str(e)}")
            return False
    
    def add_products(self, products: List[Dict[str, Any]]):
        """
        Thêm các sản phẩm vào vector database
        """
        logger.info(f"Bắt đầu thêm {len(products) if products else 0} sản phẩm vào vector database")
        print(f"[MILVUS] Bắt đầu thêm {len(products) if products else 0} sản phẩm vào vector database")
        
        if not products:
            logger.warning("Không có sản phẩm nào để thêm vào vector database")
            print("[MILVUS] Không có sản phẩm nào để thêm vào vector database")
            return
        
        try:    
            documents = []
            ids = [] # Danh sách IDs cho documents
            
            for idx, product in enumerate(products):
                try:
                    # Lấy ID của sản phẩm để log
                    product_id = product.get("id", "không có ID")
                    
                    # Tạo văn bản phong phú từ thông tin sản phẩm
                    product_text = f"Sản phẩm {product.get('name', '')} có mã sản phẩm {product.get('id', '')}. "
                    product_text += f"Mô tả: {product.get('description', '')}. "
                    product_text += f"Giá bán: {product.get('sellPrice', product.get('price', 0))} VNĐ. "
                    
                    if product.get('quantity') is not None:
                        product_text += f"Số lượng tồn kho: {product.get('quantity')}. "
                    
                    if product.get('status') is not None:
                        product_text += f"Trạng thái: {product.get('status')}. "
                    
                    if product.get('category') is not None:
                        product_text += f"Thuộc danh mục: {product.get('category', {}).get('name', '')}. "
                    
                    # Thêm thông tin nhà cung cấp nếu có
                    if product.get('supplier') is not None:
                        product_text += f"Nhà cung cấp: {product.get('supplier', {}).get('name', '')}. "
                    
                    # Log mẫu cho vài sản phẩm đầu tiên
                    if idx < 2:
                        logger.info(f"Mẫu sản phẩm {product_id}: {product_text[:100]}...")
                        print(f"[MILVUS] Mẫu sản phẩm {product_id}: {product_text[:100]}...")
                    
                    # Tạo document với metadata
                    doc = Document(
                        page_content=product_text,
                        metadata={
                            "product_id": str(product.get("id", "")),  # Đảm bảo ID dạng string
                            "name": product.get("name", ""),
                            "price": float(product.get("sellPrice", product.get("price", 0))),
                            "image_url": product.get("image", product.get("imageUrl", "")),
                            "category": product.get("category", {}).get("name", ""),
                            "status": product.get("status", ""),
                            "quantity": int(product.get("quantity", 0)),
                            "supplier_name": product.get("supplier", {}).get("name", ""),
                            "created_at": str(product.get("createdAt", "")),
                            "updated_at": str(product.get("updatedAt", ""))
                        }
                    )
                    documents.append(doc)
                    
                    # Tạo ID cho document (sử dụng ID sản phẩm nếu có hoặc tạo mới)
                    doc_id = f"product_{product.get('id', str(idx))}"
                    ids.append(doc_id)
                    
                except Exception as e:
                    logger.error(f"Lỗi khi xử lý sản phẩm {product.get('id', 'không có ID')}: {str(e)}")
                    print(f"[MILVUS] Lỗi khi xử lý sản phẩm {product.get('id', 'không có ID')}: {str(e)}")
                    # Tiếp tục với sản phẩm tiếp theo
            
            if not documents:
                logger.warning("Không có documents nào được tạo từ sản phẩm")
                print("[MILVUS] Không có documents nào được tạo từ sản phẩm")
                return
                
            logger.info(f"Đã chuẩn bị {len(documents)} documents để thêm vào collection '{self.collection_name}'")
            print(f"[MILVUS] Đã chuẩn bị {len(documents)} documents để thêm vào collection '{self.collection_name}'")
            
            # Thêm documents vào vector database với IDs
            self.vector_store.add_documents(documents, ids=ids)
            
            logger.info(f"Đã thêm thành công {len(documents)} documents vào collection '{self.collection_name}'")
            print(f"[MILVUS] Đã thêm thành công {len(documents)} documents vào collection '{self.collection_name}'")
            
        except Exception as e:
            error_msg = f"Lỗi khi thêm sản phẩm vào vector database: {str(e)}"
            logger.error(error_msg)
            print(f"[MILVUS] {error_msg}")
            traceback.print_exc()
            raise
    
    def search(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Tìm kiếm sản phẩm tương tự với query
        """
        logger.info(f"Tìm kiếm với query: '{query}', top_k={top_k}")
        print(f"[MILVUS] Tìm kiếm với query: '{query}', top_k={top_k}")
        
        try:
            # Thực hiện similarity search
            logger.info("Đang thực hiện similarity search...")
            print("[MILVUS] Đang thực hiện similarity search...")
            
            docs_with_scores = self.vector_store.similarity_search_with_score(query, k=top_k)
            
            # Chuyển đổi kết quả sang định dạng phù hợp
            results = []
            for doc, score in docs_with_scores:
                # Với Milvus, score là khoảng cách nên cần đảo lại để tính relevance
                product = {
                    "id": doc.metadata["product_id"],
                    "name": doc.metadata["name"],
                    "price": doc.metadata["price"],
                    "description": doc.page_content,
                    "image_url": doc.metadata.get("image_url", ""),
                    "category": doc.metadata.get("category", ""),
                    "status": doc.metadata.get("status", ""),
                    "quantity": doc.metadata.get("quantity", 0),
                    "relevance_score": 1.0 - score / 100.0 if score < 100 else 0.0  # Chuẩn hóa score
                }
                results.append(product)
            
            logger.info(f"Tìm thấy {len(results)} kết quả")
            print(f"[MILVUS] Tìm thấy {len(results)} kết quả")
            return results
            
        except Exception as e:
            error_msg = f"Lỗi khi thực hiện tìm kiếm: {str(e)}"
            logger.error(error_msg)
            print(f"[MILVUS] {error_msg}")
            return []
    
    def clear(self):
        """
        Xóa toàn bộ dữ liệu trong vector database
        """
        logger.info(f"Bắt đầu xóa collection '{self.collection_name}'")
        print(f"[MILVUS] Bắt đầu xóa collection '{self.collection_name}'")
        
        try:
            # Kiểm tra collection tồn tại
            if self._check_collection_exists():
                # Xóa collection
                utility.drop_collection(self.collection_name)
                logger.info(f"Đã xóa collection '{self.collection_name}'")
                print(f"[MILVUS] Đã xóa collection '{self.collection_name}'")
                
                # Tạo lại collection
                logger.info(f"Đang tạo lại collection '{self.collection_name}'")
                print(f"[MILVUS] Đang tạo lại collection '{self.collection_name}'")
                
                # Tạo collection mới
                connection_args = {"uri": self.uri}
                self.vector_store = Milvus(
                    embedding_function=self.embedding_function,
                    collection_name=self.collection_name,
                    connection_args=connection_args,
                    auto_id=True
                )
                
                logger.info(f"Đã tạo lại collection '{self.collection_name}' thành công")
                print(f"[MILVUS] Đã tạo lại collection '{self.collection_name}' thành công")
            else:
                logger.info(f"Collection '{self.collection_name}' không tồn tại, không cần xóa")
                print(f"[MILVUS] Collection '{self.collection_name}' không tồn tại, không cần xóa")
                
        except Exception as e:
            error_msg = f"Lỗi khi xóa collection: {str(e)}"
            logger.error(error_msg)
            print(f"[MILVUS] {error_msg}")
            traceback.print_exc()

# Singleton instance
vector_store = VectorStore() 