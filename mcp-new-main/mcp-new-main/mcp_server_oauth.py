from __future__ import annotations
import os
import secrets
import time
from datetime import datetime, timezone, timedelta
from typing import Dict, Optional
import hashlib
import base64
import json

from mcp.server.fastmcp import FastMCP
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response, JSONResponse
from starlette.routing import Route
from starlette.applications import Starlette

# OAuth 2.0 Configuration
OAUTH_CLIENT_ID = os.getenv("OAUTH_CLIENT_ID", "servicenow-client")
OAUTH_CLIENT_SECRET = os.getenv("OAUTH_CLIENT_SECRET", "your-client-secret-here")
OAUTH_REDIRECT_URI = os.getenv("OAUTH_REDIRECT_URI", "https://your-servicenow-instance.service-now.com/oauth_redirect.do")

# In-memory token storage (use Redis/database in production)
active_tokens: Dict[str, dict] = {}
authorization_codes: Dict[str, dict] = {}

# --- MCP Server with FastMCP ---
mcp = FastMCP("OAuth MCP Server")

# Import document agent modules
import sys
import os
sys.path.append('/home/ubuntu/mcp-new')  # Add your main app path

try:
    from backend.llm_answer import generate_answer
    from backend.retriever import reload_index, retrieve_relevant_chunks
    from backend.config import PROCESSED_DIR, VECTOR_STORE_DIR
    from backend.extract_answers import extract_all
    from backend.embed import embed_and_store
    import pickle
    import faiss
    from pathlib import Path
    DOCUMENT_AGENT_AVAILABLE = True
    print("✅ Document agent modules loaded successfully")
except ImportError as e:
    DOCUMENT_AGENT_AVAILABLE = False
    print(f"⚠️ Document agent not available: {e}")

# Document Agent Tools
@mcp.tool(title="Ask document question")
def ask_document(question: str) -> str:
    """Answer a question using the SharePoint document index and Azure OpenAI."""
    if not DOCUMENT_AGENT_AVAILABLE:
        return "Document agent not available. Please check configuration."
    try:
        return generate_answer(question)
    except FileNotFoundError:
        return "Vector store not found. Please run reindex_documents first."
    except Exception as e:
        return f"Error answering question: {str(e)}"

@mcp.tool(title="List available documents")
def list_documents() -> str:
    """List all processed documents available for querying."""
    if not DOCUMENT_AGENT_AVAILABLE:
        return "Document agent not available."
    try:
        docs = sorted([f for f in os.listdir(PROCESSED_DIR) if f.endswith(".txt")])
        if not docs:
            return "No documents found. Please run reindex_documents to process documents."
        return f"Available documents ({len(docs)}):\n" + "\n".join(f"- {doc}" for doc in docs)
    except Exception as e:
        return f"Error listing documents: {str(e)}"

@mcp.tool(title="Reindex documents")
def reindex_documents() -> str:
    """Re-extract texts from documents and rebuild the FAISS vector index."""
    if not DOCUMENT_AGENT_AVAILABLE:
        return "Document agent not available."
    try:
        # Extract documents
        extract_all()
        # Build embeddings and FAISS index
        embed_and_store()
        # Reload in-memory index
        reload_index()
        return "✅ Document reindexing completed successfully. Vector store rebuilt."
    except Exception as e:
        return f"Error during reindexing: {str(e)}"

@mcp.tool(title="Get document content")
def get_document_content(document_name: str) -> str:
    """Get the full content of a specific processed document by name."""
    if not DOCUMENT_AGENT_AVAILABLE:
        return "Document agent not available."
    try:
        doc_path = Path(PROCESSED_DIR) / document_name
        if not doc_path.exists():
            available_docs = [f for f in os.listdir(PROCESSED_DIR) if f.endswith(".txt")]
            return f"Document '{document_name}' not found. Available documents: {', '.join(available_docs)}"
        
        content = doc_path.read_text(encoding="utf-8", errors="ignore")
        # Truncate if too long for display
        if len(content) > 2000:
            content = content[:2000] + f"\n\n... (truncated, full document has {len(content)} characters)"
        return content
    except Exception as e:
        return f"Error reading document: {str(e)}"

