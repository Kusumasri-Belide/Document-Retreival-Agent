#!/bin/bash
# Setup persistent OAuth credentials (one-time setup)

CREDENTIALS_FILE="/home/ubuntu/mcp-new/.oauth_credentials"

echo "🔐 Setting up persistent OAuth credentials..."

if [ -f "$CREDENTIALS_FILE" ]; then
    echo "📋 Found existing credentials:"
    source "$CREDENTIALS_FILE"
    echo "   Client ID: $OAUTH_CLIENT_ID"
    echo "   Client Secret: $OAUTH_CLIENT_SECRET"
    echo ""
    read -p "Do you want to generate new credentials? (y/N): " REGENERATE
    if [[ ! "$REGENERATE" =~ ^[Yy]$ ]]; then
        echo "✅ Using existing credentials"
        exit 0
    fi
fi

# Generate new credentials
CLIENT_SECRET=$(openssl rand -hex 32)

# Save to file
cat > "$CREDENTIALS_FILE" << EOF
# OAuth 2.0 Credentials for MCP Server
# Generated on: $(date)
export OAUTH_CLIENT_ID="servicenow-mcp-client"
export OAUTH_CLIENT_SECRET="$CLIENT_SECRET"
export OAUTH_REDIRECT_URI="https://ven04195.service-now.com/oauth_redirect.do"
export HOST="0.0.0.0"
export PORT="8001"
EOF

# Make file readable only by owner
chmod 600 "$CREDENTIALS_FILE"

echo "✅ Persistent OAuth credentials saved!"
echo ""
echo "📋 Your OAuth Configuration:"
echo "   Client ID: servicenow-mcp-client"
echo "   Client Secret: $CLIENT_SECRET"
echo "   Redirect URI: https://ven04195.service-now.com/oauth_redirect.do"
echo ""

# Get EC2 IP
EC2_IP=$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4 2>/dev/null)
if [ -z "$EC2_IP" ]; then
    EC2_IP="13.53.171.101"
fi

echo "🌐 ServiceNow Configuration:"
echo "   Client registration type: Manual Registration"
echo "   Grant type: Authorization Code"
echo "   Token authentication method: Client Secret Basic"
echo "   Client ID: servicenow-mcp-client"
echo "   Client secret: $CLIENT_SECRET"
echo "   Auth scopes: mcp:read mcp:write"
echo "   Authorization URL: http://$EC2_IP:8001/oauth/authorize"
echo "   Token URL: http://$EC2_IP:8001/oauth/token"
echo "   Token Revocation URL: http://$EC2_IP:8001/oauth/revoke"
echo ""
echo "💾 These credentials will persist across restarts and updates!"
echo "🔄 To regenerate credentials, run this script again."