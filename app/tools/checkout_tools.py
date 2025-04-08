from typing import Dict, Any, List
from agents import function_tool
from ..client.spring_client import spring_boot_client

@function_tool("Tạo phiên thanh toán mới cho người dùng")
def create_checkout_session(user_id: str) -> Dict[str, Any]:
    """
    Tạo phiên thanh toán mới cho người dùng.
    Args:
        user_id: ID của người dùng
    Returns:
        Thông tin phiên thanh toán
    """
    # Gọi Spring Boot API để tạo phiên thanh toán
    checkout_url = spring_boot_client.create_checkout_link(user_id)
    return {
        "success": bool(checkout_url),
        "checkoutUrl": checkout_url,
        "message": "Sẵn sàng thanh toán" if checkout_url else "Không thể tạo phiên thanh toán"
    }

@function_tool("Lấy danh sách các phương thức vận chuyển có sẵn")
def get_shipping_methods() -> List[Dict[str, Any]]:
    """
    Lấy danh sách các phương thức vận chuyển có sẵn.
    Returns:
        Danh sách các phương thức vận chuyển
    """
    # Thông tin giả định - thực tế sẽ gọi Spring Boot API
    shipping_methods = [
        {"id": "standard", "name": "Giao hàng tiêu chuẩn", "price": 30000, "eta": "3-5 h"},
        {"id": "express", "name": "Giao hàng nhanh", "price": 60000, "eta": "1-2 h"}
    ]
    return shipping_methods

@function_tool("Lấy danh sách các phương thức thanh toán có sẵn")
def get_payment_methods() -> List[Dict[str, Any]]:
    """
    Lấy danh sách các phương thức thanh toán có sẵn.
    Returns:
        Danh sách các phương thức thanh toán
    """
    # Thông tin giả định - thực tế sẽ gọi Spring Boot API
    payment_methods = [
        {"id": "cod", "name": "Thanh toán khi nhận hàng"},
        {"id": "transfer", "name": "Chuyển khoản ngân hàng"},
    ]
    return payment_methods

# Định nghĩa các tools
checkout_tools = [
    create_checkout_session,
    get_shipping_methods,
    get_payment_methods
] 