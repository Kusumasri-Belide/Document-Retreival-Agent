#!/bin/bash
# Quick EC2 Deployment Script for MCP Document Agent Server
# Run this script on your EC2 instance after uploading your code

set -e  # Exit on any error

echo "🚀 Starting MCP Document Agent Server Deployment on EC2..."
echo "================================================================"

# Configuration
APP_DIR="/home/ec2-user/mcp-new"
VENV_DIR="$APP_DIR/venv"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

print_status() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Check if running as correct user
if [ "$USER" != "ec2-user" ] && [ "$USER" != "ubuntu" ]; then
    print_warning "This script is designed for ec2-user or ubuntu. Current user: $USER"
fi

# Step 1: Update system
echo "📦 Step 1: Updating system packages..."
if command -v yum &> /dev/null; then
    sudo yum update -y
    sudo yum install -y python3 python3-pip git htop curl wget python3-venv poppler-utils tesseract
    print_status "Amazon Linux packages installed"
elif command -v apt &> /dev/null; then
    sudo apt update && sudo apt upgrade -y
    sudo apt install -y python3 python3-pip git htop curl wget python3-venv poppler-utils tesseract-ocr
    print_status "Ubuntu packages installed"
else
    print_error "Unsupported package manager. Please install dependencies manually."
    exit 1
fi

# Step 2: Create directory structure
echo "📁 Step 2: Setting up directory structure..."
mkdir -p "$APP_DIR"/{backend,data/{docs,processed,vector_store}}
cd "$APP_DIR"

# Step 3: Set up Python virtual environment
echo "🐍 Step 3: Setting up Python virtual environment..."
if [ ! -d "$VENV_DIR" ]; then
    python3 -m venv venv
    print_status "Virtual environment created"
else
    print_status "Virtual environment already exists"
fi

source venv/bin/activate
pip install --upgrade pip
print_status "Virtual environment activated and pip upgraded"

# Step 4: Check for uploaded files
echo "📋 Step 4: Checking for uploaded files..."
if [ ! -f "requirements.txt" ]; then
    print_error "requirements.txt not found. Please upload your project files first."
    echo "Use: scp -i your-key.pem -r /path/to/your/project/* ec2-user@$EC2_IP:$APP_DIR/"
    exit 1
fi

if [ ! -d "backend" ]; then
    print_error "backend directory not found. Please upload your project files first."
    exit 1
fi

print_status "Project files found"

# Step 5: Install Python dependencies
echo "📦 Step 5: Installing Python dependencies..."
pip install -r requirements.txt
print_status "Python dependencies installed"

# Step 6: Set up environment file
echo "🔧 Step 6: Setting up environment configuration..."
if [ ! -f ".env" ]; then
    print_warning ".env file not found. Creating template..."
    cat > .env << 'EOF'
# Azure OpenAI Configuration - PLEASE UPDATE THESE VALUES
AZURE_OPENAI_API_KEY=your_azure_openai_key_here
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com
AZURE_OPENAI_API_VERSION=2024-02-15-preview
AZURE_OPENAI_DEPLOYMENT=your_chat_deployment_name
AZURE_OPENAI_EMBEDDING_MODEL=your_embedding_deployment_name

# Embedding Configuration
EMBEDDING_PROVIDER=azure
EMBEDDING_MODEL_NAME=text-embedding-ada-002

# Server Configuration
HOST=0.0.0.0
PORT=8001
EOF
    chmod 600 .env
    print_warning "Please edit .env file with your actual Azure OpenAI credentials!"
    echo "Run: nano .env"
else
    print_status ".env file already exists"
fi

# Step 7: Set up OAuth credentials
echo "🔐 Step 7: Setting up OAuth credentials..."
if [ -f "setup_persistent_oauth.sh" ]; then
    chmod +x setup_persistent_oauth.sh
    ./setup_persistent_oauth.sh
    print_status "OAuth credentials configured"
else
    print_warning "setup_persistent_oauth.sh not found. OAuth setup skipped."
fi

# Step 8: Make scripts executable
echo "🔧 Step 8: Making scripts executable..."
chmod +x *.sh 2>/dev/null || true
print_status "Scripts made executable"

# Step 9: Test imports
echo "🧪 Step 9: Testing imports and configuration..."
python3 -c "
try:
    import fastmcp, mcp, faiss, openai, langchain
    print('✅ Core packages imported successfully')
