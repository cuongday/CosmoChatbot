from agents import Agent, Tool, Runner
from ..core.config import settings
from ..tools.cart_tools import (
    get_cart, create_order, get_order_info, 
    get_payment_info, get_my_orders
)
from ..tools.product_tools import get_product_by_id
from ..prompts.checkout_agent import CHECKOUT_AGENT_PROMPT
from ..core.hooks import CustomAgentHooks
from ..client.spring_client import spring_boot_client
from typing import List, Dict, Any, Optional

class CheckoutAgentWrapper:
    """
    Agent xử lý quá trình thanh toán và tạo đơn hàng
    """
    def __init__(self):
        # Tạo hooks cho checkout agent
        self.hooks = CustomAgentHooks("Checkout")
        
        # Tạo agent sử dụng OpenAI Agents SDK
        self.agent = Agent(
            name="Checkout Assistant",
            instructions=CHECKOUT_AGENT_PROMPT,
            model=settings.CHAT_MODEL,
            tools=[
                get_cart,           # Lấy thông tin giỏ hàng
                get_product_by_id,  # Lấy thông tin sản phẩm
                create_order,       # Tạo đơn hàng
                get_order_info,     # Lấy thông tin đơn hàng
                get_payment_info,   # Lấy thông tin thanh toán
                get_my_orders      # Lấy danh sách đơn hàng của tôi
            ],
            hooks=self.hooks
        )
    
    async def process(self, message: str, thread_id: str = None, user_id: str = None, auth_token: str = None):
        """
        Xử lý tin nhắn liên quan đến thanh toán
        
        Args:
            message: Tin nhắn của người dùng
            thread_id: ID cuộc trò chuyện
            user_id: ID người dùng
            auth_token: Token xác thực JWT
        """
        # Cập nhật token cho Spring Boot client
        spring_boot_client.update_auth_token(auth_token)
        
        # Kiểm tra giỏ hàng trước khi xử lý
        cart = spring_boot_client.get_cart()
        if not cart or not cart.get("items"):
            return {
                "message": "Giỏ hàng của bạn đang trống. Vui lòng thêm sản phẩm vào giỏ hàng trước khi thanh toán.",
                "source_documents": [],
                "thread_id": thread_id
            }
            
        # Sử dụng Runner để xử lý tin nhắn
        result = await Runner.run(self.agent, message)
        
        # Nếu có order_id trong kết quả, thêm thông tin đơn hàng vào source_documents
        source_documents = []
        if hasattr(result, 'tool_results'):
            for tool_result in result.tool_results:
                if tool_result.tool_name in ['create_order', 'get_order_info', 'get_payment_info']:
                    if isinstance(tool_result.output, dict):
                        source_documents.append(tool_result.output)
        
        return {
            "message": result.final_output,
            "source_documents": source_documents,
            "thread_id": thread_id
        }
        
    async def process_with_history(
        self, 
        message: str, 
        conversation_history: List[Dict[str, Any]], 
        thread_id: str = None, 
        user_id: str = None, 
        auth_token: str = None
    ) -> Dict[str, Any]:
        """
        Xử lý tin nhắn liên quan đến thanh toán với lịch sử trò chuyện
        
        Args:
            message: Tin nhắn của người dùng
            conversation_history: Lịch sử trò chuyện
            thread_id: ID cuộc trò chuyện
            user_id: ID người dùng
            auth_token: Token xác thực JWT
            
        Returns:
            Dict: Kết quả từ agent
        """
        # Cập nhật token cho Spring Boot client
        spring_boot_client.update_auth_token(auth_token)
        
        # Kiểm tra giỏ hàng trước khi xử lý
        cart = spring_boot_client.get_cart()
        if not cart or not cart.get("items"):
            return {
                "message": "Giỏ hàng của bạn đang trống. Vui lòng thêm sản phẩm vào giỏ hàng trước khi thanh toán.",
                "source_documents": [],
                "thread_id": thread_id
            }
        
        # Chuẩn bị ngữ cảnh từ lịch sử trò chuyện
        context = ""
        if conversation_history and len(conversation_history) > 0:
            context = "Đây là lịch sử trò chuyện trước đó:\n"
            for msg in conversation_history:
                role = "Người dùng" if msg["role"] == "user" else "Trợ lý"
                context += f"{role}: {msg['content']}\n"
            context += "\nDựa vào lịch sử trên, hãy trả lời tin nhắn mới này:\n"
        
        # Tạo tin nhắn với ngữ cảnh
        message_with_context = f"{context}{message}" if context else message
        
        # Sử dụng Runner để xử lý tin nhắn
        result = await Runner.run(self.agent, message_with_context)
        
        # Nếu có order_id trong kết quả, thêm thông tin đơn hàng vào source_documents
        source_documents = []
        if hasattr(result, 'tool_results'):
            for tool_result in result.tool_results:
                if tool_result.tool_name in ['create_order', 'get_order_info', 'get_payment_info']:
                    if isinstance(tool_result.output, dict):
                        source_documents.append(tool_result.output)
        
        return {
            "message": result.final_output,
            "source_documents": source_documents,
            "thread_id": thread_id
        }

# Singleton instance
checkout_agent = CheckoutAgentWrapper() 