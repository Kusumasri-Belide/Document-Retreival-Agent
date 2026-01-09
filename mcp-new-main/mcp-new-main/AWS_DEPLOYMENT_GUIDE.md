# AWS EC2 Deployment Guide - MCP Server with Document Agent

Complete step-by-step guide to deploy your integrated MCP server on AWS EC2.

## 🚀 Phase 1: AWS EC2 Setup

### 1.1 Launch EC2 Instance

```bash
# Using AWS CLI (or use AWS Console)
aws ec2 run-instances \
    --image-id ami-0c02fb55956c7d316 \
    --instance-type t3.medium \
    --key-name your-key-pair \
    --security-group-ids sg-xxxxxxxxx \
    --subnet-id subnet-xxxxxxxxx \
    --tag-specifications 'ResourceType=instance,Tags=[{Key=Name,Value=mcp-document-server}]'
```

**Or via AWS Console:**
1. Go to EC2 Dashboard → Launch Instance
2. **Name**: `mcp-document-server`
3. **AMI**: Amazon Linux 2023 (or Ubuntu 22.04 LTS)
4. **Instance Type**: `t3.medium` (minimum for document processing)
5. **Key Pair**: Select or create new
6. **Security Group**: Create with these rules:
   - SSH (22) - Your IP
   - HTTP (80) - 0.0.0.0/0
   - Custom TCP (8001) - 0.0.0.0/0
7. **Storage**: 20 GB gp3

### 1.2 Connect to Instance

```bash
# Get your instance public IP
aws ec2 describe-instances --filters "Name=tag:Name,Values=mcp-document-server" --query 'Reservations[0].Instances[0].PublicIpAddress'

# Connect via SSH
ssh -i your-key.pem ec2-user@YOUR_EC2_PUBLIC_IP
# or for Ubuntu: ssh -i your-key.pem ubuntu@YOUR_EC2_PUBLIC_IP
```

## 🔧 Phase 2: System Setup

### 2.1 Update System & Install Dependencies

```bash
# For Amazon Linux 2023
sudo yum update -y
sudo yum install -y python3 python3-pip git htop curl wget

# For Ubuntu (alternative)
# sudo apt update && sudo apt upgrade -y
# sudo apt install -y python3 python3-pip git htop curl wget

# Install Python virtual environment
sudo yum install -y python3-venv
# or for Ubuntu: sudo apt install -y python3-venv

# Verify installations
python3 --version
pip3 --version
git --version
```

### 2.2 Create Application Directory

```bash
# Create main directory
sudo mkdir -p /home/ec2-user/mcp-new
sudo chown ec2-user:ec2-user /home/ec2-user/mcp-new
cd /home/ec2-user/mcp-new

# Create Python virtual environment
python3 -m venv venv
source venv/bin/activate

# Verify virtual environment
which python
which pip
```

## 📁 Phase 3: Code Deployment

### 3.1 Upload Your Code

**Option A: Git Clone (if you have a repository)**
```bash
cd /home/ec2-user
git clone https://github.com/yourusername/your-repo.git mcp-new
cd mcp-new
```

**Option B: Manual Upload via SCP**
```bash
# From your local machine, upload the entire project
scp -i your-key.pem -r /path/to/your/project/* ec2-user@YOUR_EC2_IP:/home/ec2-user/mcp-new/

# Upload specific directories
scp -i your-key.pem -r ./mcp-new-main ec2-user@YOUR_EC2_IP:/home/ec2-user/mcp-new/
scp -i your-key.pem -r ./backend ec2-user@YOUR_EC2_IP:/home/ec2-user/mcp-new/
scp -i your-key.pem -r ./data ec2-user@YOUR_EC2_IP:/home/ec2-user/mcp-new/
scp -i your-key.pem .env ec2-user@YOUR_EC2_IP:/home/ec2-user/mcp-new/
scp -i your-key.pem requirements.txt ec2-user@YOUR_EC2_IP:/home/ec2-user/mcp-new/
```

**Option C: Create Files Directly**
```bash
# If uploading individual files, create the structure:
mkdir -p /home/ec2-user/mcp-new/{backend,data/{docs,processed,vector_store},mcp-new-main}
```

### 3.2 Set Up File Structure

```bash
cd /home/ec2-user/mcp-new

# Ensure correct structure
ls -la
# Should show: backend/, data/, mcp-new-main/, .env, requirements.txt, etc.

# Copy MCP server files to root level for easier access
cp mcp-new-main/mcp-new-main/* . 2>/dev/null || echo "Files already in place"

# Make scripts executable
chmod +x *.sh
```

