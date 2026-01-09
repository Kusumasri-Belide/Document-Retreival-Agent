# Environment Setup Guide

This guide helps you set up your environment variables securely for the MCP Document Agent.

## 🔐 Security First

**Important**: Never commit actual API keys, tokens, or credentials to git. This repository uses `.env.template` as a template and `.env` is ignored by git.

## 📋 Setup Steps

### 1. Create Your Environment File

```bash
# Copy the template
cp .env.template .env

# Edit with your actual values
nano .env  # or use your preferred editor
```

### 2. Required Configuration

Fill in these required values in your `.env` file:

#### Azure OpenAI (Required)
```bash
AZURE_OPENAI_API_KEY=your_actual_azure_openai_key
AZURE_OPENAI_ENDPOINT=https://your-resource-name.openai.azure.com
AZURE_OPENAI_DEPLOYMENT=your_chat_deployment_name
AZURE_OPENAI_EMBEDDING_MODEL=your_embedding_deployment_name
```

**How to get these values:**
1. Go to [Azure Portal](https://portal.azure.com)
2. Navigate to your Azure OpenAI resource
3. Go to "Keys and Endpoint" section
4. Copy the key and endpoint
5. Go to "Model deployments" to get deployment names

#### Microsoft Graph/OneDrive (Optional)
```bash
MICROSOFT_CLIENT_ID=your_microsoft_app_client_id
MICROSOFT_CLIENT_SECRET=your_microsoft_app_client_secret
```

**How to get these values:**
1. Go to [Azure App Registrations](https://portal.azure.com/#view/Microsoft_AAD_RegisteredApps)
2. Create new app registration or use existing
3. Copy Application (client) ID
4. Go to "Certificates & secrets" → Create new client secret

### 3. Optional Configuration

#### OpenAI API (Fallback)
```bash
OPENAI_API_KEY=your_openai_api_key
```

#### Hugging Face (Local embeddings)
```bash
HUGGINGFACE_API_TOKEN=your_huggingface_token
```

#### Google OAuth (Google Drive integration)
```bash
GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_client_secret
```

### 4. Verify Configuration

```bash
# Test your configuration
python -c "
from backend.config import *
print('✅ Configuration loaded successfully')
print(f'Azure endpoint: {AZURE_OPENAI_ENDPOINT}')
print(f'Deployment: {AZURE_OPENAI_DEPLOYMENT}')
"
```

## 🚀 Deployment Configurations

### Local Development
```bash
HOST=127.0.0.1
PORT=8001
LOG_LEVEL=DEBUG
```

### Production (AWS EC2)
```bash
HOST=0.0.0.0
PORT=8001
LOG_LEVEL=INFO
```

## 🔒 Security Best Practices

1. **Never commit `.env` files**
   - Always use `.env.template` for examples
   - Keep actual credentials in `.env` (ignored by git)

2. **Use environment-specific files**
   - `.env.development` for local development
   - `.env.production` for production
   - `.env.staging` for staging

3. **Rotate credentials regularly**
   - Azure OpenAI keys
   - OAuth client secrets
   - API tokens

4. **Use least privilege access**
   - Only grant necessary permissions
   - Use separate credentials for different environments

## 🧪 Testing Configuration

```bash
# Test Azure OpenAI connection
python -c "
from backend.embedding_utils import get_embedding_client
client = get_embedding_client()
result = client.embed_single('test')
print(f'✅ Embedding test successful: {len(result)} dimensions')
"

# Test document processing
python -c "
from backend.llm_answer import generate_answer
# This will fail if no documents are indexed, but tests the connection
try:
    answer = generate_answer('test question')
    print('✅ LLM connection successful')
except FileNotFoundError:
    print('✅ LLM connection successful (no documents indexed yet)')
"
```

## 🔧 Troubleshooting

### Common Issues

1. **Azure OpenAI Authentication Error**
   ```
   Error: Invalid API key or endpoint
   ```
   - Verify `AZURE_OPENAI_API_KEY` and `AZURE_OPENAI_ENDPOINT`
   - Check if the key is active in Azure Portal

2. **Deployment Not Found**
   ```
   Error: The API deployment for this resource does not exist
   ```
   - Verify `AZURE_OPENAI_DEPLOYMENT` matches your deployment name
   - Check deployment status in Azure Portal

3. **Embedding Model Error**
   ```
   Error: Invalid embedding model
   ```
   - Verify `AZURE_OPENAI_EMBEDDING_MODEL` deployment name
   - Ensure embedding model is deployed and running

4. **Permission Errors**
   ```
   Error: Access denied
   ```
   - Check Azure OpenAI resource permissions
   - Verify subscription and resource group access

### Environment File Not Loading

```bash
# Check if .env file exists
ls -la .env

# Check file permissions
chmod 600 .env

# Verify python-dotenv is installed
pip install python-dotenv
```

## 📁 File Structure

```
your-project/
├── .env                 # Your actual credentials (ignored by git)
├── .env.template        # Template file (committed to git)
├── .gitignore          # Ignores .env and other sensitive files
├── backend/
│   └── config.py       # Loads environment variables
└── SETUP_ENVIRONMENT.md # This guide
```

## 🔄 Environment Updates

When updating environment variables:

1. **Update `.env`** with new values
2. **Restart the application** to load new values
3. **Test the changes** before deploying
4. **Update `.env.template`** if adding new variables (without actual values)

## 📞 Support

If you encounter issues:

1. Check this guide first
2. Verify all required environment variables are set
3. Test individual components (Azure OpenAI, embeddings, etc.)
4. Check application logs for specific error messages

Remember: Keep your credentials secure and never share them in public repositories! 🔐