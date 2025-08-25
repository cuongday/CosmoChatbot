from agents import Agent, Runner
from typing import Any, Dict, List

from ..client.spring_client import spring_boot_client
from ..core.config import settings
from ..core.hooks import CustomAgentHooks
from ..prompts.manager_agent import MANAGER_AGENT_PROMPT
from ..tools.manager_tools import get_assistant_info
from .cart_agent import cart_agent
from .checkout_agent import checkout_agent
from .product_agent import product_agent
from .shop_agent import shop_agent

class ManagerAgentWrapper:
    """
    Agent quản lý xử lý phân loại tin nhắn và chuyển tiếp giữa các agent chuyên biệt
    """
    def __init__(self):
        # Tạo hooks cho manager agent
        self.hooks = CustomAgentHooks("Manager")
        
        # Định nghĩa các agent khác như tools
        self.product_tool = product_agent.agent.as_tool(
            tool_name="consult_product_expert",
            tool_description="Chuyển câu hỏi cho chuyên gia sản phẩm khi khách hàng hỏi về thông tin sản phẩm, so sánh sản phẩm, tìm kiếm sản phẩm"
        )
        
        self.cart_tool = cart_agent.agent.as_tool(
            tool_name="consult_cart_expert",
            tool_description="Chuyển câu hỏi cho chuyên gia giỏ hàng khi khách hàng muốn thêm sản phẩm vào giỏ hàng, xem giỏ hàng, sửa giỏ hàng"
        )
        
        self.shop_tool = shop_agent.agent.as_tool(
            tool_name="consult_shop_expert",
            tool_description="Chuyển câu hỏi cho chuyên gia cửa hàng khi khách hàng hỏi về thông tin cửa hàng, chính sách vận chuyển, đổi trả"
        )
        
        self.checkout_tool = checkout_agent.agent.as_tool(
            tool_name="consult_checkout_expert",
            tool_description="Chuyển câu hỏi cho chuyên gia thanh toán khi khách hàng muốn thanh toán, tạo đơn hàng, xem thông tin đơn hàng"
        )
        
        # Tạo agent chính sử dụng các agent khác như tools
        self.agent = Agent(
            name="Manager Assistant",
            instructions=MANAGER_AGENT_PROMPT,
            model=settings.CHAT_MODEL,
            tools=[
                get_assistant_info,
                self.product_tool,
                self.cart_tool,
                self.shop_tool,
                self.checkout_tool
            ],
            hooks=self.hooks
        )
        
        # Tạo agent phân tích riêng biệt
        self.analysis_agent = Agent(
            name="Analyzer",
            instructions="""
            Phân tích tin nhắn của người dùng và xác định nội dung thuộc loại nào:
            1. product - Nếu liên quan đến sản phẩm, tìm kiếm, so sánh giá, thông tin về bánh
            2. cart - Nếu liên quan đến giỏ hàng, thêm/xóa sản phẩm
            3. shop - Nếu liên quan đến thông tin cửa hàng
            4. checkout - Nếu liên quan đến thanh toán, tạo đơn hàng
            
            QUAN TRỌNG: Bạn PHẢI chọn một trong bốn loại trên. KHÔNG BAO GIỜ trả về "unknown".
            Nếu tin nhắn mơ hồ hoặc không rõ ràng, hãy chọn "product" làm mặc định.
            
            Chỉ trả về một trong bốn giá trị: product, cart, shop, checkout. Không thêm bất kỳ thông tin nào khác.
            """,
            model=settings.CHAT_MODEL,
            hooks=CustomAgentHooks("Analyzer")
        )
    
    async def _analyze_message(self, message: str) -> str:
        """
        Phân tích tin nhắn để xác định agent phù hợp
        """
        result = await Runner.run(self.analysis_agent, message)
        analysis_result = result.final_output.strip().lower()
        
        # Nếu kết quả là unknown hoặc không thuộc các loại được định nghĩa,
        # mặc định sử dụng product agent (theo hướng dẫn trong prompt)
        if analysis_result not in ["product", "cart", "shop", "checkout"]:
            return "product"
            
        return analysis_result

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
        if analysis_result in ["product", "cart", "shop", "checkout"]:
            return {
                "handoff": True,
                "target_agent": analysis_result,
                "original_message": message,
                "thread_id": thread_id,
                "user_id": user_id,
                "auth_token": auth_token
            }
        
        # Không nên đạt tới đây vì _analyze_message luôn trả về một trong các giá trị trên
        # Nhưng để đảm bảo, vẫn sử dụng Manager Agent để xử lý
        result = await Runner.run(self.agent, message)
        
        # Kiểm tra xem trong kết quả Manager Agent có gọi tool nào không
        if hasattr(result, 'tool_results') and result.tool_results:
            for tool_result in result.tool_results:
                # Nếu Manager gọi một trong các tool chuyển tiếp,
                # trả về kết quả của tool đó thay vì của Manager
                if tool_result.tool_name in ['consult_product_expert', 'consult_cart_expert', 
                                           'consult_shop_expert', 'consult_checkout_expert']:
                    # Xác định target_agent từ tên tool
                    target_map = {
                        'consult_product_expert': 'product',
                        'consult_cart_expert': 'cart',
                        'consult_shop_expert': 'shop',
                        'consult_checkout_expert': 'checkout'
                    }
                    target_agent = target_map.get(tool_result.tool_name, 'product')
                    
                    return {
                        "handoff": True,
                        "target_agent": target_agent,
                        "original_message": message,
                        "thread_id": thread_id,
                        "user_id": user_id,
                        "auth_token": auth_token
                    }
        
        # Mặc định chuyển tiếp tới Product Agent nếu Manager không thực hiện chuyển tiếp
        return {
            "handoff": True,
            "target_agent": "product",
            "original_message": message,
            "thread_id": thread_id,
            "user_id": user_id,
            "auth_token": auth_token
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
        
        # Phân tích tin nhắn mới nhất (không cần lịch sử cho việc phân tích)
        analysis_result = await self._analyze_message(message)
        
        # Chuyển tiếp dựa trên kết quả phân tích
        if analysis_result in ["product", "cart", "shop", "checkout"]:
            return {
                "handoff": True,
                "target_agent": analysis_result,
                "original_message": message,
                "thread_id": thread_id,
                "user_id": user_id,
                "auth_token": auth_token,
                "conversation_history": conversation_history
            }
            
        # Không nên đạt tới đây vì _analyze_message luôn trả về một trong các giá trị trên
        # Nhưng để đảm bảo, vẫn sử dụng Manager Agent để xử lý
        
        # Kết hợp lịch sử hội thoại với tin nhắn hiện tại
        combined_message = message
        if conversation_history and len(conversation_history) > 0:
            # Lấy tối đa 5 tin nhắn gần nhất
            recent_history = conversation_history[-5:] if len(conversation_history) > 5 else conversation_history
            
            history_text = ""
            for msg in recent_history:
                role = "Người dùng" if msg["role"] == "user" else "Trợ lý"
                history_text += f"{role}: {msg['content']}\n"
            
            combined_message = f"Lịch sử hội thoại gần đây:\n{history_text}\nNgười dùng hiện tại: {message}"
        
        result = await Runner.run(self.agent, combined_message)
        
        # Kiểm tra xem trong kết quả Manager Agent có gọi tool nào không
        if hasattr(result, 'tool_results') and result.tool_results:
            for tool_result in result.tool_results:
                # Nếu Manager gọi một trong các tool chuyển tiếp,
                # trả về kết quả của tool đó thay vì của Manager
                if tool_result.tool_name in ['consult_product_expert', 'consult_cart_expert', 
                                           'consult_shop_expert', 'consult_checkout_expert']:
                    # Xác định target_agent từ tên tool
                    target_map = {
                        'consult_product_expert': 'product',
                        'consult_cart_expert': 'cart',
                        'consult_shop_expert': 'shop',
                        'consult_checkout_expert': 'checkout'
                    }
                    target_agent = target_map.get(tool_result.tool_name, 'product')
                    
                    return {
                        "handoff": True,
                        "target_agent": target_agent,
                        "original_message": message,
                        "thread_id": thread_id,
                        "user_id": user_id,
                        "auth_token": auth_token,
                        "conversation_history": conversation_history
                    }
        
        # Mặc định chuyển tiếp tới Product Agent nếu Manager không thực hiện chuyển tiếp
        return {
            "handoff": True,
            "target_agent": "product",
            "original_message": message,
            "thread_id": thread_id,
            "user_id": user_id,
            "auth_token": auth_token,
            "conversation_history": conversation_history
        }

# Singleton instance
manager_agent = ManagerAgentWrapper() 
