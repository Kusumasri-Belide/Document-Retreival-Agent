# MCP Server with SharePoint Document Agent Integration

This MCP server integrates your SharePoint document agent as MCP tools, providing OAuth 2.0 authentication for ServiceNow integration.

## 🏗️ Architecture

```
ServiceNow ←→ OAuth 2.0 ←→ MCP Server ←→ Document Agent ←→ Azure OpenAI + FAISS
```

### Components
- **OAuth 2.0 Layer**: Handles ServiceNow authentication
- **MCP Protocol**: JSON-RPC 2.0 interface for tool calls
- **Document Agent**: Your SharePoint document processing system
- **Vector Store**: FAISS index with Azure OpenAI embeddings

## 🛠️ Available MCP Tools

### Document Agent Tools
1. **ask_document** - Answer questions using document index and Azure OpenAI
2. **list_documents** - List all processed documents
3. **reindex_documents** - Rebuild document index and vector store
4. **get_document_content** - Get full content of specific document
5. **get_vector_stats** - Vector store statistics
6. **search_chunks** - Search document chunks without AI generation

### Utility Tools
7. **now** - Get current date/time
8. **add** - Add two integers

## 🚀 Deployment

### 1. Initial Setup
```bash
# Set up OAuth credentials (one-time)
./setup_persistent_oauth.sh

# Deploy document agent integration
./deploy_with_document_agent.sh

# Install as system service
./manage_server.sh install
```

### 2. ServiceNow Configuration
Use the OAuth details from `setup_persistent_oauth.sh`:

```
Client ID: servicenow-mcp-client
Client Secret: [generated 64-char hex]
Grant Type: Authorization Code
Token Auth Method: Client Secret Basic
Authorization URL: http://[EC2-IP]:8001/oauth/authorize
Token URL: http://[EC2-IP]:8001/oauth/token
Token Revocation URL: http://[EC2-IP]:8001/oauth/revoke
Scopes: mcp:read mcp:write
```

### 3. Document Processing
```bash
# Check available documents
curl -X POST http://localhost:8001/mcp \
  -H "Authorization: Bearer [token]" \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","method":"tools/call","params":{"name":"list_documents","arguments":{}},"id":1}'

# Reindex documents (if needed)
curl -X POST http://localhost:8001/mcp \
  -H "Authorization: Bearer [token]" \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","method":"tools/call","params":{"name":"reindex_documents","arguments":{}},"id":1}'
```

## 📋 Management Commands

```bash
# Start server
./manage_server.sh start

# Check status
./manage_server.sh status

# View logs
./manage_server.sh logs

# Restart server
./manage_server.sh restart

# Update code and restart
./manage_server.sh update

# Stop server
./manage_server.sh stop
```

## 🧪 Testing

```bash
# Test integration
python3 test_document_integration.py

# Test OAuth endpoints
curl http://localhost:8001/.well-known/oauth-authorization-server
```

## 📁 File Structure

```
mcp-new-main/
├── mcp_server_oauth.py          # Main OAuth MCP server
├── setup_persistent_oauth.sh    # OAuth credential setup
├── deploy_with_document_agent.sh # Deployment script
├── manage_server.sh             # Server management
├── install_service.sh           # Service installation
├── test_document_integration.py # Integration tests
├── requirements.txt             # Python dependencies
└── backend/                     # Document agent modules
    ├── config.py               # Configuration
    ├── llm_answer.py           # Azure OpenAI integration
    ├── retriever.py            # FAISS vector search
    ├── embedding_utils.py      # Embedding providers
    ├── extract_answers.py      # Document processing
    └── embed.py                # Vector store building
```

## 🔧 Configuration

### Environment Variables (.env)
```bash
# Azure OpenAI
AZURE_OPENAI_API_KEY=your_key
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com
AZURE_OPENAI_DEPLOYMENT=your_chat_deployment
AZURE_OPENAI_EMBEDDING_MODEL=your_embedding_deployment

# OAuth (auto-generated)
OAUTH_CLIENT_ID=servicenow-mcp-client
OAUTH_CLIENT_SECRET=generated_secret
OAUTH_REDIRECT_URI=https://ven04195.service-now.com/oauth_redirect.do
```

### Data Directories
- `data/docs/` - Original documents (Word, PDF, etc.)
- `data/processed/` - Extracted text files
- `data/vector_store/` - FAISS index and chunks

## 🔍 Troubleshooting

### Common Issues

1. **Import Errors**
   ```bash
   # Ensure all dependencies are installed
   pip3 install -r requirements.txt
   ```

2. **Vector Store Missing**
   ```bash
   # Rebuild the index
   # Use reindex_documents tool or run directly:
   python3 -c "from backend.extract_answers import extract_all; from backend.embed import embed_and_store; extract_all(); embed_and_store()"
   ```

3. **OAuth Issues**
   ```bash
   # Regenerate credentials
   ./setup_persistent_oauth.sh
   ```

4. **Service Not Starting**
   ```bash
   # Check logs
   sudo journalctl -u mcp-server -f
   
   # Check service status
   sudo systemctl status mcp-server
   ```

### Logs
- **Service logs**: `sudo journalctl -u mcp-server -f`
- **Manual logs**: Check console output when running directly

## 🔐 Security Notes

- OAuth credentials are stored in `/home/ubuntu/mcp-new/.oauth_credentials`
- File permissions are set to 600 (owner read/write only)
- All API endpoints require valid Bearer tokens
- CORS is configured for Azure deployment

## 📈 Monitoring

### Health Check
```bash
curl http://localhost:8001/health
```

### Server Info
```bash
curl http://localhost:8001/info
```

### Vector Store Stats
Use the `get_vector_stats` MCP tool through ServiceNow or direct API call.

## 🔄 Updates

To update the server with new code:
```bash
./manage_server.sh update
```

This will:
1. Pull latest code from git
2. Restart the service
3. Show updated status

## 🎯 ServiceNow Integration

Once configured in ServiceNow, you can:

1. **Ask Questions**: Use `ask_document` tool with natural language queries
2. **Browse Documents**: Use `list_documents` to see available content
3. **Search Content**: Use `search_chunks` for specific information
4. **Manage Index**: Use `reindex_documents` when adding new documents

Example ServiceNow script:
```javascript
// Call MCP tool from ServiceNow
var result = mcp.callTool('ask_document', {
    question: 'What is the Azure AI Foundry architecture?'
});
gs.info('Answer: ' + result.content[0].text);
```