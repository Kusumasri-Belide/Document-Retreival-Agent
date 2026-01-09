"""
Embedding utilities with fallback support for multiple providers.
"""
import numpy as np
from typing import List, Optional
from openai import AzureOpenAI, OpenAI
from backend.config import (
    AZURE_OPENAI_API_KEY, AZURE_OPENAI_ENDPOINT, AZURE_OPENAI_API_VERSION,
    AZURE_OPENAI_EMBEDDING_MODEL, OPENAI_API_KEY, EMBEDDING_PROVIDER,
    EMBEDDING_MODEL_NAME
)

class EmbeddingClient:
    def __init__(self):
        self.provider = EMBEDDING_PROVIDER.lower()
        self._azure_client = None
        self._openai_client = None
        self._sentence_transformer = None
        
    def _get_azure_client(self) -> Optional[AzureOpenAI]:
        """Get Azure OpenAI client if configured."""
        if not all([AZURE_OPENAI_API_KEY, AZURE_OPENAI_ENDPOINT, AZURE_OPENAI_EMBEDDING_MODEL]):
            return None
        if self._azure_client is None:
            self._azure_client = AzureOpenAI(
                api_key=AZURE_OPENAI_API_KEY,
                api_version=AZURE_OPENAI_API_VERSION,
                azure_endpoint=AZURE_OPENAI_ENDPOINT,
            )
        return self._azure_client
    
    def _get_openai_client(self) -> Optional[OpenAI]:
        """Get regular OpenAI client if configured."""
        if not OPENAI_API_KEY:
            return None
        if self._openai_client is None:
            self._openai_client = OpenAI(api_key=OPENAI_API_KEY)
        return self._openai_client
    
    def _get_sentence_transformer(self):
        """Get sentence transformer model if available."""
        if self._sentence_transformer is None:
            try:
                from sentence_transformers import SentenceTransformer
                self._sentence_transformer = SentenceTransformer('all-MiniLM-L6-v2')
            except ImportError:
                print("sentence-transformers not installed. Install with: pip install sentence-transformers")
                return None
        return self._sentence_transformer
    
    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """
        Embed a list of texts using the configured provider with fallbacks.
        """
        # Try Azure OpenAI first if configured
        if self.provider == "azure" or self.provider == "auto":
            try:
                client = self._get_azure_client()
                if client:
                    print(f"Using Azure OpenAI embeddings: {AZURE_OPENAI_EMBEDDING_MODEL}")
                    resp = client.embeddings.create(model=AZURE_OPENAI_EMBEDDING_MODEL, input=texts)
                    return [d.embedding for d in resp.data]
            except Exception as e:
                print(f"Azure OpenAI embeddings failed: {e}")
                if self.provider == "azure":
                    raise
        
        # Try regular OpenAI as fallback
        if self.provider in ["openai", "auto"] or self.provider == "azure":
            try:
                client = self._get_openai_client()
                if client:
                    print(f"Using OpenAI embeddings: {EMBEDDING_MODEL_NAME}")
                    resp = client.embeddings.create(model=EMBEDDING_MODEL_NAME, input=texts)
                    return [d.embedding for d in resp.data]
            except Exception as e:
                print(f"OpenAI embeddings failed: {e}")
                if self.provider == "openai":
                    raise
        
        # Try sentence transformers as final fallback
        if self.provider in ["sentence-transformers", "auto"] or self.provider in ["azure", "openai"]:
            try:
                model = self._get_sentence_transformer()
                if model:
                    print("Using local sentence-transformers embeddings")
                    embeddings = model.encode(texts)
                    return embeddings.tolist()
            except Exception as e:
                print(f"Sentence transformers failed: {e}")
                if self.provider == "sentence-transformers":
                    raise
        
        raise RuntimeError("No embedding provider available. Please configure Azure OpenAI, OpenAI API, or install sentence-transformers.")
    
    def embed_single(self, text: str) -> List[float]:
        """Embed a single text."""
        return self.embed_texts([text])[0]

# Global instance
_embedding_client = None

def get_embedding_client() -> EmbeddingClient:
    """Get the global embedding client instance."""
    global _embedding_client
    if _embedding_client is None:
        _embedding_client = EmbeddingClient()
    return _embedding_client