@mcp.tool(title="Get vector store statistics")
def get_vector_stats() -> str:
    """Get statistics about the current vector store and document index."""
    if not DOCUMENT_AGENT_AVAILABLE:
        return "Document agent not available."
    try:
        idx_path = Path(VECTOR_STORE_DIR) / "faiss_index.bin"
        ch_path = Path(VECTOR_STORE_DIR) / "chunks.pkl"
        
        if not idx_path.exists() or not ch_path.exists():
            return "Vector store not found. Run reindex_documents to build the index."
        
        # Load index and chunks
        index = faiss.read_index(str(idx_path))
        with open(ch_path, "rb") as f:
            chunks = pickle.load(f)
        
        # Get document count
        doc_count = len([f for f in os.listdir(PROCESSED_DIR) if f.endswith(".txt")])
        
        return f"""📊 Vector Store Statistics:
- Documents processed: {doc_count}
- Text chunks: {len(chunks)}
- Vector dimensions: {index.d}
- Index type: {type(index).__name__}
- Index size: {index.ntotal} vectors"""
    except Exception as e:
        return f"Error getting vector stats: {str(e)}"

@mcp.tool(title="Search document chunks")
def search_chunks(query: str, num_results: int = 4) -> str:
    """Search for relevant document chunks without generating an AI answer."""
    if not DOCUMENT_AGENT_AVAILABLE:
        return "Document agent not available."
    try:
        chunks = retrieve_relevant_chunks(query, k=num_results)
        if not chunks:
            return "No relevant chunks found for your query."
        return f"📄 Found {num_results} relevant chunks:\n\n{chunks}"
    except FileNotFoundError:
        return "Vector store not found. Please run reindex_documents first."
    except Exception as e:
        return f"Error searching chunks: {str(e)}"

# Basic utility tools (keeping original ones)
@mcp.tool(title="Get current date and time")
def now() -> str:
    """Return the current date/time in ISO 8601 with UTC offset."""
    return datetime.now(timezone.utc).astimezone().isoformat()

@mcp.tool(title="Add two integers")
def add(a: int, b: int) -> int:
    """Sum two integers and return the result."""
    return a + b

