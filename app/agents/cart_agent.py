from agents import Agent, Runner, function_tool
from ..core.config import settings
from ..tools.cart_tools import add_to_cart, update_cart, remove_from_cart, get_cart, clear_cart
from ..tools.product_tools import get_product_info, get_product_by_id, check_product_availability, rag_product_search
from ..prompts.cart_agent import CART_AGENT_PROMPT
from ..core.hooks import CustomAgentHooks
from typing import List, Dict, Any
import asyncio
import json

class CartAgentWrapper:
    """
    Agent xử lý các yêu cầu về giỏ hàng và thanh toán
    """
    def __init__(self):
        # Tạo hooks cho cart agent
        self.hooks = CustomAgentHooks("Cart")
        
        # Tạo agent sử dụng OpenAI Agents SDK
        self.agent = Agent(
            name="Cart Assistant",
            instructions=CART_AGENT_PROMPT,
            model=settings.CHAT_MODEL,
            tools=[
                rag_product_search,
                get_product_info,
                get_product_by_id,
                check_product_availability,
                add_to_cart,
                update_cart,
                remove_from_cart,
                get_cart,
                clear_cart
            ],
            hooks=self.hooks
        )
    
    def _extract_products_from_result(self, result: Any) -> List[Dict[str, Any]]:
        """
        Trích xuất thông tin sản phẩm từ kết quả của tool
        
        Args:
            result: Kết quả từ tool
            
        Returns:
            List[Dict]: Danh sách thông tin sản phẩm
        """
        source_documents = []
        try:
            # Kiểm tra xem trong kết quả có chứa thông tin sản phẩm không
            if hasattr(result, 'tool_results') and result.tool_results:
                for tool_result in result.tool_results:
                    # Chỉ xử lý kết quả từ các tool liên quan đến sản phẩm
                    if tool_result.tool_name in ['get_product_info', 'get_product_by_id', 'check_product_availability', 'rag_product_search']:
                        # Parse kết quả JSON từ tool
                        if isinstance(tool_result.output, str):
                            try:
                                products = json.loads(tool_result.output)
                            except:
                                continue
                        else:
                            products = tool_result.output
                            
                        # Xử lý trường hợp kết quả là một list hoặc dict
                        if isinstance(products, dict):
                            products = [products]
                        elif not isinstance(products, list):
                            continue
                            
                        # Thêm từng sản phẩm vào source_documents
                        for product in products:
                            if isinstance(product, dict):
                                # Lấy URL hình ảnh
                                image_url = product.get("image_url", "")
                                # Tạo thẻ img HTML nếu có URL hình ảnh
                                image_html = f'<img src="{image_url}" alt="{product.get("name", "Sản phẩm bánh")}" />' if image_url else ""
                                
                                source_documents.append({
                                    "id": product.get("id", ""),
                                    "name": product.get("name", ""),
                                    "price": product.get("price", 0),
                                    "description": product.get("description", ""),
                                    "image_url": image_url,
                                    "image_html": image_html,  # Thêm trường mới chứa thẻ HTML
                                    "category": product.get("category", ""),
                                    "status": product.get("status", ""),
                                    "quantity": product.get("quantity", 0),
                                    "available": product.get("available", None),
                                    "relevance_score": product.get("relevance_score", 0)
                                })
                    
                    # Thêm nội dung từ add_to_cart và get_cart
                    if tool_result.tool_name in ['add_to_cart', 'get_cart', 'update_cart']:
                        try:
                            cart_data = json.loads(tool_result.output) if isinstance(tool_result.output, str) else tool_result.output
                            
                            if isinstance(cart_data, dict) and "items" in cart_data:
                                for item in cart_data["items"]:
                                    if isinstance(item, dict) and "product" in item:
                                        product = item["product"]
                                        # Lấy URL hình ảnh
                                        image_url = product.get("image_url", "")
                                        # Tạo thẻ img HTML nếu có URL hình ảnh
                                        image_html = f'<img src="{image_url}" alt="{product.get("name", "Sản phẩm bánh")}" />' if image_url else ""
                                        
                                        source_documents.append({
                                            "id": product.get("id", ""),
                                            "name": product.get("name", ""),
                                            "price": product.get("price", 0),
                                            "quantity_in_cart": item.get("quantity", 0),
                                            "image_url": image_url,
                                            "image_html": image_html,  # Thêm trường mới chứa thẻ HTML
                                            "in_cart": True
                                        })
                        except Exception as e:
                            print(f"Error extracting cart items: {str(e)}")
                            
        except Exception as e:
            print(f"Error extracting products: {str(e)}")
            
        return source_documents
    
    async def process(self, message: str, thread_id: str = None, user_id: str = None, auth_token: str = None):
        """
        Xử lý tin nhắn từ người dùng
        
        Args:
            message: Tin nhắn người dùng
            thread_id: ID cuộc trò chuyện
            user_id: ID người dùng
            auth_token: Token xác thực JWT
        """
        # Cập nhật token cho Spring Boot client
        from ..client.spring_client import spring_boot_client
        spring_boot_client.update_auth_token(auth_token)
        
        # Sử dụng Runner từ OpenAI Agents SDK để xử lý tin nhắn
        result = await Runner.run(self.agent, message)
        
        # Trích xuất thông tin sản phẩm từ kết quả của tool
        source_documents = self._extract_products_from_result(result)
        
        # Cấu trúc kết quả để tương thích với API hiện tại
        return {
            "message": result.final_output,
            "thread_id": thread_id,
            "source_documents": source_documents
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
        Xử lý tin nhắn từ người dùng với lịch sử trò chuyện
        
        Args:
            message: Tin nhắn người dùng
            conversation_history: Lịch sử trò chuyện
            thread_id: ID cuộc trò chuyện
            user_id: ID người dùng
            auth_token: Token xác thực JWT
            
        Returns:
            Dict: Kết quả từ agent
        """
        # Cập nhật token cho Spring Boot client
        from ..client.spring_client import spring_boot_client
        spring_boot_client.update_auth_token(auth_token)
        
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
        
        # Sử dụng Runner từ OpenAI Agents SDK để xử lý tin nhắn đã kết hợp
        result = await Runner.run(self.agent, combined_message)
        
        # Trích xuất thông tin sản phẩm từ kết quả của tool
        source_documents = self._extract_products_from_result(result)
        
        # Cấu trúc kết quả để tương thích với API hiện tại
        return {
            "message": result.final_output,
            "thread_id": thread_id,
            "source_documents": source_documents
        }

# Singleton instance
cart_agent = CartAgentWrapper() 