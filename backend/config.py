import os
from dotenv import load_dotenv
load_dotenv()

AZURE_OPENAI_API_KEY = os.getenv("AZURE_OPENAI_API_KEY")
AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")  # e.g., https://your-resource.openai.azure.com
AZURE_OPENAI_API_VERSION = os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-15-preview")
AZURE_OPENAI_DEPLOYMENT = os.getenv("AZURE_OPENAI_DEPLOYMENT")  # chat/completions deployment
AZURE_OPENAI_EMBEDDING_MODEL = os.getenv("AZURE_OPENAI_EMBEDDING_MODEL")  # embeddings deployment

# Fallback embedding options
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")  # Regular OpenAI API key
EMBEDDING_PROVIDER = os.getenv("EMBEDDING_PROVIDER", "azure")  # "azure", "openai", or "sentence-transformers"
EMBEDDING_MODEL_NAME = os.getenv("EMBEDDING_MODEL_NAME", "text-embedding-ada-002")  # Model name for fallback

# OneDrive Configuration
MICROSOFT_CLIENT_ID = os.getenv("MICROSOFT_CLIENT_ID")
MICROSOFT_CLIENT_SECRET = os.getenv("MICROSOFT_CLIENT_SECRET")  # Optional for public client
MICROSOFT_TENANT_ID = os.getenv("MICROSOFT_TENANT_ID", "common")  # "common" for personal accounts
ONEDRIVE_FOLDER_PATH = os.getenv("ONEDRIVE_FOLDER_PATH", "/")  # Root folder by default

DATA_DIR = "data"
DOCS_DIR = os.path.join(DATA_DIR, "docs")
PROCESSED_DIR = os.path.join(DATA_DIR, "processed")
VECTOR_STORE_DIR = os.path.join(DATA_DIR, "vector_store")

for d in [DOCS_DIR, PROCESSED_DIR, VECTOR_STORE_DIR]:
    os.makedirs(d, exist_ok=True)