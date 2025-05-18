import uvicorn
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import os
import logging
from dotenv import load_dotenv
from app.core.config import settings

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Application lifecycle events
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup event: initialize resources
    logger.info("Application starting up...")
    
    # Khởi tạo và chuẩn bị database SQLModel
    from app.db.database import create_db_and_tables
    create_db_and_tables()
    logger.info("Database initialized and tables created")
    
    # Initialize vector database
    # This is a placeholder - actual implementation would depend on your setup
    logger.info("Initialized vector database")
    
    yield
    
    # Shutdown event: cleanup resources
    logger.info("Application shutting down...")

# Create FastAPI application
app = FastAPI(
    title=settings.APP_NAME,
    description="Multi-agent chatbot service with RAG for cosmetic shop",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS
origins = settings.CORS_ORIGINS.split(",")
# Check if "*" is in origins
if "*" in origins:
    # Khi cho phép tất cả origin, không thể đặt allow_credentials=True
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Allow all origins
        allow_credentials=False,  # Must be False when using ["*"]
        allow_methods=["*"],
        allow_headers=["*"],
    )
else:
    # Khi chỉ định danh sách cụ thể, có thể đặt allow_credentials=True
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# Include API routes
from app.api.endpoints import router
app.include_router(router, prefix="/api/v1")

# Request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    logger.info(f"Request {request.method} {request.url}")
    response = await call_next(request)
    logger.info(f"Response status code: {response.status_code}")
    return response

# Root endpoint
@app.get("/")
async def root():
    return {
        "message": "Cosmetic Shop Chatbot API",
        "docs": "/docs"
    }

# Test CORS endpoint
@app.options("/test-cors")
@app.get("/test-cors")
async def test_cors():
    return {"cors_test": "success"}

# Run application if executed directly
if __name__ == "__main__":
    port = settings.PORT
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        reload=settings.DEBUG
    ) 