except ImportError as e:
    print(f'❌ Import error: {e}')
    exit(1)

try:
    from backend.config import PROCESSED_DIR, VECTOR_STORE_DIR
    print('✅ Backend configuration imported')
except ImportError as e:
    print(f'❌ Backend import error: {e}')
    exit(1)
"

if [ $? -eq 0 ]; then
    print_status "Import tests passed"
else
    print_error "Import tests failed. Check your configuration."
    exit 1
fi

# Step 10: Process documents (if any exist)
echo "📄 Step 10: Processing documents..."
if [ "$(ls -A data/docs/ 2>/dev/null)" ]; then
    print_status "Documents found. Processing..."
    python3 -c "
from backend.extract_answers import extract_all
from backend.embed import embed_and_store
print('🔄 Extracting text from documents...')
extract_all()
print('🔄 Building vector index...')
embed_and_store()
print('✅ Document processing complete!')
"
    print_status "Documents processed and indexed"
else
    print_warning "No documents found in data/docs/. You can add documents later and run reindex."
fi

# Step 11: Install as system service
echo "🔧 Step 11: Installing as system service..."
if [ -f "install_service.sh" ]; then
    sudo ./install_service.sh
    print_status "System service installed"
else
    print_warning "install_service.sh not found. Manual service setup required."
fi

# Step 12: Start the server
echo "🚀 Step 12: Starting the MCP server..."
if systemctl is-active --quiet mcp-server; then
    print_status "MCP server is already running"
else
    sudo systemctl start mcp-server
    sleep 3
    if systemctl is-active --quiet mcp-server; then
        print_status "MCP server started successfully"
    else
        print_error "Failed to start MCP server. Check logs with: sudo journalctl -u mcp-server -f"
        exit 1
    fi
fi

# Step 13: Get server information
echo "📋 Step 13: Getting server information..."
EC2_IP=$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4 2>/dev/null || echo "localhost")

echo ""
echo "🎉 DEPLOYMENT COMPLETE!"
echo "================================================================"
echo ""
echo "📊 Server Status:"
sudo systemctl status mcp-server --no-pager -l
echo ""
echo "🌐 Server URLs:"
echo "   Health Check: http://$EC2_IP:8001/health"
echo "   Server Info:  http://$EC2_IP:8001/info"
echo "   OAuth Discovery: http://$EC2_IP:8001/.well-known/oauth-authorization-server"
echo ""

if [ -f ".oauth_credentials" ]; then
    source .oauth_credentials
    echo "🔐 OAuth Configuration for ServiceNow:"
    echo "   Client ID: $OAUTH_CLIENT_ID"
    echo "   Client Secret: $OAUTH_CLIENT_SECRET"
    echo "   Authorization URL: http://$EC2_IP:8001/oauth/authorize"
    echo "   Token URL: http://$EC2_IP:8001/oauth/token"
    echo "   Token Revocation URL: http://$EC2_IP:8001/oauth/revoke"
    echo "   Scopes: mcp:read mcp:write"
    echo ""
fi

echo "🛠️ Available MCP Tools:"
echo "   • ask_document - Answer questions using document index"
echo "   • list_documents - List available processed documents"
echo "   • reindex_documents - Rebuild document index"
echo "   • get_document_content - Get specific document content"
echo "   • get_vector_stats - Vector store statistics"
echo "   • search_chunks - Search document chunks"
echo "   • now - Get current date/time"
echo "   • add - Add two numbers"
echo ""

echo "📋 Management Commands:"
echo "   Check status: ./manage_server.sh status"
echo "   View logs:    ./manage_server.sh logs"
echo "   Restart:      ./manage_server.sh restart"
echo "   Update:       ./manage_server.sh update"
echo ""

echo "🧪 Test Commands:"
echo "   Test health:  curl http://$EC2_IP:8001/health"
echo "   Test info:    curl http://$EC2_IP:8001/info"
echo "   Run tests:    python3 test_document_integration.py"
echo ""

if [ ! -f ".env" ] || grep -q "your_azure_openai_key_here" .env; then
    print_warning "IMPORTANT: Please update your .env file with actual Azure OpenAI credentials!"
    echo "   Edit with: nano .env"
    echo "   Then restart: ./manage_server.sh restart"
fi

print_status "Deployment completed successfully! 🎉"