from pydantic import BaseModel
from typing import Optional, List, Dict, Any


class ChatRequest(BaseModel):
    """
    Request model for chat API
    """
    message: str
    thread_id: Optional[str] = None
    thread_title: Optional[str] = None
    user_id: Optional[str] = None
    auth_token: Optional[str] = None


class ChatResponse(BaseModel):
    """
    Response model for chat API
    """
    message: str
    source_documents: Optional[List[Dict[str, Any]]] = None
    conversation_id: Optional[str] = None  # Trả về conversation_id cho frontend


class ProductRequest(BaseModel):
    """
    Request model for product API
    """
    message: str
    thread_id: Optional[str] = None
    thread_title: Optional[str] = None
    user_id: Optional[str] = None
    auth_token: Optional[str] = None


class ProductResponse(BaseModel):
    """
    Response model for product API
    """
    message: str
    source_documents: Optional[List[Dict[str, Any]]] = None
    conversation_id: Optional[str] = None


class ShopRequest(BaseModel):
    """
    Request model for shop assistant API
    """
    message: str
    thread_id: Optional[str] = None
    thread_title: Optional[str] = None
    user_id: Optional[str] = None
    auth_token: Optional[str] = None


class ShopResponse(BaseModel):
    """
    Response model for shop assistant API
    """
    message: str
    source_documents: Optional[List[Dict[str, Any]]] = None
    conversation_id: Optional[str] = None


class SyncRequest(BaseModel):
    """
    Request model for synchronization API
    """
    type: str
    data: List[Dict[str, Any]]


class SyncResponse(BaseModel):
    """
    Response model for synchronization API
    """
    status: str
    count: int
    message: str


class AutoSyncRequest(BaseModel):
    """
    Request model for auto-synchronization API
    """
    type: str
    limit: Optional[int] = 100 