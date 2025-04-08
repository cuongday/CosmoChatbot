from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
from typing import Optional, Dict, Any, List
from sqlmodel import Session
import json

# from ..core.security import verify_api_key
from ..core.config import settings
from ..agents.manager_agent import manager_agent, ManagerAgentWrapper
from ..agents.product_agent import product_agent, ProductAgentWrapper
from ..agents.cart_agent import cart_agent, CartAgentWrapper
from ..agents.shop_agent import shop_agent, ShopAgentWrapper
from ..agents.checkout_agent import checkout_agent, CheckoutAgentWrapper
from ..rag.vector_store import vector_store
from ..client.spring_client import spring_boot_client
from ..models.api_models import ChatRequest, ChatResponse, ProductRequest, ProductResponse, ShopRequest, ShopResponse, SyncRequest, AutoSyncRequest, SyncResponse
from ..db.database import get_session
from ..db.services import ConversationService
from ..db.models import Conversation, Message

router = APIRouter()

# Khởi tạo các agent
manager_agent = ManagerAgentWrapper()
product_agent = ProductAgentWrapper()
cart_agent = CartAgentWrapper()
shop_agent = ShopAgentWrapper()
checkout_agent = CheckoutAgentWrapper()

@router.post("/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    session: Session = Depends(get_session)
) -> ChatResponse:
    """
    Endpoint xử lý tin nhắn chat từ người dùng
    """
    try:
        # Cập nhật token cho spring boot client nếu có
        if request.auth_token:
            spring_boot_client.update_auth_token(request.auth_token)
            
        # Khởi tạo conversation service
        conversation_service = ConversationService(session)
        
        # Xử lý conversation_id/thread_id
        thread_id = request.thread_id
        if not thread_id and request.user_id:
            # Tạo conversation mới nếu chưa có
            conversation = conversation_service.create_conversation(
                user_id=request.user_id,
                title=request.thread_title
            )
            thread_id = conversation.id
            
        # Lưu tin nhắn của người dùng
        if thread_id:
            conversation_service.add_message(
                conversation_id=thread_id,
                role="user",
                content=request.message,
                metadata={"user_id": request.user_id} if request.user_id else None
            )
            
            # Lấy lịch sử trò chuyện từ database
            conversation_history = conversation_service.get_conversation_history(thread_id)
        else:
            conversation_history = []
            
        # Phân tích yêu cầu bằng Manager Agent
        manager_response = await manager_agent.process(
            message=request.message,
            thread_id=thread_id,
            user_id=request.user_id,
            auth_token=request.auth_token
        )
        
        # Kiểm tra nếu manager quyết định chuyển tiếp
        if manager_response.get("handoff", False):
            agent_type = manager_response.get("target_agent", "")
            
            # Chọn agent phù hợp để xử lý
            if agent_type == "product":
                agent = product_agent
            elif agent_type == "cart":
                agent = cart_agent
            elif agent_type == "shop":
                agent = shop_agent
            elif agent_type == "checkout":
                agent = checkout_agent
            else:
                raise ValueError(f"Agent type không hợp lệ: {agent_type}")
                
            # Xử lý tin nhắn với agent đã chọn
            if thread_id and conversation_history:
                # Có lịch sử trò chuyện
                response = await agent.process_with_history(
                    message=request.message,
                    conversation_history=conversation_history,
                    thread_id=thread_id,
                    user_id=request.user_id,
                    auth_token=request.auth_token
                )
            else:
                # Không có lịch sử trò chuyện
                response = await agent.process(
                    message=request.message,
                    thread_id=thread_id,
                    user_id=request.user_id,
                    auth_token=request.auth_token
                )
                
            # Lưu câu trả lời từ agent vào database
            if thread_id:
                conversation_service.add_message(
                    conversation_id=thread_id,
                    role="assistant",
                    content=response.get("message", ""),
                    metadata={"agent": agent_type}
                )
                
            return ChatResponse(
                message=response.get("message", ""),
                source_documents=response.get("source_documents", []),
                thread_id=thread_id
            )
        else:
            # Nếu không có chuyển tiếp, lưu và trả về response trực tiếp từ manager
            if thread_id:
                conversation_service.add_message(
                    conversation_id=thread_id,
                    role="assistant",
                    content=manager_response.get("message", ""),
                    metadata={"agent": "manager"}
                )
                
            return ChatResponse(
                message=manager_response.get("message", ""),
                source_documents=manager_response.get("source_documents", []),
                thread_id=thread_id
            )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Lỗi khi xử lý tin nhắn: {str(e)}"
        )

