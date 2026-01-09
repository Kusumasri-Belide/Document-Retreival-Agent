#!/bin/bash
# Upload MCP Document Agent to EC2 Instance
# Run this script from your local machine

# Configuration - UPDATE THESE VALUES
EC2_IP="YOUR_EC2_PUBLIC_IP"
KEY_FILE="path/to/your-key.pem"
EC2_USER="ec2-user"  # or "ubuntu" for Ubuntu instances

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

print_status() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Check if configuration is set
if [ "$EC2_IP" = "YOUR_EC2_PUBLIC_IP" ]; then
    print_error "Please update EC2_IP in this script with your actual EC2 public IP"
    exit 1
fi

if [ "$KEY_FILE" = "path/to/your-key.pem" ]; then
    print_error "Please update KEY_FILE in this script with your actual key file path"
    exit 1
fi

if [ ! -f "$KEY_FILE" ]; then
    print_error "Key file not found: $KEY_FILE"
    exit 1
fi

echo "🚀 Uploading MCP Document Agent to EC2..."
echo "Target: $EC2_USER@$EC2_IP"
echo "================================================"

# Test SSH connection
echo "🔐 Testing SSH connection..."
ssh -i "$KEY_FILE" -o ConnectTimeout=10 "$EC2_USER@$EC2_IP" "echo 'SSH connection successful'" || {
    print_error "SSH connection failed. Check your EC2_IP, KEY_FILE, and security group settings."
    exit 1
}
print_status "SSH connection successful"

# Create remote directory
echo "📁 Creating remote directory..."
ssh -i "$KEY_FILE" "$EC2_USER@$EC2_IP" "mkdir -p /home/$EC2_USER/mcp-new"

# Upload main application files
echo "📤 Uploading main application files..."

# Upload backend directory
if [ -d "backend" ]; then
    scp -i "$KEY_FILE" -r backend "$EC2_USER@$EC2_IP:/home/$EC2_USER/mcp-new/"
    print_status "Backend directory uploaded"
else
    print_warning "Backend directory not found"
fi

# Upload data directory
if [ -d "data" ]; then
    scp -i "$KEY_FILE" -r data "$EC2_USER@$EC2_IP:/home/$EC2_USER/mcp-new/"
    print_status "Data directory uploaded"
else
    print_warning "Data directory not found - will be created on server"
fi

# Upload MCP server files
if [ -d "mcp-new-main" ]; then
    scp -i "$KEY_FILE" -r mcp-new-main "$EC2_USER@$EC2_IP:/home/$EC2_USER/mcp-new/"
    print_status "MCP server files uploaded"
else
    print_error "mcp-new-main directory not found"
    exit 1
fi

# Upload configuration files
echo "📤 Uploading configuration files..."

files_to_upload=(".env" "requirements.txt" "credentials.json" "token.json" "app.py")
for file in "${files_to_upload[@]}"; do
    if [ -f "$file" ]; then
        scp -i "$KEY_FILE" "$file" "$EC2_USER@$EC2_IP:/home/$EC2_USER/mcp-new/"
        print_status "$file uploaded"
    else
        print_warning "$file not found - skipping"
    fi
done

# Copy MCP server files to root level for easier access
echo "🔧 Setting up file structure on server..."
ssh -i "$KEY_FILE" "$EC2_USER@$EC2_IP" "
cd /home/$EC2_USER/mcp-new
cp mcp-new-main/mcp-new-main/* . 2>/dev/null || echo 'Files copied'
chmod +x *.sh 2>/dev/null || true
ls -la
"

print_status "File structure set up"

echo ""
echo "🎉 Upload Complete!"
echo "================================================"
echo ""
echo "📋 Next Steps:"
echo "1. SSH into your EC2 instance:"
echo "   ssh -i $KEY_FILE $EC2_USER@$EC2_IP"
echo ""
echo "2. Navigate to the application directory:"
echo "   cd /home/$EC2_USER/mcp-new"
echo ""
echo "3. Run the quick deployment script:"
echo "   chmod +x quick_deploy_ec2.sh"
echo "   ./quick_deploy_ec2.sh"
echo ""
echo "4. Update your .env file with actual Azure OpenAI credentials:"
echo "   nano .env"
echo ""
echo "5. Restart the server after updating credentials:"
echo "   ./manage_server.sh restart"
echo ""

print_status "Ready for deployment! 🚀"