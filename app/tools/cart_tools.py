from typing import Dict, Any, List, Optional
from agents import function_tool, Tool
from ..client.spring_client import spring_boot_client

@function_tool("Thêm sản phẩm vào giỏ hàng")
def add_to_cart(product_id: str, quantity: int) -> Dict[str, Any]:
    """
    Thêm sản phẩm vào giỏ hàng.
    
    Args:
        product_id: ID của sản phẩm cần thêm vào giỏ hàng
        quantity: Số lượng sản phẩm
        
    Returns:
        Thông tin giỏ hàng sau khi thêm sản phẩm
    """
    try:
        # Nếu quantity không được chỉ định hoặc <= 0, mặc định là 1
        if not quantity or quantity <= 0:
            quantity = 1
            
        print(f"Thêm sản phẩm vào giỏ hàng: product_id={product_id}, quantity={quantity}")
        result = spring_boot_client.add_to_cart(product_id=product_id, quantity=quantity)
        
        if result.get("success", False):
            print("Thêm sản phẩm vào giỏ hàng thành công")
            # Lấy thông tin giỏ hàng mới nhất
            cart = spring_boot_client.get_cart()
            return cart
        else:
            print(f"Lỗi khi thêm vào giỏ hàng: {result.get('message', 'Unknown error')}")
            return result
            
    except Exception as e:
        error_msg = f"Lỗi khi thêm sản phẩm vào giỏ hàng: {str(e)}"
        print(error_msg)
        return {"success": False, "message": error_msg}

@function_tool("Cập nhật số lượng sản phẩm trong giỏ hàng")
def update_cart(product_id: str, quantity: int) -> Dict[str, Any]:
    """
    Cập nhật số lượng sản phẩm trong giỏ hàng.
    
    Args:
        product_id: ID của sản phẩm cần cập nhật
        quantity: Số lượng mới
        
    Returns:
        Thông tin giỏ hàng sau khi cập nhật
    """
    try:
        result = spring_boot_client.update_cart_item(product_id, quantity)
        if result.get("success", False):
            # Lấy thông tin giỏ hàng mới nhất
            return spring_boot_client.get_cart()
        return result
    except Exception as e:
        error_msg = f"Lỗi khi cập nhật giỏ hàng: {str(e)}"
        print(error_msg)
        return {"success": False, "message": error_msg}

@function_tool("Xóa sản phẩm khỏi giỏ hàng")
def remove_from_cart(product_id: str) -> Dict[str, Any]:
    """
    Xóa sản phẩm khỏi giỏ hàng.
    
    Args:
        product_id: ID của sản phẩm cần xóa
        
    Returns:
        Thông tin giỏ hàng sau khi xóa sản phẩm
    """
    try:
        result = spring_boot_client.remove_from_cart(product_id)
        if result.get("success", False):
            # Lấy thông tin giỏ hàng mới nhất
            return spring_boot_client.get_cart()
        return result
    except Exception as e:
        error_msg = f"Lỗi khi xóa sản phẩm khỏi giỏ hàng: {str(e)}"
        print(error_msg)
        return {"success": False, "message": error_msg}

@Tool(name="get_cart", description="Lấy thông tin giỏ hàng hiện tại của người dùng")
def get_cart() -> Dict[str, Any]:
    """
    Lấy thông tin giỏ hàng hiện tại của người dùng
    
    Returns:
        Dict: Thông tin giỏ hàng bao gồm danh sách sản phẩm và tổng tiền
    """
    try:
        cart = spring_boot_client.get_cart()
        if not cart:
            return {"items": [], "total": 0}
        return cart
    except Exception as e:
        print(f"Error getting cart: {str(e)}")
        return {"items": [], "total": 0}

@function_tool("Xóa toàn bộ giỏ hàng")
def clear_cart() -> Dict[str, Any]:
    """
    Xóa toàn bộ giỏ hàng.
    
    Returns:
        Xác nhận giỏ hàng đã được xóa
    """
    try:
        result = spring_boot_client.clear_cart()
        if result.get("success", False):
            return {"success": True, "message": "Đã xóa toàn bộ giỏ hàng", "items": [], "total": 0}
        return result
    except Exception as e:
        error_msg = f"Lỗi khi xóa giỏ hàng: {str(e)}"
        print(error_msg)
        return {"success": False, "message": error_msg}

@Tool(name="create_order", description="Tạo đơn hàng mới với thông tin thanh toán")
def create_order(payment_method: str, phone: str, address: str) -> Dict[str, Any]:
    """
    Tạo đơn hàng mới với thông tin thanh toán
    
    Args:
        payment_method: Phương thức thanh toán (TRANSFER)
        phone: Số điện thoại người nhận
        address: Địa chỉ giao hàng
        
    Returns:
        Dict: Thông tin đơn hàng vừa tạo
    """
    try:
        order = spring_boot_client.create_order(
            payment_method=payment_method,
            phone=phone,
            address=address
        )
        return order
    except Exception as e:
        print(f"Error creating order: {str(e)}")
        return {}

@Tool(name="get_order_info", description="Lấy thông tin chi tiết của một đơn hàng")
def get_order_info(order_id: str) -> Dict[str, Any]:
    """
    Lấy thông tin chi tiết của một đơn hàng
    
    Args:
        order_id: ID của đơn hàng
        
    Returns:
        Dict: Thông tin chi tiết đơn hàng
    """
    try:
        order = spring_boot_client.get_order_info(order_id)
        return order
    except Exception as e:
        print(f"Error getting order info: {str(e)}")
        return {}

@Tool(name="get_payment_info", description="Lấy thông tin thanh toán của một đơn hàng")
def get_payment_info(order_id: str) -> Dict[str, Any]:
    """
    Lấy thông tin thanh toán của một đơn hàng
    
    Args:
        order_id: ID của đơn hàng
        
    Returns:
        Dict: Thông tin thanh toán
    """
    try:
        payment = spring_boot_client.get_payment_info(order_id)
        return payment
    except Exception as e:
        print(f"Error getting payment info: {str(e)}")
        return {}

@Tool(name="get_my_orders", description="Lấy danh sách đơn hàng của người dùng hiện tại")
def get_my_orders() -> List[Dict[str, Any]]:
    """
    Lấy danh sách đơn hàng của người dùng hiện tại
    
    Returns:
        List[Dict]: Danh sách các đơn hàng
    """
    try:
        orders = spring_boot_client.get_my_orders()
        return orders
    except Exception as e:
        print(f"Error getting orders: {str(e)}")
        return []

# Định nghĩa các tools cho OpenAI Agent
cart_tools = [
    function_tool(add_to_cart),
    function_tool(get_cart),
    function_tool(update_cart),
    function_tool(remove_from_cart),
    function_tool(clear_cart),
    function_tool(create_order),
    function_tool(get_order_info),
    function_tool(get_payment_info),
    function_tool(get_my_orders)
] 