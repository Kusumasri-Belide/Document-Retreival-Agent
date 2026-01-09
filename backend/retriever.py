import os
import pickle
from typing import Optional, Tuple, List

import faiss
import numpy as np

from backend.config import VECTOR_STORE_DIR
from backend.embedding_utils import get_embedding_client

# -------- In-memory singletons (lazy-loaded) --------
_embedding_client: Optional = None
_index: Optional[faiss.Index] = None
_chunks: Optional[List[str]] = None


# ----------------- Helpers -----------------
def _paths() -> Tuple[str, str]:
    """Return absolute paths to the FAISS index and chunks store."""
    index_path = os.path.join(VECTOR_STORE_DIR, "faiss_index.bin")
    chunks_path = os.path.join(VECTOR_STORE_DIR, "chunks.pkl")
    return index_path, chunks_path


def _normalize(v: np.ndarray) -> np.ndarray:
    """L2-normalize vectors (so inner-product approximates cosine)."""
    n = np.linalg.norm(v, axis=1, keepdims=True)
    n[n == 0] = 1.0
    return v / n


def _embedding_client_once():
    """Get the embedding client once."""
    global _embedding_client
    if _embedding_client is None:
        _embedding_client = get_embedding_client()
    return _embedding_client


def _ensure_loaded() -> None:
    """Load FAISS index + chunks from disk if not already loaded."""
    global _index, _chunks
    if _index is not None and _chunks is not None:
        return

    index_path, chunks_path = _paths()
    if not (os.path.exists(index_path) and os.path.exists(chunks_path)):
        raise FileNotFoundError(
            "Vector store not found. Expected files:\n"
            f"- {index_path}\n- {chunks_path}\n"
            "Run the embed step to (re)build the vector store."
        )

    _index = faiss.read_index(index_path)
    with open(chunks_path, "rb") as f:
        _chunks = pickle.load(f)


def reload_index() -> None:
    """
    Force the process to reload the FAISS index & chunks from disk.
    Call this after rebuilding the vector store (e.g., MCP reindex()).
    """
    global _index, _chunks, _embedding_client
    _index = None
    _chunks = None
    _embedding_client = None
    _ensure_loaded()


def _embed_query(q: str) -> np.ndarray:
    """Embed a single query string using the configured embedding provider."""
    client = _embedding_client_once()
    embedding = client.embed_single(q)
    vec = np.array([embedding], dtype="float32")
    return _normalize(vec)


# ----------------- Public API -----------------
def retrieve_relevant_chunks(query: str, k: int = 4) -> str:
    """
    Return top-k chunks concatenated with separators.
    Raises FileNotFoundError if the vector store is missing.
    """
    _ensure_loaded()
    assert _index is not None and _chunks is not None

    if not _chunks:
        return ""

    qv = _embed_query(query)
    k = max(1, min(k, len(_chunks)))  # clamp k to available chunks
    scores, idx = _index.search(qv, k)

    selected = [ _chunks[i] for i in idx[0] if 0 <= i < len(_chunks) ]
    return "\n\n---\n\n".join(selected)
