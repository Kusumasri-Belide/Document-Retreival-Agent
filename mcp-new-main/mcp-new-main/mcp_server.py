from __future__ import annotations
import os
from datetime import datetime, timezone

from mcp.server.fastmcp import FastMCP

# --- Minimal MCP server ---
mcp = FastMCP("Time MCP Server")

@mcp.tool(title="Get current date and time")
def now() -> str:
    """Return the current date/time in ISO 8601 with UTC offset."""
    return datetime.now(timezone.utc).astimezone().isoformat()

@mcp.tool(title="Add two integers")
def add(a: int, b: int) -> int:
    """Return the sum of two integers."""
    return a + b

# --- HTTP transport (ASGI) ---
# API Key authentication
API_KEY = os.getenv("API_KEY")

# Build the ASGI app
app = mcp.streamable_http_app()

# Add API key authentication middleware
if API_KEY:
    from starlette.middleware.base import BaseHTTPMiddleware
    from starlette.requests import Request
    from starlette.responses import Response
    import logging
    
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

    class APIKeyMiddleware(BaseHTTPMiddleware):
        async def dispatch(self, request: Request, call_next):
            # Log all requests
            logger.info(f"Request: {request.method} {request.url} from {request.client.host}")
            
            # Check API key
            api_key = request.headers.get("X-API-Key")
            if api_key != API_KEY:
                logger.warning(f"Unauthorized request from {request.client.host}")
                return Response("Unauthorized", status_code=401)
            
            # Add CORS headers
            response = await call_next(request)
            response.headers["Access-Control-Allow-Origin"] = "*"
            response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
            response.headers["Access-Control-Allow-Headers"] = "Content-Type, Accept, X-API-Key, mcp-session-id"
            
            return response

    app.add_middleware(APIKeyMiddleware)
    print(f"🔐 API Key authentication enabled")
else:
    print("⚠️  No API key configured - server is open to all requests")

if __name__ == "__main__":
    # Run HTTP server
    import uvicorn
    import os
    
    # Use environment variables for production
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", 8001))
    
    uvicorn.run(app, host=host, port=port, log_level="info")