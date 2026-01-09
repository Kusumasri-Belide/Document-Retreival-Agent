from __future__ import annotations
import os
from datetime import datetime, timezone
import logging

from mcp.server.fastmcp import FastMCP
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Secure MCP server ---
mcp = FastMCP("Time MCP Server")

@mcp.tool(title="Get current date and time")
def now() -> str:
    """Return the current date/time in ISO 8601 with UTC offset."""
    result = datetime.now(timezone.utc).astimezone().isoformat()
    logger.info(f"Time requested: {result}")
    return result

@mcp.tool(title="Add two integers")
def add(a: int, b: int) -> int:
    """Return the sum of two integers."""
    result = a + b
    logger.info(f"Addition requested: {a} + {b} = {result}")
    return result

# --- Security Middleware ---
API_KEY = os.getenv("API_KEY")

class SecurityMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Log all requests
        logger.info(f"Request: {request.method} {request.url} from {request.client.host}")
        
        # Check API key if configured
        if API_KEY:
            api_key = request.headers.get("X-API-Key")
            if api_key != API_KEY:
                logger.warning(f"Unauthorized request from {request.client.host}")
                return Response("Unauthorized", status_code=401)
        
        # CORS headers for ServiceNow
        response = await call_next(request)
        response.headers["Access-Control-Allow-Origin"] = "*"
        response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
        response.headers["Access-Control-Allow-Headers"] = "Content-Type, Accept, X-API-Key, mcp-session-id"
        
        return response

# Build the ASGI app
app = mcp.streamable_http_app()
app.add_middleware(SecurityMiddleware)

# Health check endpoint
@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

if __name__ == "__main__":
    import uvicorn
    
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", 8001))
    
    logger.info(f"Starting MCP server on {host}:{port}")
    if API_KEY:
        logger.info("API key authentication enabled")
    else:
        logger.warning("No API key configured - server is open to all requests")
    
    uvicorn.run(app, host=host, port=port, log_level="info")