## 🔐 Phase 4: Environment Configuration

### 4.1 Create Environment File

```bash
cd /home/ec2-user/mcp-new

# Create .env file with your Azure OpenAI credentials
cat > .env << 'EOF'
# Azure OpenAI Configuration
AZURE_OPENAI_API_KEY=your_azure_openai_key_here
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com
AZURE_OPENAI_API_VERSION=2024-02-15-preview
AZURE_OPENAI_DEPLOYMENT=your_chat_deployment_name
AZURE_OPENAI_EMBEDDING_MODEL=your_embedding_deployment_name

# Embedding Configuration
EMBEDDING_PROVIDER=azure
EMBEDDING_MODEL_NAME=text-embedding-ada-002

# Optional: OpenAI Fallback
OPENAI_API_KEY=your_openai_key_if_needed

# Microsoft/OneDrive (if using OneDrive integration)
MICROSOFT_CLIENT_ID=your_client_id
MICROSOFT_CLIENT_SECRET=your_client_secret
MICROSOFT_TENANT_ID=common

# Server Configuration
HOST=0.0.0.0
PORT=8001
EOF

# Secure the environment file
chmod 600 .env
```

### 4.2 Set Up OAuth Credentials

```bash
# Run OAuth setup script
./setup_persistent_oauth.sh

# This will create .oauth_credentials file with:
# - Client ID: servicenow-mcp-client  
# - Generated client secret
# - Your EC2 IP for redirect URIs
```

## 📦 Phase 5: Install Dependencies

### 5.1 Install Python Packages

```bash
cd /home/ec2-user/mcp-new
source venv/bin/activate

# Upgrade pip first
pip install --upgrade pip

# Install all dependencies
pip install -r requirements.txt

# Verify critical packages
python -c "import fastmcp, mcp, faiss, openai, langchain; print('✅ All packages installed')"
```

### 5.2 Install System Dependencies for Document Processing

```bash
# For unstructured document processing
sudo yum install -y poppler-utils tesseract

# For Ubuntu alternative:
# sudo apt install -y poppler-utils tesseract-ocr

# Verify installations
pdfinfo -v
tesseract --version
```

## 🗂️ Phase 6: Document Setup

### 6.1 Upload Your Documents

```bash
# Create documents directory
mkdir -p /home/ec2-user/mcp-new/data/docs

# Upload documents from local machine
scp -i your-key.pem /path/to/your/documents/* ec2-user@YOUR_EC2_IP:/home/ec2-user/mcp-new/data/docs/

# Or if documents are already in your uploaded code:
ls -la data/docs/
```

### 6.2 Process Documents and Build Index

```bash
cd /home/ec2-user/mcp-new
source venv/bin/activate

# Test document processing
python -c "
from backend.extract_answers import extract_all
from backend.embed import embed_and_store
print('🔄 Processing documents...')
extract_all()
print('🔄 Building vector index...')
embed_and_store()
print('✅ Document processing complete!')
"

# Verify processed files
ls -la data/processed/
ls -la data/vector_store/
```

## 🚀 Phase 7: Deploy and Start Server

### 7.1 Run Integration Deployment

```bash
cd /home/ec2-user/mcp-new

# Run the deployment script
./deploy_with_document_agent.sh

# This will:
# - Copy all necessary files
# - Install dependencies
# - Set up proper structure
```

### 7.2 Test the Integration

```bash
# Test imports and configuration
python test_document_integration.py

# Should show:
# ✅ All modules imported successfully
# ✅ Configuration loaded
# ✅ Documents and vector store available
```

### 7.3 Install as System Service

```bash
# Install as systemd service
sudo ./install_service.sh

# This creates a service that:
# - Starts automatically on boot
# - Restarts if it crashes
# - Runs in background
# - Logs to systemd journal
```

### 7.4 Start the Server

```bash
# Start the service
sudo systemctl start mcp-server

# Check status
sudo systemctl status mcp-server

# Enable auto-start on boot
sudo systemctl enable mcp-server

# View logs
sudo journalctl -u mcp-server -f
```

## 🧪 Phase 8: Testing & Verification

### 8.1 Test Server Endpoints

```bash
# Get your EC2 public IP
EC2_IP=$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4)
echo "Server running at: http://$EC2_IP:8001"

# Test health endpoint
curl http://$EC2_IP:8001/health

# Test OAuth discovery
curl http://$EC2_IP:8001/.well-known/oauth-authorization-server

# Test server info
curl http://$EC2_IP:8001/info
```

