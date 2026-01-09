from openai import AzureOpenAI
from backend.retriever import retrieve_relevant_chunks
from backend.config import (
    AZURE_OPENAI_API_KEY, AZURE_OPENAI_ENDPOINT,
    AZURE_OPENAI_API_VERSION, AZURE_OPENAI_DEPLOYMENT
)

_client = AzureOpenAI(
    api_key=AZURE_OPENAI_API_KEY,
    api_version=AZURE_OPENAI_API_VERSION,
    azure_endpoint=AZURE_OPENAI_ENDPOINT,
)

def generate_answer(query: str) -> str:
    context = retrieve_relevant_chunks(query)
    messages = [
        {"role": "system", "content": "You are a helpful document assistant. Use the context faithfully; say 'Not found in docs' if needed."},
        {"role": "user", "content": f"Context:\n{context}\n\nQuestion: {query}"}
    ]
    resp = _client.chat.completions.create(
        model=AZURE_OPENAI_DEPLOYMENT,   # deployment name
        messages=messages,
        temperature=0.2,
        max_tokens=500,
    )
    return resp.choices[0].message.content