# --- ServiceNow Compatibility Wrapper ---
async def servicenow_mcp_handler(request: Request):
    """ServiceNow-compatible MCP handler that wraps FastMCP"""
    try:
        data = await request.json()
        method = data.get("method")
        params = data.get("params", {})
        request_id = data.get("id")
        
        print(f"🔧 ServiceNow MCP method: {method}")
        
        if method == "initialize":
            # ServiceNow-compatible initialize response
            response = {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {
                    "protocolVersion": "2025-03-26",  # Match ServiceNow's version
                    "capabilities": {
                        "tools": {"listChanged": False}
                    },
                    "serverInfo": {
                        "name": "OAuth MCP Server",
                        "version": "1.0.0"
                    }
                }
            }
            print(f"✅ Initialize response sent to ServiceNow")
            return JSONResponse(response)
        
        elif method == "tools/list":
            # Get tools from FastMCP and format for ServiceNow
            tools = [
                {
                    "name": "now",
                    "description": "Get current date and time in ISO 8601 format",
                    "inputSchema": {
                        "type": "object",
                        "properties": {},
                        "additionalProperties": False
                    }
                },
                {
                    "name": "add", 
                    "description": "Add two integers together",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "a": {"type": "integer", "description": "First number"},
                            "b": {"type": "integer", "description": "Second number"}
                        },
                        "required": ["a", "b"],
                        "additionalProperties": False
                    }
                },
                {
                    "name": "ask_document",
                    "description": "Answer questions using the SharePoint document index and Azure OpenAI",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "question": {"type": "string", "description": "Question to ask about the documents"}
                        },
                        "required": ["question"],
                        "additionalProperties": False
                    }
                },
                {
                    "name": "list_documents",
                    "description": "List all processed documents available for querying",
                    "inputSchema": {
                        "type": "object",
                        "properties": {},
                        "additionalProperties": False
                    }
                },
                {
                    "name": "reindex_documents",
                    "description": "Re-extract texts from documents and rebuild the FAISS vector index",
                    "inputSchema": {
                        "type": "object",
                        "properties": {},
                        "additionalProperties": False
                    }
                },
                {
                    "name": "get_document_content",
                    "description": "Get the full content of a specific processed document by name",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "document_name": {"type": "string", "description": "Name of the document to retrieve"}
                        },
                        "required": ["document_name"],
                        "additionalProperties": False
                    }
                },
                {
                    "name": "get_vector_stats",
                    "description": "Get statistics about the current vector store and document index",
                    "inputSchema": {
                        "type": "object",
                        "properties": {},
                        "additionalProperties": False
                    }
                },
                {
                    "name": "search_chunks",
                    "description": "Search for relevant document chunks without generating an AI answer",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "query": {"type": "string", "description": "Search query"},
                            "num_results": {"type": "integer", "description": "Number of results to return", "default": 4}
                        },
                        "required": ["query"],
                        "additionalProperties": False
                    }
                }
            ]
            
            response = {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {"tools": tools}
            }
            print(f"✅ Tools list sent to ServiceNow: {len(tools)} tools")
            return JSONResponse(response)
        
        elif method == "tools/call":
            # Call the actual FastMCP tool functions
            tool_name = params.get("name")
            arguments = params.get("arguments", {})
            
            print(f"🛠️ Calling FastMCP tool: {tool_name} with args: {arguments}")
            
            try:
                if tool_name == "now":
                    result = now()
                elif tool_name == "add":
                    result = add(arguments.get("a", 0), arguments.get("b", 0))
                elif tool_name == "ask_document":
                    result = ask_document(arguments.get("question", ""))
                elif tool_name == "list_documents":
                    result = list_documents()
                elif tool_name == "reindex_documents":
                    result = reindex_documents()
                elif tool_name == "get_document_content":
                    result = get_document_content(arguments.get("document_name", ""))
                elif tool_name == "get_vector_stats":
                    result = get_vector_stats()
                elif tool_name == "search_chunks":
                    result = search_chunks(
                        arguments.get("query", ""),
                        arguments.get("num_results", 4)
                    )
                else:
                    return JSONResponse({
                        "jsonrpc": "2.0",
                        "id": request_id,
                        "error": {"code": -32601, "message": f"Unknown tool: {tool_name}"}
                    })
                
                response = {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "result": {
                        "content": [{"type": "text", "text": str(result)}],
                        "isError": False
                    }
                }
                print(f"✅ Tool result sent to ServiceNow: {result[:100]}...")  # Truncate long results in log
                return JSONResponse(response)
                
            except Exception as tool_error:
                print(f"❌ Tool execution error: {tool_error}")
                return JSONResponse({
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "result": {
                        "content": [{"type": "text", "text": f"Error: {str(tool_error)}"}],
                        "isError": True
                    }
                })
        
        else:
            return JSONResponse({
                "jsonrpc": "2.0",
                "id": request_id,
                "error": {"code": -32601, "message": f"Unknown method: {method}"}
            })
            
    except Exception as e:
        print(f"❌ ServiceNow MCP Error: {e}")
        return JSONResponse({
            "jsonrpc": "2.0",
            "id": data.get("id") if 'data' in locals() else None,
            "error": {"code": -32603, "message": str(e)}
        })

# --- OAuth 2.0 Endpoints ---

async def oauth_authorize(request: Request):
    """OAuth 2.0 Authorization Endpoint"""
    from starlette.responses import RedirectResponse
    
    client_id = request.query_params.get("client_id")
    redirect_uri = request.query_params.get("redirect_uri")
    response_type = request.query_params.get("response_type")
    scope = request.query_params.get("scope", "mcp:read mcp:write")
    state = request.query_params.get("state", "")
    
    # Validate parameters
    if not client_id or client_id != OAUTH_CLIENT_ID:
        return JSONResponse({"error": "invalid_client"}, status_code=400)
    
    if response_type != "code":
        return JSONResponse({"error": "unsupported_response_type"}, status_code=400)
    
    if not redirect_uri:
        return JSONResponse({"error": "invalid_request", "error_description": "redirect_uri is required"}, status_code=400)
    
    # Generate authorization code
    auth_code = secrets.token_urlsafe(32)
    authorization_codes[auth_code] = {
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "scope": scope,
        "expires_at": time.time() + 600,  # 10 minutes
        "used": False
    }
    
    # Build redirect URL with code and state
    redirect_url = f"{redirect_uri}?code={auth_code}"
    if state:
        redirect_url += f"&state={state}"
    
    print(f"🔄 Redirecting to: {redirect_url}")
    
    # Return 302 redirect (this is what ServiceNow expects!)
    return RedirectResponse(url=redirect_url, status_code=302)

