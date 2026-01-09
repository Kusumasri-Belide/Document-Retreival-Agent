#!/bin/bash
# OAuth 2.0 Setup Script for MCP Server

echo "🔐 Setting up OAuth 2.0 for MCP Server..."

# Generate secure client secret
CLIENT_SECRET=$(openssl rand -hex 32)

# Set environment variables
export OAUTH_CLIENT_ID="servicenow-mcp-client"
export OAUTH_CLIENT_SECRET="$CLIENT_SECRET"
# CHANGE THIS: Replace with your actual ServiceNow instance URL
# Example: https://dev12345.service-now.com or https://yourcompany.service-now.com
SERVICENOW_INSTANCE="https://ven04195.service-now.com"
export OAUTH_REDIRECT_URI="$SERVICENOW_INSTANCE/oauth_redirect.do"
export HOST="0.0.0.0"
export PORT="8001"

echo "✅ OAuth 2.0 Configuration:"
echo "   Client ID: $OAUTH_CLIENT_ID"
echo "   Client Secret: $OAUTH_CLIENT_SECRET"
echo "   Redirect URI: $OAUTH_REDIRECT_URI"
echo ""
echo "🌐 OAuth Endpoints:"
echo "   Authorization: http://$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4):8001/oauth/authorize"
echo "   Token: http://$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4):8001/oauth/token"
echo "   UserInfo: http://$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4):8001/oauth/userinfo"
echo "   Revoke: http://$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4):8001/oauth/revoke"
echo ""
echo "📋 ServiceNow Configuration:"
echo "   Authorization URL: http://$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4):8001/oauth/authorize"
echo "   Token URL: http://$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4):8001/oauth/token"
echo "   Client ID: $OAUTH_CLIENT_ID"
echo "   Client Secret: $OAUTH_CLIENT_SECRET"
echo ""
echo "🚀 Starting OAuth MCP Server..."

python3 mcp_server_oauth.py
