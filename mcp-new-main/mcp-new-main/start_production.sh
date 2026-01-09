#!/bin/bash
# Production startup script for AWS EC2

# Install Python and pip if not available
sudo yum update -y
sudo yum install -y python3 python3-pip

# Install dependencies
pip3 install -r requirements.txt

# Set environment variables
export HOST=0.0.0.0
export PORT=8001

# Start the MCP server
python3 mcp_server.py