async def oauth_token(request: Request):
    """OAuth 2.0 Token Endpoint"""
    import base64
    
    # ServiceNow sends application/x-www-form-urlencoded
    content_type = request.headers.get("content-type", "")
    
    if "application/json" in content_type:
        data = await request.json()
    else:
        form_data = await request.form()
        data = dict(form_data)
    
    print(f"🎫 Token request data: {data}")
    print(f"🔍 Content-Type: {content_type}")
    print(f"🔑 Headers: {dict(request.headers)}")
    
    # Handle Client Secret Basic authentication (ServiceNow uses this)
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Basic "):
        # Decode Basic auth
        encoded = auth_header[6:]  # Remove "Basic "
        try:
            decoded = base64.b64decode(encoded).decode('utf-8')
            client_id, client_secret = decoded.split(':', 1)
            print(f"🔐 Basic Auth - Client ID: {client_id}")
        except Exception as e:
            print(f"❌ Basic Auth decode error: {e}")
            return JSONResponse({"error": "invalid_client"}, status_code=401)
    else:
        # Get from form/JSON data
        client_id = data.get("client_id")
        client_secret = data.get("client_secret")
        print(f"🔐 Form Auth - Client ID: {client_id}")
    
    grant_type = data.get("grant_type")
    code = data.get("code")
    redirect_uri = data.get("redirect_uri")
    
    print(f"📋 Grant type: {grant_type}, Code: {code}, Redirect: {redirect_uri}")
    
    # Validate grant type
    if grant_type != "authorization_code":
        return JSONResponse({"error": "unsupported_grant_type"}, status_code=400)
    
    # Validate client credentials
    if client_id != OAUTH_CLIENT_ID or client_secret != OAUTH_CLIENT_SECRET:
        print(f"❌ Client validation failed. Expected: {OAUTH_CLIENT_ID}, Got: {client_id}")
        return JSONResponse({"error": "invalid_client"}, status_code=401)
    
    # Validate authorization code
    if not code or code not in authorization_codes:
        print(f"❌ Invalid authorization code: {code}")
        print(f"📋 Available codes: {list(authorization_codes.keys())}")
        return JSONResponse({"error": "invalid_grant"}, status_code=400)
    
    auth_data = authorization_codes[code]
    
    # Check if code is expired or used
    if time.time() > auth_data["expires_at"] or auth_data["used"]:
        print(f"❌ Authorization code expired or used")
        return JSONResponse({"error": "invalid_grant"}, status_code=400)
    
    # Validate redirect URI matches
    if redirect_uri != auth_data["redirect_uri"]:
        print(f"❌ Redirect URI mismatch. Expected: {auth_data['redirect_uri']}, Got: {redirect_uri}")
        return JSONResponse({"error": "invalid_grant"}, status_code=400)
    
    # Mark code as used
    auth_data["used"] = True
    
    # Generate access token
    access_token = secrets.token_urlsafe(32)
    refresh_token = secrets.token_urlsafe(32)
    
    # Store token
    active_tokens[access_token] = {
        "client_id": client_id,
        "scope": auth_data["scope"],
        "expires_at": time.time() + 3600,  # 1 hour
        "refresh_token": refresh_token
    }
    
    print(f"✅ Token generated successfully for client: {client_id}")
    
    # Return standard OAuth token response
    return JSONResponse({
        "access_token": access_token,
        "token_type": "Bearer",
        "expires_in": 3600,
        "refresh_token": refresh_token,
        "scope": auth_data["scope"]
    })

async def oauth_userinfo(request: Request):
    """OAuth 2.0 User Info Endpoint"""
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        return JSONResponse({"error": "invalid_token"}, status_code=401)
    
    token = auth_header[7:]  # Remove "Bearer "
    
    if token not in active_tokens:
        return JSONResponse({"error": "invalid_token"}, status_code=401)
    
    token_data = active_tokens[token]
    if time.time() > token_data["expires_at"]:
        return JSONResponse({"error": "token_expired"}, status_code=401)
    
    return JSONResponse({
        "sub": "mcp-server-user",
        "name": "MCP Server",
        "scope": token_data["scope"]
    })

async def oauth_revoke(request: Request):
    """OAuth 2.0 Token Revocation Endpoint"""
    form_data = await request.form()
    token = form_data.get("token")
    token_type_hint = form_data.get("token_type_hint", "access_token")
    
    # Handle Client Secret Basic authentication
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Basic "):
        import base64
        encoded = auth_header[6:]
        decoded = base64.b64decode(encoded).decode('utf-8')
        client_id, client_secret = decoded.split(':', 1)
        
        # Validate client
        if client_id != OAUTH_CLIENT_ID or client_secret != OAUTH_CLIENT_SECRET:
            return JSONResponse({"error": "invalid_client"}, status_code=401)
    
    # Revoke the token
    if token in active_tokens:
        del active_tokens[token]
    
    # Always return 200 for security (don't reveal if token existed)
    return JSONResponse({"revoked": True})

