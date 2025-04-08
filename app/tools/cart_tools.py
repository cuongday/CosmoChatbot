from typing import Dict, Any, List, Optional
from agents import function_tool
from ..client.spring_client import spring_boot_client

@function_tool("Thêm sản phẩm vào giỏ hàng")
def add_to_cart(product_id: str, quantity: int) -> Dict[str, Any]:
    """
    Thêm sản phẩm vào giỏ hàng.
    
    Args:
        product_id: ID của sản phẩm cần thêm vào giỏ hàng
        quantity: Số lượng sản phẩm
        
    Returns:
        Dict: Thông tin giỏ hàng sau khi thêm sản phẩm
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
        Dict: Thông tin giỏ hàng sau khi cập nhật
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
        Dict: Thông tin giỏ hàng sau khi xóa sản phẩm
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

@function_tool("Lấy thông tin giỏ hàng hiện tại")
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
        print(f"Lỗi khi lấy thông tin giỏ hàng: {str(e)}")
        return {"items": [], "total": 0}

@function_tool("Xóa toàn bộ giỏ hàng")
def clear_cart() -> Dict[str, Any]:
    """
    Xóa toàn bộ giỏ hàng.
    
    Returns:
        Dict: Xác nhận giỏ hàng đã được xóa
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

@function_tool("Tạo đơn hàng mới")
def create_order(payment_method: str, phone: str, address: str) -> Dict[str, Any]:
    """
    Tạo đơn hàng mới với thông tin thanh toán
    
    Args:
        payment_method: Phương thức thanh toán (COD hoặc TRANSFER)
        phone: Số điện thoại người nhận
        address: Địa chỉ giao hàng
        
    Returns:
        Dict: Thông tin đơn hàng vừa tạo, bao gồm:
        - order_id: ID đơn hàng
        - payment_method: Phương thức thanh toán
        - status: Trạng thái đơn hàng
        - payment_url: URL thanh toán (chỉ với TRANSFER)
        - total_amount: Tổng tiền
        - created_at: Thời gian tạo
    """
    try:
        # Kiểm tra phương thức thanh toán hợp lệ
        if payment_method not in ["COD", "TRANSFER"]:
            raise ValueError("Phương thức thanh toán không hợp lệ. Chỉ hỗ trợ COD hoặc TRANSFER")
            
        # Tạo đơn hàng
        order = spring_boot_client.create_order(
            payment_method=payment_method,
            phone=phone,
            address=address
        )
        
        # Log thông tin đơn hàng
        print(f"Đã tạo đơn hàng: {order.get('order_id')} - {payment_method}")
        if payment_method == "TRANSFER" and order.get('payment_url'):
            print(f"Payment URL: {order['payment_url']}")
            
        return order
    except Exception as e:
        print(f"Lỗi khi tạo đơn hàng: {str(e)}")
        return {
            "error": str(e),
            "success": False
        }

@function_tool("Lấy thông tin chi tiết đơn hàng")
def get_order_info(order_id: str) -> Dict[str, Any]:
    """
    Lấy thông tin chi tiết của một đơn hàng
    
    Args:
        order_id: ID của đơn hàng
        
    Returns:
        Dict: Thông tin chi tiết đơn hàng bao gồm:
        - order_id: ID đơn hàng
        - status: Trạng thái đơn hàng
        - payment_method: Phương thức thanh toán
        - items: Danh sách sản phẩm
        - total_amount: Tổng tiền
        - shipping_info: Thông tin giao hàng
        - created_at: Thời gian tạo
    """
    try:
        order = spring_boot_client.get_order_info(order_id)
        
        # Log thông tin đơn hàng
        print(f"Thông tin đơn hàng {order_id}: {order.get('status')}")
        
        return order
    except Exception as e:
        print(f"Lỗi khi lấy thông tin đơn hàng: {str(e)}")
        return {
            "error": str(e),
            "success": False
        }

@function_tool("Lấy thông tin thanh toán đơn hàng")
def get_payment_info(order_id: str) -> Dict[str, Any]:
    """
    Lấy thông tin thanh toán của một đơn hàng
    
    Args:
        order_id: ID của đơn hàng
        
    Returns:
        Dict: Thông tin thanh toán bao gồm:
        - payment_method: Phương thức thanh toán
        - status: Trạng thái thanh toán
        - amount: Số tiền
        - payment_url: URL thanh toán (với TRANSFER)
        - paid_at: Thời gian thanh toán (nếu đã thanh toán)
    """
    try:
        payment = spring_boot_client.get_payment_info(order_id)
        
        # Log trạng thái thanh toán
        print(f"Trạng thái thanh toán đơn {order_id}: {payment.get('status')}")
        
        return payment
    except Exception as e:
        print(f"Lỗi khi lấy thông tin thanh toán: {str(e)}")
        return {
            "error": str(e),
            "success": False
        }

@function_tool("Lấy danh sách đơn hàng của tôi")
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
        print(f"Lỗi khi lấy danh sách đơn hàng: {str(e)}")
        return []

# Định nghĩa các tools cho OpenAI Agent
cart_tools = [
    add_to_cart,
    get_cart,
    update_cart,
    remove_from_cart,
    clear_cart,
    create_order,
    get_order_info,
    get_payment_info,
    get_my_orders
] 