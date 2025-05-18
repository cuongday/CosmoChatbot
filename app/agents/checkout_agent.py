from agents import Agent, Runner, function_tool
from ..core.config import settings
from ..tools.cart_tools import (
    get_cart, create_order, get_order_info, 
    get_payment_info, get_my_orders
)
from ..tools.product_tools import get_product_by_id, check_product_availability, rag_product_search
from ..prompts.checkout_agent import CHECKOUT_AGENT_PROMPT
from ..core.hooks import CustomAgentHooks
from ..client.spring_client import spring_boot_client
from typing import List, Dict, Any, Optional
import json
import asyncio

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
                get_my_orders,      # Lấy danh sách đơn hàng của tôi
                check_product_availability,
                rag_product_search
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
        print(f"Auth token received: {auth_token[:20]}...") if auth_token else print("Auth token is None")
        spring_boot_client.update_auth_token(auth_token)
        
        # Kiểm tra giỏ hàng trước khi xử lý
        cart = spring_boot_client.get_cart()
        print(f"Checkout Agent - Get Cart Result: {cart}")
        
        if not cart:
            print("Checkout Agent - Cart is None")
            return {
                "message": "Giỏ hàng của bạn đang trống. Vui lòng thêm sản phẩm vào giỏ hàng trước khi thanh toán.",
                "source_documents": [],
                "thread_id": thread_id
            }
            
        if not cart.get("items"):
            print(f"Checkout Agent - Cart items is empty or not found. Cart structure: {cart}")
            return {
                "message": "Giỏ hàng của bạn đang trống. Vui lòng thêm sản phẩm vào giỏ hàng trước khi thanh toán.",
                "source_documents": [],
                "thread_id": thread_id
            }
            
        # Sử dụng Runner để xử lý tin nhắn
        print(f"Checkout Agent - Processing message with cart: {cart}")
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
        print(f"Auth token received in process_with_history: {auth_token[:20]}...") if auth_token else print("Auth token is None in process_with_history")
        spring_boot_client.update_auth_token(auth_token)
        
        # Kiểm tra giỏ hàng trước khi xử lý
        cart = spring_boot_client.get_cart()
        print(f"Checkout Agent (with history) - Get Cart Result: {cart}")
        
        if not cart:
            print("Checkout Agent (with history) - Cart is None")
            return {
                "message": "Giỏ hàng của bạn đang trống. Vui lòng thêm sản phẩm vào giỏ hàng trước khi thanh toán.",
                "source_documents": [],
                "thread_id": thread_id
            }
            
        if not cart.get("items"):
            print(f"Checkout Agent (with history) - Cart items is empty or not found. Cart structure: {cart}")
            return {
                "message": "Giỏ hàng của bạn đang trống. Vui lòng thêm sản phẩm vào giỏ hàng trước khi thanh toán.",
                "source_documents": [],
                "thread_id": thread_id
            }
        
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
        
        # Sử dụng Runner để xử lý tin nhắn đã kết hợp
        result = await Runner.run(self.agent, combined_message)
        
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
                    # Xử lý kết quả từ get_cart
                    if tool_result.tool_name == 'get_cart':
                        # Parse kết quả JSON từ tool
                        if isinstance(tool_result.output, str):
                            try:
                                cart_data = json.loads(tool_result.output)
                            except:
                                continue
                        else:
                            cart_data = tool_result.output
                            
                        # Trích xuất thông tin sản phẩm từ cart
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
                                    
                    # Xử lý kết quả từ get_product_by_id hoặc check_product_availability
                    elif tool_result.tool_name in ['get_product_by_id', 'check_product_availability', 'rag_product_search']:
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
                    
                    # Xử lý kết quả từ create_order
                    elif tool_result.tool_name == 'create_order':
                        # Parse kết quả JSON từ tool
                        if isinstance(tool_result.output, str):
                            try:
                                order_data = json.loads(tool_result.output)
                            except:
                                continue
                        else:
                            order_data = tool_result.output
                            
                        # Trích xuất thông tin đơn hàng
                        if isinstance(order_data, dict):
                            order_info = {
                                "order_id": order_data.get("id", ""),
                                "total_amount": order_data.get("total_amount", 0),
                                "payment_method": order_data.get("payment_method", ""),
                                "payment_url": order_data.get("payment_url", ""),
                                "status": order_data.get("status", ""),
                                "created_at": order_data.get("created_at", "")
                            }
                            source_documents.append(order_info)
        except Exception as e:
            print(f"Error extracting products: {str(e)}")
            
        return source_documents

# Singleton instance
checkout_agent = CheckoutAgentWrapper() 