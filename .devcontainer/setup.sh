#!/bin/bash

# MCP Server Template Development Environment Setup
set -e  # Exit on any error

echo "🚀 Setting up MCP Server Template Development Environment..."

# Update system packages with error handling
echo "📦 Updating system packages..."
if apt-get update && apt-get upgrade -y; then
    echo "✅ System packages updated successfully"
else
    echo "⚠️  System package update failed, continuing..."
fi

# Install system dependencies
echo "🔧 Installing system dependencies..."
apt-get install -y \
    curl \
    wget \
    git \
    jq \
    tree \
    htop \
    sqlite3 \
    build-essential \
    pkg-config \
    libssl-dev \
    libffi-dev || echo "⚠️  Some system packages failed to install, continuing..."

# Upgrade pip and install Python dependencies
echo "🐍 Installing Python dependencies..."
pip install --upgrade pip setuptools wheel

# Install project dependencies
if [ -f "requirements.txt" ]; then
    echo "📋 Installing project requirements..."
    pip install -r requirements.txt
else
    echo "⚠️  No requirements.txt found, installing core dependencies..."
    pip install \
        mcp==1.12.3 \
        aiohttp==3.12.15 \
        requests==2.32.3 \
        psycopg2-binary==2.9.10 \
        tabulate==0.9.0 \
        beautifulsoup4==4.12.3 \
        pyyaml \
        python-dotenv
fi

# Install development dependencies
echo "🛠️  Installing development dependencies..."
pip install \
    black \
    isort \
    flake8 \
    mypy \
    pytest \
    pytest-asyncio \
    pytest-cov \
    jupyter \
    ipython

# Create development directories
echo "📁 Creating development directories..."
mkdir -p /workspaces/syinfo-mcp/{logs,tmp,examples,tests}

# Set up Git configuration (if not already configured)
if [ -z "$(git config --global user.name)" ]; then
    echo "🔧 Setting up Git configuration..."
    git config --global user.name "Developer"
    git config --global user.email "dev@example.com"
    git config --global init.defaultBranch main
fi

# Create example environment file
if [ ! -f ".env.example" ]; then
    echo "📝 Creating example environment file..."
    cat > .env.example << EOF
# MCP Server Configuration
MCP_SERVER_NAME=My Custom MCP Server
MCP_SERVER_DESCRIPTION=A customized MCP server for my domain
MCP_HOST=0.0.0.0
MCP_PORT=8000
MCP_LOG_LEVEL=INFO
MCP_DEBUG=false

# Transport Configuration
MCP_TRANSPORT=streamable-http
MCP_STATELESS_HTTP=true

# Permissions
MCP_ALLOW_READ_ACCESS=true
MCP_ALLOW_WRITE_ACCESS=false
MCP_ALLOW_DELETE_ACCESS=false

# External API Configuration (optional)
# MCP_EXTERNAL_API_HOST=api.example.com
# MCP_EXTERNAL_API_PORT=443
# MCP_EXTERNAL_API_PROTOCOL=https
# MCP_EXTERNAL_API_AUTH_TOKEN=your-token-here

# Database Configuration (optional)
# MCP_DATABASE_ENABLED=true
# MCP_DATABASE_TYPE=postgresql
# MCP_DATABASE_HOST=localhost
# MCP_DATABASE_PORT=5432
# MCP_DATABASE_NAME=mcp_server
# MCP_DATABASE_USER=mcp_user
# MCP_DATABASE_PASSWORD=mcp_password
EOF
fi

# Create development configuration
if [ ! -f "config.dev.json" ]; then
    echo "⚙️  Creating development configuration..."
    cat > config.dev.json << EOF
{
  "server_name": "Development MCP Server",
  "server_description": "MCP server for development and testing",
  "mcp_host": "0.0.0.0",
  "mcp_port": 8000,
  "mcp_log_level": "DEBUG",
  "mcp_debug": true,
  "allow_read_access": true,
  "allow_write_access": true,
  "allow_delete_access": false,
  "database_enabled": false
}
EOF
fi

# Create a simple Makefile for common tasks
if [ ! -f "Makefile" ]; then
    echo "🔨 Creating Makefile for common tasks..."
    cat > Makefile << 'EOF'
.PHONY: help install dev test lint format clean run-template run-original docker-build

