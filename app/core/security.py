# from fastapi import Request, HTTPException, Depends, status
# from fastapi.security import APIKeyHeader
# from .config import settings

# # Định nghĩa header chứa API key
# api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

# async def verify_api_key(api_key: str = Depends(api_key_header)):
#     """
#     Kiểm tra API key trong header request
#     """
#     if not api_key or api_key != settings.SPRING_BOOT_API_KEY:
#         raise HTTPException(
#             status_code=status.HTTP_401_UNAUTHORIZED,
#             detail="Invalid API Key"
#         )
#     return api_key

# def get_client_ip(request: Request) -> str:
#     """
#     Lấy địa chỉ IP của client
#     """
#     forwarded = request.headers.get("X-Forwarded-For")
#     if forwarded:
#         return forwarded.split(",")[0]
#     return request.client.host if request.client else "unknown" 