from typing import Dict, Any, List
from agents import function_tool

@function_tool("Cung cấp thông tin về các assistant có sẵn trong hệ thống")
def get_assistant_info() -> Dict[str, Any]:
    """
    Cung cấp thông tin về các assistant có sẵn trong hệ thống để Manager Agent
    có thể quyết định chuyển tiếp câu hỏi đến đúng assistant.
    
    Returns:
        Dict[str, Any]: Thông tin về các assistant có sẵn
    """
    return {
        "assistants": [
            {
                "id": "product",
                "name": "Product Assistant",
                "description": "Chuyên gia về sản phẩm bánh, cung cấp thông tin chi tiết về các loại bánh, giá cả, thành phần",
                "capabilities": [
                    "Tìm kiếm bánh theo tên, mô tả hoặc thành phần",
                    "Xem thông tin chi tiết của một sản phẩm bánh",
                    "So sánh các loại bánh khác nhau",
                    "Lọc bánh theo danh mục (bánh sinh nhật, bánh kem, bánh mì, ...)"
                ]
            },
            {
                "id": "cart",
                "name": "Cart Assistant",
                "description": "Chuyên gia về giỏ hàng và quy trình đặt bánh, thanh toán",
                "capabilities": [
                    "Thêm bánh vào giỏ hàng",
                    "Cập nhật số lượng bánh trong giỏ hàng",
                    "Xóa bánh khỏi giỏ hàng",
                    "Xem thông tin giỏ hàng hiện tại",
                    "Xóa toàn bộ giỏ hàng"
                ]
            },
            {
                "id": "shop",
                "name": "Shop Assistant",
                "description": "Chuyên gia về thông tin cửa hàng, chính sách, vận chuyển",
                "capabilities": [
                    "Cung cấp thông tin chung về cửa hàng Cosmo Bakery",
                    "Chi tiết về phương thức vận chuyển và giao bánh",
                    "Thông tin về chính sách đổi/trả bánh",
                    "Thông tin liên hệ và địa chỉ cửa hàng"
                ]
            }
        ]
    } 