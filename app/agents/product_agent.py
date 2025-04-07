from agents import Agent, Tool, Runner
from ..core.config import settings
from ..tools.product_tools import get_product_info, get_product_by_id, compare_products, get_products_by_category
from ..prompts.product_agent import PRODUCT_AGENT_PROMPT
from ..client.spring_client import spring_boot_client
from ..core.hooks import CustomAgentHooks
from typing import List, Dict, Any, Optional
import json

class ProductAgentWrapper:
    """
    Agent chuyên biệt về sản phẩm giúp người dùng tìm kiếm và tra cứu thông tin sản phẩm
    """
    def __init__(self):
        # Tạo hooks cho product agent
        self.hooks = CustomAgentHooks("Product")
        
        # Tạo agent sử dụng OpenAI Agents SDK
        self.agent = Agent(
            name="Product Expert",
            instructions=PRODUCT_AGENT_PROMPT,
            model=settings.CHAT_MODEL,
            tools=[
                get_product_info,        # Tool tìm kiếm thông tin sản phẩm
                get_product_by_id,       # Tool lấy thông tin sản phẩm theo ID
                compare_products,        # Tool so sánh các sản phẩm
                get_products_by_category # Tool lấy sản phẩm theo danh mục
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
                    if tool_result.tool_name in ['get_product_info', 'get_product_by_id', 'get_products_by_category']:
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
                                source_documents.append({
                                    "id": product.get("id", ""),
                                    "name": product.get("name", ""),
                                    "price": product.get("price", 0),
                                    "description": product.get("description", ""),
                                    "image_url": product.get("image_url", ""),
                                    "category": product.get("category", ""),
                                    "status": product.get("status", ""),
                                    "quantity": product.get("quantity", 0),
                                    "relevance_score": product.get("relevance_score", 0)
                                })
        except Exception as e:
            print(f"Error extracting products: {str(e)}")
            
        return source_documents
    
    async def process(self, message: str, thread_id: str = None, user_id: str = None, auth_token: str = None):
        """
        Xử lý tin nhắn liên quan đến sản phẩm
        
        Args:
            message: Tin nhắn của người dùng
            thread_id: ID cuộc trò chuyện
            user_id: ID người dùng
            auth_token: Token xác thực JWT
        """
        # Cập nhật token xác thực cho spring_boot_client nếu có
        spring_boot_client.update_auth_token(auth_token)
        
        # Sử dụng Runner từ OpenAI Agents SDK để xử lý tin nhắn
        result = await Runner.run(self.agent, message)
        
        # Trích xuất thông tin sản phẩm từ kết quả của tool
        source_documents = self._extract_products_from_result(result)
        
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
        Xử lý tin nhắn liên quan đến sản phẩm với lịch sử trò chuyện
        
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
        
        # Trích xuất thông tin sản phẩm từ kết quả của tool
        source_documents = self._extract_products_from_result(result)
        
        return {
            "message": result.final_output,
            "source_documents": source_documents,
            "thread_id": thread_id
        }

# Singleton instance
product_agent = ProductAgentWrapper()