@router.post("/sync", response_model=SyncResponse)
async def sync_data(request: SyncRequest, background_tasks: BackgroundTasks):
    """
    Endpoint đồng bộ dữ liệu từ MySQL sang Vector DB
    """
    try:
        if request.type == "products":
            # Thêm task đồng bộ vào background task
            background_tasks.add_task(vector_store.add_products, request.data)
            
            return SyncResponse(
                status="success",
                count=len(request.data),
                message=f"Đã đồng bộ {len(request.data)} sản phẩm vào vector database"
            )
        else:
            return SyncResponse(
                status="error",
                count=0,
                message="Loại dữ liệu không được hỗ trợ"
            )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi đồng bộ dữ liệu: {str(e)}")

@router.post("/auto-sync", response_model=SyncResponse)
async def auto_sync_data(request: AutoSyncRequest, background_tasks: BackgroundTasks):
    """
    Endpoint tự động đồng bộ dữ liệu từ Spring Boot API sang Vector DB
    """
    print(f"[AUTO-SYNC] Bắt đầu quá trình đồng bộ tự động loại: {request.type}, limit: {request.limit}")
    try:
        if request.type == "products":
            # Lấy dữ liệu sản phẩm từ Spring Boot API
            print(f"[AUTO-SYNC] Đang lấy dữ liệu từ Spring Boot API...")
            products = spring_boot_client.get_all_products(limit=request.limit)
            
            if not products:
                print(f"[AUTO-SYNC] Không thể lấy dữ liệu sản phẩm từ Spring Boot API")
                return SyncResponse(
                    status="error",
                    count=0,
                    message="Không thể lấy dữ liệu sản phẩm từ Spring Boot API"
                )
            
            print(f"[AUTO-SYNC] Lấy được {len(products)} sản phẩm từ API")
            print(f"[AUTO-SYNC] Đang thêm dữ liệu vào vector database...")
            
            # Gọi trực tiếp hàm thay vì qua background task để dễ debug
            try:
                # Hiển thị cấu hình Qdrant
                print(f"[AUTO-SYNC] Qdrant config: host={settings.QDRANT_HOST}, port={settings.QDRANT_PORT}, collection={settings.QDRANT_COLLECTION_NAME}")
                
                # Thêm dữ liệu trực tiếp thay vì qua background task
                vector_store.add_products(products)
                
                print(f"[AUTO-SYNC] Hoàn thành quá trình thêm dữ liệu vào vector database")
            except Exception as e:
                print(f"[AUTO-SYNC] Lỗi khi thêm dữ liệu vào vector database: {str(e)}")
                return SyncResponse(
                    status="error",
                    count=0,
                    message=f"Lỗi khi thêm dữ liệu vào vector database: {str(e)}"
                )
            
            return SyncResponse(
                status="success",
                count=len(products),
                message=f"Đã tự động đồng bộ {len(products)} sản phẩm vào vector database"
            )
        else:
            print(f"[AUTO-SYNC] Loại dữ liệu '{request.type}' không được hỗ trợ")
            return SyncResponse(
                status="error",
                count=0,
                message="Loại dữ liệu không được hỗ trợ"
            )
    except Exception as e:
        print(f"[AUTO-SYNC] Lỗi đồng bộ dữ liệu: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Lỗi đồng bộ dữ liệu: {str(e)}")

@router.get("/health")
async def health_check():
    """
    Endpoint kiểm tra trạng thái hoạt động của service
    """
    return {"status": "ok", "version": "1.0.0"}

@router.get("/conversations/{user_id}", response_model=List[Dict[str, Any]])
async def get_user_conversations(user_id: str, session: Session = Depends(get_session)):
    """
    Lấy danh sách các cuộc trò chuyện của người dùng
    """
    try:
        conversation_service = ConversationService(session)
        conversations = conversation_service.get_conversation_by_user(user_id)
        
        return [
            {
                "id": str(conv.id),
                "title": conv.title,
                "created_at": conv.created_at.isoformat(),
                "updated_at": conv.updated_at.isoformat()
            }
            for conv in conversations
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi lấy danh sách cuộc trò chuyện: {str(e)}")

@router.get("/conversations/{conversation_id}/messages", response_model=List[Dict[str, Any]])
async def get_conversation_messages(conversation_id: str, limit: int = 50, session: Session = Depends(get_session)):
    """
    Lấy danh sách tin nhắn trong một cuộc trò chuyện
    """
    try:
        conversation_service = ConversationService(session)
        messages = conversation_service.get_messages(conversation_id, limit)
        
        return [
            {
                "id": str(msg.id),
                "role": msg.role,
                "content": msg.content,
                "created_at": msg.created_at.isoformat(),
                "metadata": json.loads(msg.metadata) if msg.metadata else {}
            }
            for msg in messages
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi lấy tin nhắn: {str(e)}") 