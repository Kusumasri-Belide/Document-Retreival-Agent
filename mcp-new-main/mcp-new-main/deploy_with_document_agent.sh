#!/bin/bash
# Deploy MCP Server with Document Agent Integration

echo "🚀 Deploying MCP Server with Document Agent..."

# Set paths
MCP_DIR="/home/ubuntu/mcp-new"
MAIN_APP_DIR="/home/ubuntu/mcp-new"  # Adjust this to your main app path if different

# Create necessary directories
mkdir -p "$MCP_DIR/backend"
mkdir -p "$MCP_DIR/data/docs"
mkdir -p "$MCP_DIR/data/processed" 
mkdir -p "$MCP_DIR/data/vector_store"

# Copy backend modules from main application
echo "📁 Copying backend modules..."
cp "$MAIN_APP_DIR/backend/__init__.py" "$MCP_DIR/backend/" 2>/dev/null || touch "$MCP_DIR/backend/__init__.py"
cp "$MAIN_APP_DIR/backend/config.py" "$MCP_DIR/backend/"
cp "$MAIN_APP_DIR/backend/embedding_utils.py" "$MCP_DIR/backend/"
cp "$MAIN_APP_DIR/backend/extract_answers.py" "$MCP_DIR/backend/"
cp "$MAIN_APP_DIR/backend/embed.py" "$MCP_DIR/backend/"
cp "$MAIN_APP_DIR/backend/retriever.py" "$MCP_DIR/backend/"
cp "$MAIN_APP_DIR/backend/llm_answer.py" "$MCP_DIR/backend/"

# Copy environment and configuration files
echo "🔧 Copying configuration files..."
cp "$MAIN_APP_DIR/.env" "$MCP_DIR/" 2>/dev/null || echo "⚠️ No .env file found in main app"
cp "$MAIN_APP_DIR/credentials.json" "$MCP_DIR/" 2>/dev/null || echo "⚠️ No credentials.json found"
cp "$MAIN_APP_DIR/token.json" "$MCP_DIR/" 2>/dev/null || echo "⚠️ No token.json found"

# Copy existing data if available
echo "📄 Copying existing data..."
if [ -d "$MAIN_APP_DIR/data" ]; then
    cp -r "$MAIN_APP_DIR/data/"* "$MCP_DIR/data/" 2>/dev/null || echo "⚠️ No data directory found"
fi

# Install Python dependencies
echo "📦 Installing dependencies..."
cd "$MCP_DIR"
pip3 install -r requirements.txt

# Load OAuth credentials
echo "🔐 Loading OAuth credentials..."
if [ -f "$MCP_DIR/.oauth_credentials" ]; then
    source "$MCP_DIR/.oauth_credentials"
    echo "✅ OAuth credentials loaded"
else
    echo "⚠️ OAuth credentials not found. Run setup_persistent_oauth.sh first"
fi

# Set permissions
chmod +x "$MCP_DIR"/*.sh

echo ""
echo "✅ Deployment complete!"
echo ""
echo "📋 Available MCP Tools:"
echo "   • ask_document - Answer questions using document index"
echo "   • list_documents - List available processed documents"
echo "   • reindex_documents - Rebuild document index"
echo "   • get_document_content - Get specific document content"
echo "   • get_vector_stats - Vector store statistics"
echo "   • search_chunks - Search document chunks"
echo "   • now - Get current date/time"
echo "   • add - Add two numbers"
echo ""
echo "🚀 To start the server:"
echo "   ./manage_server.sh start"
echo ""
echo "📊 To check status:"
echo "   ./manage_server.sh status"
echo ""
echo "📋 To view logs:"
echo "   ./manage_server.sh logs"