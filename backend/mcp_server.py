# backend/mcp_server.py
from pathlib import Path
from typing import List
import os
import pickle
import faiss

from mcp.server.fastmcp import FastMCP

from backend.llm_answer import generate_answer
from backend.ingest_onedrive import fetch_onedrive_folder
from backend.extract_answers import extract_all          # <-- fixed import
from backend.embed import embed_and_store
from backend.retriever import reload_index             # <-- reload in-memory FAISS
from backend.config import PROCESSED_DIR, VECTOR_STORE_DIR

mcp = FastMCP(
    name="DocAgent",
    instructions="Document QA and maintenance tools over your Azure+FAISS RAG index.",
)

# ---------- TOOLS ----------
@mcp.tool()
def ask(question: str) -> str:
    """Answer a question using the current vector index + docs."""
    return generate_answer(question)

@mcp.tool()
def list_docs() -> List[str]:
    """List available processed text files (data/processed)."""
    return sorted([f for f in os.listdir(PROCESSED_DIR) if f.endswith(".txt")])

@mcp.tool()
def reindex() -> str:
    """Re-extract texts and rebuild the FAISS index, then refresh in-memory state."""
    extract_all()          # data/docs -> data/processed
    embed_and_store()      # data/processed -> data/vector_store
    reload_index()         # ensure the running process uses the new index
    return "Reindex complete."

# ---------- RESOURCES ----------
@mcp.resource("doc://{name}")
def read_doc(name: str) -> str:
    """Return the contents of a processed .txt by file name (exact match)."""
    p = Path(PROCESSED_DIR) / name
    if not p.exists():
        return f"Not found: {name}"
    return p.read_text(encoding="utf-8", errors="ignore")

@mcp.resource("vector://stats")
def vector_stats() -> str:
    """Basic stats about the FAISS index and chunk store."""
    idx_path = Path(VECTOR_STORE_DIR) / "faiss_index.bin"
    ch_path  = Path(VECTOR_STORE_DIR) / "chunks.pkl"
    if not idx_path.exists() or not ch_path.exists():
        return "Vector store missing. Run the reindex tool."
    index = faiss.read_index(str(idx_path))
    with open(ch_path, "rb") as f:
        chunks = pickle.load(f)
    return f"chunks={len(chunks)}, dim={index.d}, type={type(index).__name__}"

if __name__ == "__main__":
    # STDIO mode for local MCP dev (avoid printing to stdout here)
    mcp.run()