help:  ## Show this help message
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install:  ## Install dependencies
	pip install -r requirements.txt

dev:  ## Install development dependencies
	pip install black isort flake8 mypy pytest pytest-asyncio pytest-cov

test:  ## Run tests
	pytest tests/ -v --cov=src

lint:  ## Run linting
	flake8 src/
	mypy src/

format:  ## Format code
	black src/
	isort src/

clean:  ## Clean up temporary files
	find . -type d -name __pycache__ -delete
	find . -type f -name "*.pyc" -delete
	rm -rf .pytest_cache .coverage htmlcov/

run-template:  ## Run template server
	python -m src.template_server

run-original:  ## Run original server (if available)
	python -m src.mcp_server

docker-build:  ## Build Docker image
	docker build -t mcp-server-template .

docker-run:  ## Run Docker container
	docker run -p 8000:8000 mcp-server-template

logs:  ## View server logs
	tail -f logs/*.log 2>/dev/null || echo "No log files found"

examples:  ## Show usage examples
	@echo "Examples:"
	@echo "  make run-template                 # Run template server"
	@echo "  MCP_DEBUG=true make run-template  # Run with debug"
	@echo "  make test                        # Run all tests"
	@echo "  make lint format                 # Code quality checks"

EOF
fi

# Create example Python test file
if [ ! -f "tests/test_template.py" ]; then
    mkdir -p tests
    echo "🧪 Creating example test file..."
    cat > tests/test_template.py << EOF
"""
Example tests for the template server.
"""

import pytest
from src.template_server import TemplateMCPServer, ServerCapabilities


def test_server_capabilities():
    """Test server capabilities configuration."""
    caps = ServerCapabilities.default()
    assert len(caps.tools_modules) > 0
    assert len(caps.resources_modules) > 0
    assert len(caps.prompts_modules) > 0


def test_template_server_init():
    """Test template server initialization."""
    server = TemplateMCPServer(
        server_name="Test Server",
        host="localhost", 
        port=9000
    )
    
    assert server.server_name == "Test Server"
    assert server.host == "localhost"
    assert server.port == 9000


@pytest.mark.asyncio
async def test_server_capabilities_empty():
    """Test server with empty capabilities."""
    caps = ServerCapabilities.empty()
    server = TemplateMCPServer(
        server_name="Empty Server",
        capabilities=caps
    )
    
    assert len(server.capabilities.tools_modules) == 0
    assert len(server.capabilities.resources_modules) == 0
    assert len(server.capabilities.prompts_modules) == 0
EOF

    # Create __init__.py for tests
    touch tests/__init__.py
fi

# Set proper permissions
echo "🔒 Setting permissions..."
chmod +x .devcontainer/setup.sh
find . -name "*.py" -exec chmod 644 {} \;

# Create a simple health check script
echo "🏥 Creating health check script..."
cat > health_check.py << EOF
#!/usr/bin/env python3
"""
Simple health check script for the MCP server.
"""

import requests
import sys
import os

def check_server_health(host="localhost", port=8000):
    """Check if the MCP server is running and healthy."""
    try:
        # Try to connect to the server
        response = requests.get(f"http://{host}:{port}/health", timeout=5)
        if response.status_code == 200:
            print(f"✅ Server is healthy at {host}:{port}")
            return True
        else:
            print(f"⚠️  Server responded with status {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Server health check failed: {e}")
        return False

if __name__ == "__main__":
    host = os.getenv("MCP_HOST", "localhost")
    port = int(os.getenv("MCP_PORT", "8000"))
    
    if check_server_health(host, port):
        sys.exit(0)
    else:
        sys.exit(1)
EOF

chmod +x health_check.py

echo "✅ Development environment setup complete!"
echo ""
echo "🎯 Next steps:"
echo "  1. Copy .env.example to .env and customize"
echo "  2. Run 'make help' to see available commands"
echo "  3. Run 'make run-template' to start the template server"
echo "  4. Run 'make test' to run the test suite"
echo ""
echo "🔧 Available commands:"
echo "  - make run-template    # Run template server"
echo "  - make test           # Run tests"
echo "  - make lint           # Check code quality"
echo "  - make format         # Format code"
echo ""
echo "Happy coding! 🚀"