# --- OAuth Middleware ---
class OAuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Skip OAuth for OAuth endpoints
        if request.url.path in ["/oauth/authorize", "/oauth/token", "/oauth/userinfo", "/.well-known/oauth-authorization-server"]:
            return await call_next(request)
        
        # Log MCP requests for debugging
        if request.url.path == "/mcp":
            try:
                body = await request.body()
                if body:
                    mcp_data = json.loads(body.decode())
                    print(f"📨 MCP Request: {json.dumps(mcp_data, indent=2)}")
                
                # Recreate request for processing
                async def receive():
                    return {"type": "http.request", "body": body}
                
                request = Request(request.scope, receive)
            except Exception as e:
                print(f"❌ Error logging MCP request: {e}")
        
        # Check for Bearer token
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return JSONResponse({"error": "missing_token"}, status_code=401)
        
        token = auth_header[7:]  # Remove "Bearer "
        
        # Validate token
        if token not in active_tokens:
            return JSONResponse({"error": "invalid_token"}, status_code=401)
        
        token_data = active_tokens[token]
        if time.time() > token_data["expires_at"]:
            del active_tokens[token]  # Clean up expired token
            return JSONResponse({"error": "token_expired"}, status_code=401)
        
        # Add CORS headers
        response = await call_next(request)
        response.headers["Access-Control-Allow-Origin"] = "*"
        response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
        response.headers["Access-Control-Allow-Headers"] = "Content-Type, Accept, Authorization, mcp-session-id"
        
        return response

# --- OAuth Discovery Endpoint ---
async def oauth_discovery(request: Request):
    """OAuth 2.0 Authorization Server Metadata"""
    base_url = f"http://{request.url.hostname}:{request.url.port}"
    
    return JSONResponse({
        "issuer": base_url,
        "authorization_endpoint": f"{base_url}/oauth/authorize",
        "token_endpoint": f"{base_url}/oauth/token",
        "userinfo_endpoint": f"{base_url}/oauth/userinfo",
        "response_types_supported": ["code"],
        "grant_types_supported": ["authorization_code"],
        "token_endpoint_auth_methods_supported": ["client_secret_post"],
        "scopes_supported": ["mcp:read", "mcp:write"]
    })

# --- Build Application ---
# Create OAuth routes
oauth_routes = [
    Route("/oauth/authorize", oauth_authorize, methods=["GET"]),
    Route("/oauth/token", oauth_token, methods=["POST"]),
    Route("/oauth/userinfo", oauth_userinfo, methods=["GET"]),
    Route("/oauth/revoke", oauth_revoke, methods=["POST"]),
    Route("/.well-known/oauth-authorization-server", oauth_discovery, methods=["GET"]),
]

# Create hybrid app: FastMCP + ServiceNow compatibility
fastmcp_app = mcp.streamable_http_app()  # Keep FastMCP for other clients

# Create main Starlette app for ServiceNow
from starlette.applications import Starlette
app = Starlette()

# Add OAuth middleware
app.add_middleware(OAuthMiddleware)

# Add all routes including ServiceNow-compatible MCP handler
all_routes = oauth_routes + [
    Route("/mcp", servicenow_mcp_handler, methods=["POST"]),  # ServiceNow endpoint
    Route("/mcp-standard", fastmcp_app, methods=["POST"]),    # Standard MCP endpoint (future use)
]

for route in all_routes:
    app.router.routes.append(route)

if __name__ == "__main__":
    import uvicorn
    
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", 8001))
    
    print("🔐 OAuth 2.0 MCP Server Starting...")
    print(f"📍 Server URL: http://{host}:{port}")
    print(f"🔑 Client ID: {OAUTH_CLIENT_ID}")
    print(f"🔒 Client Secret: {OAUTH_CLIENT_SECRET}")
    print(f"📋 Authorization URL: http://{host}:{port}/oauth/authorize")
    print(f"🎫 Token URL: http://{host}:{port}/oauth/token")
    print(f"👤 UserInfo URL: http://{host}:{port}/oauth/userinfo")
    
    uvicorn.run(app, host=host, port=port, log_level="info")