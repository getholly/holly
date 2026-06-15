import os

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from rest_mcp_client.auth import require_api_token
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

# Add CORS middleware. allow_credentials with a wildcard origin is invalid and is
# rejected by browsers; this is a server-to-server API, so credentials are not used.
# Origins can be restricted via REST_MCP_CORS_ORIGINS (comma-separated).
_cors_origins = [o for o in os.getenv("REST_MCP_CORS_ORIGINS", "*").split(",") if o]
app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_credentials=False,
    allow_methods=["*"],  # Allow all HTTP methods
    allow_headers=["*"],  # Allow all headers
)

# Include routers. The bearer-token dependency enforces auth when
# REST_MCP_API_TOKEN is configured on the container (opt-in, see auth.py).
app.include_router(conversation_router, dependencies=[Depends(require_api_token)])
app.include_router(git_router, dependencies=[Depends(require_api_token)])
app.include_router(files_router, dependencies=[Depends(require_api_token)])

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