### 8.2 Test Document Agent Functions

```bash
# Test direct API (without OAuth for testing)
curl -X POST http://localhost:8001/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "What documents are available?"}'
```

## 🔧 Phase 9: ServiceNow Configuration

### 9.1 Get OAuth Configuration Details

```bash
# Display OAuth configuration for ServiceNow
source .oauth_credentials
EC2_IP=$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4)

echo "📋 ServiceNow OAuth Configuration:"
echo "Client ID: $OAUTH_CLIENT_ID"
echo "Client Secret: $OAUTH_CLIENT_SECRET"
echo "Authorization URL: http://$EC2_IP:8001/oauth/authorize"
echo "Token URL: http://$EC2_IP:8001/oauth/token"
echo "Token Revocation URL: http://$EC2_IP:8001/oauth/revoke"
echo "Scopes: mcp:read mcp:write"
```

### 9.2 Configure ServiceNow

In your ServiceNow instance (`ven04195.service-now.com`):

1. **Navigate to**: System OAuth → Application Registry
2. **Create New**: OAuth API endpoint for external clients
3. **Configure**:
   - Name: `MCP Document Agent`
   - Client ID: `servicenow-mcp-client`
   - Client Secret: `[from above output]`
   - Redirect URL: `https://ven04195.service-now.com/oauth_redirect.do`
   - Authorization URL: `http://[EC2_IP]:8001/oauth/authorize`
   - Token URL: `http://[EC2_IP]:8001/oauth/token`

## 🔄 Phase 10: Management & Monitoring

### 10.1 Server Management Commands

```bash
# Start server
./manage_server.sh start

# Stop server  
./manage_server.sh stop

# Restart server
./manage_server.sh restart

# Check status
./manage_server.sh status

# View live logs
./manage_server.sh logs

# Update code and restart
./manage_server.sh update
```

### 10.2 Monitoring & Logs

```bash
# System resource usage
htop

# Disk usage
df -h

# Service logs
sudo journalctl -u mcp-server -f --since "1 hour ago"

# Application logs
tail -f /var/log/mcp-server.log  # if configured

# Check listening ports
sudo netstat -tlnp | grep 8001
```

## 🔒 Phase 11: Security & Production Hardening

### 11.1 Firewall Configuration

```bash
# Configure firewall (if using firewalld)
sudo firewall-cmd --permanent --add-port=8001/tcp
sudo firewall-cmd --permanent --add-port=80/tcp
sudo firewall-cmd --reload

# For iptables alternative:
# sudo iptables -A INPUT -p tcp --dport 8001 -j ACCEPT
```

### 11.2 SSL/HTTPS Setup (Optional but Recommended)

```bash
# Install certbot for Let's Encrypt
sudo yum install -y certbot

# Get SSL certificate (requires domain name)
# sudo certbot certonly --standalone -d your-domain.com

# Configure nginx as reverse proxy with SSL
sudo yum install -y nginx
```

## 🎯 Phase 12: Final Verification

### 12.1 Complete System Test

```bash
# Run comprehensive test
python test_document_integration.py

# Test all MCP tools through direct API
curl -X POST http://localhost:8001/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "List all available documents"}'
```

### 12.2 Performance Check

```bash
# Check memory usage
free -h

# Check CPU usage
top

# Check disk space
df -h

# Check service status
systemctl status mcp-server
```

## 📋 Quick Reference Commands

```bash
# Essential commands for daily operations:

# Check server status
./manage_server.sh status

# View logs
./manage_server.sh logs

# Restart server
./manage_server.sh restart

# Reindex documents (when adding new docs)
# Use ServiceNow MCP tool: reindex_documents

# Check system resources
htop
df -h

# View service logs
sudo journalctl -u mcp-server -f
```

## 🆘 Troubleshooting

### Common Issues:

1. **Port 8001 not accessible**:
   ```bash
   # Check security group allows port 8001
   # Check if service is running: systemctl status mcp-server
   ```

2. **Import errors**:
   ```bash
   # Ensure virtual environment is activated
   source venv/bin/activate
   pip install -r requirements.txt
   ```

3. **Document processing fails**:
   ```bash
   # Check document formats are supported
   # Ensure unstructured dependencies installed
   ```

4. **OAuth issues**:
   ```bash
   # Regenerate credentials
   ./setup_persistent_oauth.sh
   ```

Your MCP server with document agent is now fully deployed on AWS EC2! 🎉