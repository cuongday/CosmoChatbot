import requests
import random
import json
from typing import Dict, List, Any, Optional
from ..core.config import settings

class SpringBootClient:
    """
    Client giao tiếp với Spring Boot API
    """
    def __init__(self, auth_token: str = None):
        self.base_url = settings.SPRING_BOOT_API_URL
        self.headers = {
            "Content-Type": "application/json"
        }
        # Thêm token nếu được cung cấp
        if auth_token:
            self.headers["Authorization"] = auth_token if auth_token.startswith("Bearer ") else f"Bearer {auth_token}"
    
    def update_auth_token(self, auth_token: str):
        """Cập nhật token xác thực"""
        if auth_token:
            self.headers["Authorization"] = auth_token if auth_token.startswith("Bearer ") else f"Bearer {auth_token}"
        elif "Authorization" in self.headers:
            del self.headers["Authorization"]
    
    def get_all_products(self, limit: int = 140) -> List[Dict[str, Any]]:
        """
        Lấy tất cả sản phẩm từ Spring Boot API
        
        Args:
            limit: Số lượng sản phẩm tối đa cần lấy
            
        Returns:
            Danh sách sản phẩm
        """
        url = f"{self.base_url}/api/v1/products"
        params = {"page": 1, "size": limit}
        response = requests.get(url, params=params, headers=self.headers)
        
        if response.status_code == 200:
            # Truy cập theo cấu trúc chính xác của API
            json_data = response.json()
            if json_data and "data" in json_data and "result" in json_data["data"]:
                return json_data["data"]["result"]
            else:
                print(f"Cấu trúc JSON không như mong đợi: {json_data}")
                return []
        return []
    
    def get_product_by_id(self, product_id: str) -> Optional[Dict[str, Any]]:
        """
        Lấy thông tin sản phẩm theo ID
        """
        url = f"{self.base_url}/api/v1/products/{product_id}"
        response = requests.get(url, headers=self.headers)
        
        if response.status_code == 200:
            json_data = response.json()
            if json_data and "data" in json_data:
                return json_data["data"]
            else:
                print(f"Cấu trúc JSON không như mong đợi: {json_data}")
                return None
        return None
    
    def search_products(self, query: str, page: int = 1, size: int = 10) -> List[Dict[str, Any]]:
        url = f"{self.base_url}/api/v1/products"
        params = {
            "page": page,
            "size": size
        }
        
        # Thêm filter nếu có
        if query:
            params["filter"] = query
            
        print(f"URL: {url}")
        print(f"Params: {params}")
            
        response = requests.get(url, params=params, headers=self.headers)
        
        if response.status_code == 200:
            json_data = response.json()
            if json_data and "data" in json_data and "result" in json_data["data"]:
                return json_data["data"]["result"]
            else:
                print(f"Cấu trúc JSON không như mong đợi: {json_data}")
                return []
        return []
    
    def get_products_by_category(self, category_id: str, page: int = 1, size: int = 10) -> List[Dict[str, Any]]:
        """
        Lấy sản phẩm theo danh mục sử dụng Spring Filter
        
        Args:
            category_id: ID danh mục
            page: Trang (mặc định là 1)
            size: Số lượng sản phẩm mỗi trang (mặc định là 10)
            
        Returns:
            Danh sách sản phẩm thuộc danh mục
        """
        # Sử dụng Spring Filter để lọc theo category
        filter_query = f"category.id:{category_id}"
        return self.search_products(filter_query, page, size)
    
    def get_product_by_name(self, name: str) -> List[Dict[str, Any]]:
        """
        Tìm sản phẩm theo tên sử dụng Spring Filter
        
        Args:
            name: Tên sản phẩm cần tìm
            
        Returns:
            Danh sách sản phẩm có tên phù hợp
        """
        # Sử dụng toán tử ~ của Spring Filter để tìm kiếm tương đối
        filter_query = f"name~'{name}'"
        return self.search_products(filter_query)
    
    def get_products_by_price_range(self, min_price: float = None, max_price: float = None) -> List[Dict[str, Any]]:
        filters = []
        if min_price is not None:
            filters.append(f"sellPrice>{min_price}")
        if max_price is not None:
            filters.append(f"sellPrice<{max_price}")
            
        filter_query = " and ".join(filters) if filters else None
        print(f"Filter query: {filter_query}")
        return self.search_products(filter_query)
    
    def add_to_cart(self, product_id: str, quantity: int = 1) -> Dict[str, Any]:
        """
        Thêm sản phẩm vào giỏ hàng
        
        Args:
            product_id: ID sản phẩm
            quantity: Số lượng (mặc định là 1)
            
        Returns:
            Dict chứa kết quả thêm vào giỏ hàng
        """
        try:
            url = f"{self.base_url}/api/v1/carts/add"
            
            # Kiểm tra xem product_id có phải là số không
            try:
                product_id_int = int(product_id)
            except ValueError:
                return {
                    "success": False, 
                    "message": f"ID sản phẩm không hợp lệ: {product_id}"
                }
                
            payload = {
                "productId": product_id_int,
                "quantity": quantity
            }
            
            print(f"Gọi API thêm vào giỏ hàng: {url}")
            print(f"Headers: {self.headers}")
            print(f"Payload: {payload}")
            
            response = requests.post(url, json=payload, headers=self.headers)
            print(f"Status code: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                print(f"Kết quả API: {result}")
                return result
            else:
                error_msg = f"Lỗi khi thêm vào giỏ hàng: HTTP {response.status_code}"
                if response.text:
                    try:
                        error_data = response.json()
                        if "message" in error_data:
                            error_msg = error_data["message"]
                    except:
                        error_msg += f" - {response.text}"
                print(error_msg)
                return {"success": False, "message": error_msg}
                
        except Exception as e:
            error_msg = f"Lỗi khi gọi API thêm vào giỏ hàng: {str(e)}"
            print(error_msg)
            return {"success": False, "message": error_msg}
    
    def update_cart_item(self, cart_detail_id: str, quantity: int) -> Dict[str, Any]:
        """
        Cập nhật số lượng sản phẩm trong giỏ hàng
        """
        url = f"{self.base_url}/api/v1/carts/update/{cart_detail_id}"
        payload = {
            "quantity": quantity
        }
        response = requests.put(url, json=payload, headers=self.headers)
        
        if response.status_code == 200:
            return response.json()
        return {"success": False, "message": "Không thể cập nhật giỏ hàng"}
    
    def remove_from_cart(self, cart_detail_id: str) -> Dict[str, Any]:
        """
        Xóa sản phẩm khỏi giỏ hàng
        """
        url = f"{self.base_url}/api/v1/carts/remove/{cart_detail_id}"
        response = requests.delete(url, headers=self.headers)
        
        if response.status_code == 200:
            return {"success": True, "message": "Đã xóa sản phẩm khỏi giỏ hàng"}
        return {"success": False, "message": "Không thể xóa sản phẩm khỏi giỏ hàng"}
    
    def get_cart(self, user_id: str = None) -> Dict[str, Any]:
        """
        Lấy thông tin giỏ hàng
        """
        url = f"{self.base_url}/api/v1/carts"
        response = requests.get(url, headers=self.headers)
        
        if response.status_code == 200:
            json_data = response.json()
            print(f"Response giỏ hàng: {json_data}")
            
            # Kiểm tra cấu trúc JSON và trích xuất dữ liệu
            if json_data and "data" in json_data:
                items = json_data["data"]
                if isinstance(items, list) and len(items) > 0:
                    # Định dạng lại dữ liệu để phù hợp với mong đợi của agent
                    formatted_items = []
                    total_price = 0
                    
                    for item in items:
                        product = item.get("product", {})
                        formatted_item = {
                            "id": item.get("id"),
                            "product_id": product.get("id"),
                            "name": product.get("name"),
                            "price": product.get("sellPrice", 0),
                            "quantity": item.get("quantity", 0),
                            "image": product.get("image")
                        }
                        formatted_items.append(formatted_item)
                        total_price += (product.get("sellPrice", 0) * item.get("quantity", 0))
                    
                    return {
                        "items": formatted_items,
                        "total": total_price,
                        "count": len(formatted_items)
                    }
                return {"items": [], "total": 0, "count": 0}
            return {"items": [], "total": 0, "count": 0}
        return {"items": [], "total": 0, "count": 0}
    
    def clear_cart(self) -> Dict[str, Any]:
        """
        Xóa tất cả sản phẩm trong giỏ hàng
        """
        url = f"{self.base_url}/api/v1/carts/clear"
        response = requests.delete(url, headers=self.headers)
        
        if response.status_code == 200:
            return {"success": True, "message": "Đã xóa tất cả sản phẩm trong giỏ hàng"}
        return {"success": False, "message": "Không thể xóa giỏ hàng"}
    
    def create_order(self, payment_method: str, phone: str, address: str) -> Dict[str, Any]:
        """
        Tạo đơn hàng mới
        
        Args:
            payment_method: TRANSFER hoặc COD
            phone: Số điện thoại
            address: Địa chỉ giao hàng
        """
        url = f"{self.base_url}/api/v1/orders"
        payload = {
            "paymentMethod": payment_method,
            "phone": phone,
            "address": address
        }
        
        print(f"Gọi API tạo đơn hàng: {url}")
        print(f"Headers: {self.headers}")
        print(f"Payload: {payload}")
        
        response = requests.post(url, json=payload, headers=self.headers)
        print(f"Status code: {response.status_code}")
        
        if response.status_code == 200 or response.status_code == 201:
            result = response.json()
            print(f"Kết quả API: {result}")
            
            # Khởi tạo các biến mặc định
            order_id = None
            payment_url = None
            
            # Trích xuất dữ liệu từ cấu trúc response
            if "data" in result:
                if "order" in result["data"]:
                    order = result["data"]["order"]
                    order_id = order.get("id")
                    # Có thể payment_url nằm trong order hoặc ngoài order
                    if "paymentUrl" in order:
                        payment_url = order.get("paymentUrl")
                
                # Payment URL có thể nằm trực tiếp trong data
                if "paymentUrl" in result["data"]:
                    payment_url = result["data"].get("paymentUrl")
            
            print(f"Đã tạo đơn hàng: {order_id} - {payment_method}")
            if payment_method == "TRANSFER" and payment_url:
                print(f"Payment URL: {payment_url}")
            
            return {
                "success": True,  # Đặt cờ success=True vì API đã trả về thành công
                "message": result.get("message", "Tạo đơn hàng thành công"),
                "order_id": order_id,
                "payment_url": payment_url,
                "payment_method": payment_method
            }
        else:
            error_msg = f"Lỗi khi tạo đơn hàng: HTTP {response.status_code}"
            if response.text:
                try:
                    error_data = response.json()
                    if "message" in error_data:
                        error_msg = error_data["message"]
                except:
                    error_msg += f" - {response.text}"
            print(error_msg)
            return {"success": False, "message": error_msg}
            
    def get_order_info(self, order_id: str) -> Dict[str, Any]:
        """
        Lấy thông tin chi tiết đơn hàng
        """
        url = f"{self.base_url}/api/v1/orders/{order_id}"
        response = requests.get(url, headers=self.headers)
        
        if response.status_code == 200:
            return response.json()
        return {"success": False, "message": "Không thể lấy thông tin đơn hàng"}
    
    def get_payment_info(self, order_id: str) -> Dict[str, Any]:
        """
        Lấy thông tin thanh toán của đơn hàng
        """
        url = f"{self.base_url}/api/v1/payment/payment-info/{order_id}"
        response = requests.get(url, headers=self.headers)
        
        if response.status_code == 200:
            return response.json()
        return {"success": False, "message": "Không thể lấy thông tin thanh toán"}
    
    def get_my_orders(self) -> List[Dict[str, Any]]:
        """
        Lấy danh sách đơn hàng của người dùng hiện tại
        """
        url = f"{self.base_url}/api/v1/orders/my-orders"
        response = requests.get(url, headers=self.headers)
        
        if response.status_code == 200:
            json_data = response.json()
            if json_data and "result" in json_data:
                return json_data["result"]
        return []

# Singleton instance
spring_boot_client = SpringBootClient() 