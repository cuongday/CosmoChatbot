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

@function_tool("Tìm kiếm sản phẩm bằng RAG")
def rag_product_search(query: str, limit: int) -> List[Dict]:
    """
    Tìm kiếm thông tin sản phẩm bằng RAG (Retrieval Augmented Generation) từ vector database
    
    Args:
        query: Câu truy vấn tìm kiếm sản phẩm
        limit: Số lượng kết quả trả về tối đa
        
    Returns:
        Danh sách sản phẩm phù hợp với truy vấn từ vector database
    """
    from ..rag.retriever import product_retriever
    # Xử lý giá trị mặc định cho limit bên trong hàm
    if limit is None or limit <= 0:
        limit = 5
    
    # Làm phong phú query nếu quá ngắn
    enhanced_query = query
    if len(query.split()) <= 2:
        enhanced_query = f"sản phẩm {query} mô tả chi tiết"
        
    print(f"Thực hiện tìm kiếm RAG với query gốc: '{query}'")
    if enhanced_query != query:
        print(f"Query đã nâng cao: '{enhanced_query}'")
        
    results = product_retriever.retrieve(enhanced_query, limit)
    if results:
        print(f"Tìm thấy {len(results)} sản phẩm từ RAG")
        
        # Thêm debug thông tin để kiểm tra kết quả
        for i, result in enumerate(results[:2]):  # Chỉ hiển thị 2 kết quả đầu để tránh spam log
            print(f"  {i+1}. {result.get('name', 'Không tên')} - Giá: {result.get('price', 0):,.0f} VNĐ")
    else:
        print("Không tìm thấy sản phẩm nào từ RAG")
    return results

@function_tool("Kiểm tra sản phẩm còn hàng")
def check_product_availability(product_id: str) -> Dict:
    product = spring_boot_client.get_product_by_id(product_id)
    if not product:
        return {"id": product_id, "available": False, "message": "Không tìm thấy sản phẩm"}
    
    is_available = product.get("quantity", 0) > 0
    return {
        "id": product.get("id", ""),
        "name": product.get("name", ""),
        "price": product.get("sellPrice", 0),
        "quantity": product.get("quantity", 0),
        "status": product.get("status", ""),
        "available": is_available,
        "message": "Sản phẩm còn hàng" if is_available else "Sản phẩm hết hàng hoặc không còn hoạt động"
    }

@function_tool("Tìm kiếm sản phẩm theo khoảng giá từ API")
def find_products_by_price_range(min_price: float, max_price: float) -> List[Dict]:
    """
    Tìm kiếm sản phẩm trong khoảng giá trực tiếp từ API backend
    
    Args:
        min_price: Giá tối thiểu (VD: 100000)
        max_price: Giá tối đa (VD: 500000)
        
    Returns:
        Danh sách sản phẩm trong khoảng giá
    """
    print(f"Tìm kiếm sản phẩm trong khoảng giá {min_price:,.0f} - {max_price:,.0f} VNĐ từ API")
    results = spring_boot_client.get_products_by_price_range(min_price, max_price)
    
    # Thêm thông tin chi tiết để debug
    if results:
        print(f"Tìm thấy {len(results)} sản phẩm trong khoảng giá từ API")
        # Hiển thị thông tin 2 sản phẩm đầu tiên để debug
        for i, product in enumerate(results[:2]):
            print(f"  {i+1}. {product.get('name', 'Không tên')} - Giá: {product.get('sellPrice', product.get('price', 0)):,.0f} VNĐ")
    else:
        print("Không tìm thấy sản phẩm nào trong khoảng giá yêu cầu")
        
    return results 