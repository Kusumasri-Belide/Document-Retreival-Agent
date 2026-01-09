#!/bin/bash
# MCP Server Management Script

show_help() {
    echo "🔧 MCP Server Management"
    echo "========================"
    echo ""
    echo "Usage: ./manage_server.sh [command]"
    echo ""
    echo "Commands:"
    echo "  start     - Start the MCP server"
    echo "  stop      - Stop the MCP server"
    echo "  restart   - Restart the MCP server"
    echo "  status    - Show server status"
    echo "  logs      - Show live logs"
    echo "  update    - Update server code and restart"
    echo "  install   - Install as system service"
    echo ""
    echo "Examples:"
    echo "  ./manage_server.sh start"
    echo "  ./manage_server.sh logs"
    echo "  ./manage_server.sh update"
}

case "$1" in
    start)
        echo "🚀 Starting MCP server..."
        sudo systemctl start mcp-server
        sudo systemctl status mcp-server --no-pager
        ;;
    stop)
        echo "🛑 Stopping MCP server..."
        sudo systemctl stop mcp-server
        echo "✅ Server stopped"
        ;;
    restart)
        echo "🔄 Restarting MCP server..."
        sudo systemctl restart mcp-server
        sudo systemctl status mcp-server --no-pager
        ;;
    status)
        echo "📊 MCP Server Status:"
        sudo systemctl status mcp-server --no-pager
        echo ""
        echo "🌐 Server should be available at:"
        echo "   http://$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4):8001/mcp"
        ;;
    logs)
        echo "📋 Live MCP Server Logs (Press Ctrl+C to exit):"
        sudo journalctl -u mcp-server -f
        ;;
    update)
        echo "📥 Updating MCP server code..."
        git pull origin main
        echo "🔄 Restarting server with new code..."
        sudo systemctl restart mcp-server
        sleep 2
        sudo systemctl status mcp-server --no-pager
        echo "✅ Update complete!"
        ;;
    install)
        echo "🔧 Installing MCP server as system service..."
        chmod +x install_service.sh
        ./install_service.sh
        ;;
    *)
        show_help
        ;;
esac