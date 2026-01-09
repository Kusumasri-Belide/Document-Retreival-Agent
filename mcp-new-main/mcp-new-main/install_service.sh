#!/bin/bash
# Install MCP Server as a systemd service

echo "🔧 Installing MCP Server as a system service..."

# Create service file
sudo tee /etc/systemd/system/mcp-server.service > /dev/null <<EOF
[Unit]
Description=OAuth MCP Server for ServiceNow
After=network.target
StartLimitIntervalSec=0

[Service]
Type=simple
Restart=always
RestartSec=5
User=ubuntu
WorkingDirectory=/home/ubuntu/mcp-new
Environment=PATH=/home/ubuntu/mcp-new/venv/bin:/usr/local/bin:/usr/bin:/bin
ExecStart=/bin/bash -c 'source /home/ubuntu/mcp-new/.oauth_credentials && /home/ubuntu/mcp-new/venv/bin/python /home/ubuntu/mcp-new/mcp_server_oauth.py'
StandardOutput=journal
StandardError=journal
SyslogIdentifier=mcp-server

[Install]
WantedBy=multi-user.target
EOF

# Reload systemd and enable service
sudo systemctl daemon-reload
sudo systemctl enable mcp-server.service

echo "✅ MCP Server service installed!"
echo ""
echo "📋 Service Management Commands:"
echo "   Start:    sudo systemctl start mcp-server"
echo "   Stop:     sudo systemctl stop mcp-server"
echo "   Restart:  sudo systemctl restart mcp-server"
echo "   Status:   sudo systemctl status mcp-server"
echo "   Logs:     sudo journalctl -u mcp-server -f"
echo ""
echo "🚀 Starting the service now..."
sudo systemctl start mcp-server

echo ""
echo "📊 Service Status:"
sudo systemctl status mcp-server --no-pager

echo ""
echo "🎉 Your MCP server is now running as a service!"
echo "   ✅ Starts automatically on boot"
echo "   ✅ Restarts if it crashes"
echo "   ✅ Runs even when you disconnect SSH"
echo "   ✅ Survives server reboots"