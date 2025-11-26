from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from rest_mcp_client.routes.conversation import router as conversation_router
from rest_mcp_client.routes.git import router as git_router
from rest_mcp_client.routes.files import router as files_router

# Create FastAPI app
app = FastAPI(
    title="REST MCP Client",
    description="API for chatting with LLM models with conversation history",
    version="0.1.0",
    docs_url="/api/docs",  # Custom Swagger UI URL
    redoc_url="/api/redoc",  # Custom ReDoc URL
    openapi_url="/api/openapi.json"  # Custom OpenAPI schema URL
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allow all HTTP methods
    allow_headers=["*"],  # Allow all headers
)

# Include routers
app.include_router(conversation_router)
app.include_router(git_router)
app.include_router(files_router)

@app.get("/")
async def root():
    return {
        "message": "REST MCP Client API is running",
        "documentation": "/api/docs",
    }


@app.get("/api/health")
async def health_check():
    """Health check endpoint for container readiness."""
    from datetime import datetime
    
    return {
        "status": "healthy",
        "service": "REST MCP Client",
        "timestamp": datetime.utcnow().isoformat()
    }
