from agents import Agent, Runner, handoff, Tool, RunContextWrapper
from ..core.config import settings
from ..tools.manager_tools import get_assistant_info
from ..prompts.manager_agent import MANAGER_AGENT_PROMPT
from .product_agent import product_agent
from .cart_agent import cart_agent
from .shop_agent import shop_agent
from .checkout_agent import checkout_agent
from ..core.hooks import CustomAgentHooks
from ..client.spring_client import spring_boot_client
from typing import List, Dict, Any, Optional
import asyncio

class ManagerAgentWrapper:
    """
    Agent quản lý xử lý phân loại tin nhắn và chuyển tiếp giữa các agent chuyên biệt
    """
    def __init__(self):
        # Tạo hooks cho manager agent
        self.hooks = CustomAgentHooks("Manager")
        
        # Tạo agent sử dụng OpenAI Agents SDK
        self.agent = Agent(
            name="Manager Assistant",
            instructions=MANAGER_AGENT_PROMPT,
            model=settings.CHAT_MODEL,
            tools=[
                get_assistant_info  # Tool cung cấp thông tin về các assistant có sẵn
            ],
            hooks=self.hooks
        )
        
        # Định nghĩa handoffs theo cú pháp chính thức của OpenAI Agents SDK
        self.product_handoff = product_agent.agent.as_tool(
            tool_name="consult_product_expert",
            tool_description="Chuyển câu hỏi cho chuyên gia sản phẩm bánh khi khách hàng hỏi về sản phẩm"
        )
        
        self.cart_handoff = cart_agent.agent.as_tool(
            tool_name="consult_cart_expert",
            tool_description="Chuyển câu hỏi cho chuyên gia giỏ hàng khi khách hàng muốn đặt bánh hoặc thanh toán"
        )
        
        self.shop_handoff = shop_agent.agent.as_tool(
            tool_name="consult_shop_expert",
            tool_description="Chuyển câu hỏi cho chuyên gia cửa hàng khi khách hàng hỏi về cửa hàng"
        )
        
        self.checkout_handoff = checkout_agent.agent.as_tool(
            tool_name="consult_checkout_expert",
            tool_description="Chuyển câu hỏi cho chuyên gia thanh toán khi khách hàng muốn thanh toán hoặc tạo đơn hàng"
        )
    
    async def _analyze_message(self, message: str, context: str = "") -> str:
        """
        Phân tích tin nhắn để xác định agent phù hợp
        """
        message_with_context = f"{context}{message}" if context else message
        
        analysis_hooks = CustomAgentHooks("Analyzer")
        analysis_agent = Agent(
            name="Analyzer",
            instructions="""
            Phân tích tin nhắn của người dùng và xác định nội dung thuộc loại nào:
            1. product - Nếu liên quan đến sản phẩm, tìm kiếm, so sánh giá
            2. cart - Nếu liên quan đến giỏ hàng, thêm/xóa sản phẩm
            3. shop - Nếu liên quan đến thông tin cửa hàng
            4. checkout - Nếu liên quan đến thanh toán, tạo đơn hàng
            5. unknown - Nếu không rõ ràng
            
            Chỉ trả về một trong các giá trị trên, không thêm bất kỳ thông tin nào khác.
            """,
            model=settings.CHAT_MODEL,
            tools=[],
            hooks=analysis_hooks
        )
        
        result = await Runner.run(analysis_agent, message_with_context)
        return result.final_output.strip().lower()

    async def process(self, message: str, thread_id: str = None, user_id: str = None, auth_token: str = None):
        """
        Xử lý tin nhắn từ người dùng và quyết định chuyển tiếp đến agent phù hợp
        
        Args:
            message: Tin nhắn của người dùng
            thread_id: ID cuộc trò chuyện
            user_id: ID người dùng
            auth_token: Token xác thực JWT
        """
        # Cập nhật token xác thực cho spring_boot_client nếu có
        spring_boot_client.update_auth_token(auth_token)
        
        # Phân tích tin nhắn
        analysis_result = await self._analyze_message(message)
        
        # Chuyển tiếp dựa trên kết quả phân tích
        if analysis_result == "product":
            return {
                "handoff": True,
                "target_agent": "product",
                "original_message": message,
                "thread_id": thread_id,
                "user_id": user_id,
                "auth_token": auth_token
            }
        elif analysis_result == "cart":
            return {
                "handoff": True,
                "target_agent": "cart",
                "original_message": message,
                "thread_id": thread_id,
                "user_id": user_id,
                "auth_token": auth_token
            }
        elif analysis_result == "shop":
            return {
                "handoff": True,
                "target_agent": "shop",
                "original_message": message,
                "thread_id": thread_id,
                "user_id": user_id,
                "auth_token": auth_token
            }
        elif analysis_result == "checkout":
            return {
                "handoff": True,
                "target_agent": "checkout",
                "original_message": message,
                "thread_id": thread_id,
                "user_id": user_id,
                "auth_token": auth_token
            }
        
        # Nếu không rõ ràng, sử dụng orchestrator
        orchestrator = Agent(
            name="Orchestrator",
            instructions=MANAGER_AGENT_PROMPT,
            model=settings.CHAT_MODEL,
            tools=[
                get_assistant_info,
                self.product_handoff,
                self.cart_handoff,
                self.shop_handoff,
                self.checkout_handoff
            ],
            hooks=self.hooks
        )
        
        result = await Runner.run(orchestrator, message)
        
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
        Xử lý tin nhắn từ người dùng với lịch sử trò chuyện và quyết định chuyển tiếp đến agent phù hợp
        
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
        
        # Chuẩn bị ngữ cảnh
        context = ""
        if conversation_history and len(conversation_history) > 0:
            context = "Đây là lịch sử trò chuyện trước đó:\n"
            for msg in conversation_history:
                role = "Người dùng" if msg["role"] == "user" else "Trợ lý"
                context += f"{role}: {msg['content']}\n"
            context += "\nDựa vào lịch sử trên, hãy trả lời tin nhắn mới này:\n"
        
        # Phân tích tin nhắn với ngữ cảnh
        analysis_result = await self._analyze_message(message, context)
        
        # Chuyển tiếp dựa trên kết quả phân tích
        if analysis_result == "product":
            return {
                "handoff": True,
                "target_agent": "product",
                "original_message": message,
                "thread_id": thread_id,
                "user_id": user_id,
                "auth_token": auth_token
            }
        elif analysis_result == "cart":
            return {
                "handoff": True,
                "target_agent": "cart",
                "original_message": message,
                "thread_id": thread_id,
                "user_id": user_id,
                "auth_token": auth_token
            }
        elif analysis_result == "shop":
            return {
                "handoff": True,
                "target_agent": "shop",
                "original_message": message,
                "thread_id": thread_id,
                "user_id": user_id,
                "auth_token": auth_token
            }
        elif analysis_result == "checkout":
            return {
                "handoff": True,
                "target_agent": "checkout",
                "original_message": message,
                "thread_id": thread_id,
                "user_id": user_id,
                "auth_token": auth_token
            }
            
        # Nếu không rõ ràng, sử dụng orchestrator với ngữ cảnh
        message_with_context = f"{context}{message}" if context else message
        
        orchestrator = Agent(
            name="Orchestrator",
            instructions=MANAGER_AGENT_PROMPT,
            model=settings.CHAT_MODEL,
            tools=[
                get_assistant_info,
                self.product_handoff,
                self.cart_handoff,
                self.shop_handoff,
                self.checkout_handoff
            ],
            hooks=self.hooks
        )
        
        result = await Runner.run(orchestrator, message_with_context)
        
        return {
            "message": result.final_output,
            "source_documents": [],
            "thread_id": thread_id
        }

# Singleton instance
manager_agent = ManagerAgentWrapper() 