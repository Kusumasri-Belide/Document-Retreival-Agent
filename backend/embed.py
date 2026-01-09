import os, pickle, faiss, numpy as np
from langchain.text_splitter import RecursiveCharacterTextSplitter
from backend.config import PROCESSED_DIR, VECTOR_STORE_DIR
from backend.embedding_utils import get_embedding_client

def _normalize(mat: np.ndarray) -> np.ndarray:
    n = np.linalg.norm(mat, axis=1, keepdims=True)
    n[n == 0] = 1.0
    return mat / n

def embed_and_store():
    embedding_client = get_embedding_client()

    splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    chunks: list[str] = []

    for fname in os.listdir(PROCESSED_DIR):
        fp = os.path.join(PROCESSED_DIR, fname)
        if not os.path.isfile(fp):
            continue
        with open(fp, "r", encoding="utf-8") as f:
            text = f.read()
        chunks.extend(splitter.split_text(text))

    if not chunks:
        print("No processed text found. Put .txt files in data/processed/")
        return

    print(f"Embedding {len(chunks)} chunks...")
    vecs: list[list[float]] = []
    B = 64  # Batch size
    for i in range(0, len(chunks), B):
        batch = chunks[i:i+B]
        batch_embeddings = embedding_client.embed_texts(batch)
        vecs.extend(batch_embeddings)
        print(f"Processed {min(i+B, len(chunks))}/{len(chunks)} chunks")

    X = np.array(vecs, dtype="float32")
    X = _normalize(X)

    index = faiss.IndexFlatIP(X.shape[1])  # cosine via normalized dot product
    index.add(X)
    os.makedirs(VECTOR_STORE_DIR, exist_ok=True)
    faiss.write_index(index, os.path.join(VECTOR_STORE_DIR, "faiss_index.bin"))

    with open(os.path.join(VECTOR_STORE_DIR, "chunks.pkl"), "wb") as f:
        pickle.dump(chunks, f)

    print(f"✅ Stored {len(chunks)} chunks | dim={X.shape[1]}")

if __name__ == "__main__":
    embed_and_store()