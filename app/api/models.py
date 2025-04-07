from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any

class ChatRequest(BaseModel):
    """
    Request model cho API chat
    """
    message: str = Field(..., description="Tin nhắn từ người dùng")
    thread_id: str = Field(..., description="ID của cuộc hội thoại")
    user_id: Optional[str] = Field(None, description="ID của người dùng")
    auth_token: Optional[str] = Field(None, description="Token JWT để xác thực")

class Product(BaseModel):
    """
    Model đại diện cho sản phẩm
    """
    id: str
    name: str
    price: float
    description: Optional[str] = None
    image_url: Optional[str] = None
    category: Optional[str] = None
    relevance_score: Optional[float] = None

class Action(BaseModel):
    """
    Model đại diện cho hành động có thể thực hiện
    """
    type: str = Field(..., description="Loại hành động (add_to_cart, checkout, view_product)")
    value: Dict[str, Any] = Field(..., description="Dữ liệu của hành động")

class ChatResponse(BaseModel):
    """
    Response model cho API chat
    """
    response: str = Field(..., description="Phản hồi từ chatbot")
    products: Optional[List[Product]] = Field([], description="Danh sách sản phẩm liên quan")
    actions: Optional[List[Action]] = Field([], description="Danh sách hành động có thể thực hiện")

class SyncRequest(BaseModel):
    """
    Request model cho API đồng bộ dữ liệu
    """
    type: str = Field(..., description="Loại dữ liệu (products, categories)")
    data: List[Dict[str, Any]] = Field(..., description="Dữ liệu cần đồng bộ")

class SyncResponse(BaseModel):
    """
    Response model cho API đồng bộ dữ liệu
    """
    status: str = Field(..., description="Trạng thái của quá trình đồng bộ")
    count: int = Field(..., description="Số lượng item đã đồng bộ")
    message: Optional[str] = Field(None, description="Thông báo bổ sung")

class AutoSyncRequest(BaseModel):
    """
    Request model cho API tự động đồng bộ dữ liệu từ Spring Boot
    """
    type: str = Field(..., description="Loại dữ liệu cần đồng bộ (products, categories)")
    limit: Optional[int] = Field(100, description="Số lượng item tối đa cần đồng bộ") 