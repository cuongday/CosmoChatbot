from agents import Agent, Tool, Runner
from ..core.config import settings
from ..tools.shop_tools import get_shop_info, get_shipping_info, get_return_policy, get_contact_info, get_user_orders, get_order_details
from ..prompts.shop_agent import SHOP_AGENT_PROMPT
from ..client.spring_client import spring_boot_client
from ..core.hooks import CustomAgentHooks
from typing import List, Dict, Any, Optional

class ShopAgentWrapper:
    """
    Agent xử lý các yêu cầu về thông tin cửa hàng, vận chuyển, chính sách
    """
    def __init__(self):
        # Tạo hooks cho shop agent
        self.hooks = CustomAgentHooks("Shop")
        
        # Tạo agent sử dụng OpenAI Agents SDK
        self.agent = Agent(
            name="Shop Assistant",
            instructions=SHOP_AGENT_PROMPT,
            model=settings.CHAT_MODEL,
            tools=[
                get_shop_info,
                get_shipping_info,
                get_return_policy,
                get_contact_info,
                get_user_orders,
                get_order_details
            ],
            hooks=self.hooks
        )
    
    async def process(self, message: str, thread_id: str = None, user_id: str = None, auth_token: str = None):
        """
        Xử lý tin nhắn từ người dùng
        
        Args:
            message: Tin nhắn người dùng
            thread_id: ID cuộc trò chuyện
            user_id: ID người dùng
            auth_token: Token xác thực JWT
        """
        # Cập nhật token cho Spring Boot client nếu cần
        spring_boot_client.update_auth_token(auth_token)
        
        # Sử dụng Runner từ OpenAI Agents SDK để xử lý tin nhắn
        result = await Runner.run(self.agent, message)
        
        # Cấu trúc kết quả để tương thích với API hiện tại
        return {
            "message": result.final_output,
            "source_documents": [],
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
        Xử lý tin nhắn liên quan đến cửa hàng với lịch sử trò chuyện
        
        Args:
            message: Tin nhắn của người dùng
            conversation_history: Lịch sử trò chuyện
            thread_id: ID cuộc trò chuyện
            user_id: ID người dùng
            auth_token: Token xác thực JWT
            
        Returns:
            Dict: Kết quả từ agent
        """
        # Cập nhật token xác thực cho spring_boot_client nếu có
        spring_boot_client.update_auth_token(auth_token)
        
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
        
        # Sử dụng Runner từ OpenAI Agents SDK để xử lý tin nhắn
        result = await Runner.run(self.agent, message_with_context)
        
        # Trả về kết quả
        return {
            "message": result.final_output,
            "source_documents": [],
            "thread_id": thread_id
        }

# Singleton instance
shop_agent = ShopAgentWrapper() 