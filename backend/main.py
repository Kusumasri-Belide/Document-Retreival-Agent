import os
from fastapi import FastAPI, HTTPException
from starlette.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from backend.llm_answer import generate_answer
from backend.mcp_server import mcp

app = FastAPI(
    title="Document Agent MCP Server", 
    version="1.0.0",
    description="MCP Server for document retrieval and Q&A using Azure OpenAI and OneDrive"
)

# CORS configuration for Azure deployment
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure specific origins in production
    allow_methods=["GET", "POST", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["Mcp-Session-Id"],  # required by browser MCP clients
)

# Expose MCP over HTTP at /mcp
app.mount("/mcp", mcp.streamable_http_app())


class Query(BaseModel):
    question: str


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/ask")
async def ask_question(q: Query):
    try:
        answer = generate_answer(q.question)
        return {"answer": answer}
    except FileNotFoundError as e:
        # Vector store not built yet
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        # Bubble other errors with message
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/")
def root():
    """Root endpoint with server information"""
    return {
        "name": "Document Agent MCP Server",
        "version": "1.0.0",
        "mcp_endpoint": "/mcp",
        "health_endpoint": "/health",
        "api_endpoint": "/ask"
    }

@app.get("/info")
def server_info():
    """Server information and available endpoints"""
    return {
        "server": "Document Agent MCP Server",
        "endpoints": {
            "mcp": "/mcp - MCP protocol endpoint",
            "health": "/health - Health check",
            "ask": "/ask - Direct Q&A endpoint",
            "root": "/ - Server information"
        },
        "mcp_tools": [
            "ask - Answer questions using the document index",
            "list_docs - List available processed documents", 
            "reindex - Rebuild the document index"
        ],
        "mcp_resources": [
            "doc://{name} - Read processed document content",
            "vector://stats - Vector store statistics"
        ]
    }