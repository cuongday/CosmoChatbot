from typing import Dict, Any, List
from agents import function_tool
from ..client.spring_client import spring_boot_client

@function_tool("Lấy thông tin về đơn hàng của người dùng")
def get_user_orders() -> List[Dict[str, Any]]:
    """
    Lấy danh sách đơn hàng của người dùng hiện tại.
    
    Returns:
        Danh sách đơn hàng
    """
    orders = spring_boot_client.get_user_orders()
    return orders

@function_tool("Lấy chi tiết đơn hàng")
def get_order_details(order_id: str) -> Dict[str, Any]:
    """
    Lấy chi tiết của một đơn hàng.
    
    Args:
        order_id: ID của đơn hàng
        
    Returns:
        Chi tiết đơn hàng
    """
    details = spring_boot_client.get_order_details(order_id)
    return details

@function_tool("Lấy thông tin tổng quan về cửa hàng")
def get_shop_info() -> Dict[str, Any]:
    """
    Lấy thông tin tổng quan về cửa hàng bánh Cosmo
    
    Returns:
        Thông tin cơ bản về cửa hàng
    """
    return {
        "name": "Cosmo Bakery",
        "description": "Cửa hàng bánh Cosmo chuyên cung cấp các loại bánh tươi ngon, chất lượng cao với nhiều loại bánh truyền thống và hiện đại.",
        "established": "2020",
        "specialty": "Bánh sinh nhật, bánh kem, bánh ngọt, bánh mì"
    }

@function_tool("Lấy thông tin về vận chuyển và giao bánh")
def get_shipping_info() -> Dict[str, Any]:
    """
    Lấy thông tin về phương thức vận chuyển và giao bánh
    
    Returns:
        Thông tin chi tiết về các phương thức vận chuyển
    """
    return {
        "delivery_options": [
            {"name": "Giao hàng tiêu chuẩn", "time": "2-3 giờ", "fee": 30000},
            {"name": "Giao hàng nhanh", "time": "1 giờ", "fee": 50000},
            {"name": "Giao hàng theo lịch hẹn", "time": "Theo yêu cầu", "fee": 70000}
        ],
        "free_shipping": "Đơn hàng từ 500.000 VNĐ",
        "delivery_areas": "Nội thành Hà Nội và TP.HCM",
        "note": "Bánh cần được bảo quản trong điều kiện mát, tránh va đập trong quá trình vận chuyển"
    }

@function_tool("Lấy thông tin về chính sách đổi/trả bánh")
def get_return_policy() -> Dict[str, Any]:
    """
    Lấy thông tin về chính sách đổi/trả bánh
    
    Returns:
        Thông tin chi tiết về chính sách đổi trả
    """
    return {
        "return_period": "Trong vòng 24 giờ sau khi nhận hàng",
        "conditions": [
            "Bánh bị hư hỏng, không đúng mẫu mã đã đặt",
            "Bánh không đảm bảo chất lượng, vệ sinh an toàn thực phẩm",
            "Giao sai loại bánh hoặc số lượng"
        ],
        "process": "Liên hệ hotline để được hướng dẫn đổi/trả",
        "exceptions": "Không áp dụng đối với bánh đã sử dụng một phần hoặc bánh đặt riêng theo yêu cầu"
    }

@function_tool("Lấy thông tin liên hệ của cửa hàng")
def get_contact_info() -> Dict[str, Any]:
    """
    Lấy thông tin liên hệ của cửa hàng
    
    Returns:
        Thông tin chi tiết về các kênh liên hệ và địa chỉ cửa hàng
    """
    return {
        "phone": "1900 1234",
        "email": "info@cosmobakery.vn",
        "website": "www.cosmobakery.vn",
        "social_media": {
            "facebook": "facebook.com/cosmobakery",
            "instagram": "instagram.com/cosmobakery"
        },
        "locations": [
            {
                "address": "123 Nguyễn Trãi, Quận 1, TP.HCM",
                "phone": "028 1234 5678",
                "hours": "7:00 - 22:00"
            },
            {
                "address": "456 Lê Lợi, Hà Đông, Hà Nội",
                "phone": "024 8765 4321",
                "hours": "7:00 - 21:30"
            }
        ]
    }

# Định nghĩa các tools
shop_tools = [
    get_user_orders,
    get_order_details,
    get_shop_info,
    get_shipping_info,
    get_return_policy,
    get_contact_info
] 