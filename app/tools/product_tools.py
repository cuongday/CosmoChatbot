from typing import List, Dict, Any
from agents import function_tool
from ..client.spring_client import spring_boot_client

@function_tool("Tìm kiếm thông tin sản phẩm")
def get_product_info(query: str) -> List[Dict]:
    """
    Tìm kiếm thông tin sản phẩm sử dụng Spring Filter
    
    Args:
        query: Filter query (ví dụ: name~'Passion' hoặc price>100000)
        
    Returns:
        Danh sách sản phẩm phù hợp với filter
    """
    return spring_boot_client.search_products(query)

@function_tool("Lấy thông tin sản phẩm theo ID")
def get_product_by_id(product_id: str) -> Dict:
    """
    Lấy thông tin sản phẩm theo ID
    
    Args:
        product_id: ID sản phẩm
        
    Returns:
        Thông tin sản phẩm nếu tìm thấy, dict rỗng nếu không tìm thấy
    """
    result = spring_boot_client.get_product_by_id(product_id)
    return result if result else {}

@function_tool("Lấy danh sách sản phẩm theo danh mục")
def get_products_by_category(category_id: str) -> List[Dict]:
    """
    Lấy danh sách sản phẩm theo danh mục sử dụng Spring Filter
    
    Args:
        category_id: ID hoặc tên danh mục
        
    Returns:
        Danh sách sản phẩm thuộc danh mục
    """
    try:
        print(f"Gọi get_products_by_category với tham số: {category_id}")
        
        # Sử dụng Spring Filter để tìm theo category
        filter_query = f"category.id:{category_id}"
        if not category_id.isdigit():
            filter_query = f"category.name~'{category_id}'"
            
        products = spring_boot_client.search_products(filter_query)
        
        if products:
            print(f"Tìm thấy {len(products)} sản phẩm trong danh mục")
            # Bổ sung thêm thông tin
            for product in products:
                if "category" in product and product["category"]:
                    product["category_name"] = product["category"].get("name", "")
                    product["category_id"] = str(product["category"].get("id", ""))
        else:
            print("Không tìm thấy sản phẩm nào trong danh mục này")
        
        return products
    except Exception as e:
        print(f"Lỗi trong get_products_by_category: {str(e)}")
        return []

@function_tool("Tìm kiếm sản phẩm theo khoảng giá")
def search_products_by_price_range(min_price: float = None, max_price: float = None) -> List[Dict]:
    """
    Tìm kiếm sản phẩm theo khoảng giá sử dụng Spring Filter
    
    Args:
        min_price: Giá tối thiểu
        max_price: Giá tối đa
        
    Returns:
        Danh sách sản phẩm trong khoảng giá
    """
    return spring_boot_client.get_products_by_price_range(min_price, max_price)

@function_tool("So sánh thông tin các sản phẩm")
def compare_products(product_ids: List[str]) -> List[Dict]:
    """
    So sánh thông tin của nhiều sản phẩm
    
    Args:
        product_ids: Danh sách ID các sản phẩm cần so sánh
    
    Returns:
        Thông tin chi tiết của các sản phẩm để so sánh
    """
    products = []
    for product_id in product_ids:
        product = spring_boot_client.get_product_by_id(product_id)
        if product:
            products.append(product)
    return products 