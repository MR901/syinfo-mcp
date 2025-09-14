#!/bin/bash

# Syinfo MCP Development Environment Service Startup Script
# This script starts the syinfo MCP server in development mode

set -e

echo "🚀 Starting Syinfo MCP Development Environment..."

# Set up environment
export WORKSPACE_ROOT="${WORKSPACE_ROOT:-/workspaces/syinfo-mcp}"
export PYTHONPATH="${WORKSPACE_ROOT}/python:${PYTHONPATH}"

# Create log directory
mkdir -p /tmp/mcp_logs

# Function to log with timestamp
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

# Function to check if service is running
check_service() {
    local port=$1
    local service_name=$2
    if curl -s -f "http://localhost:${port}/" > /dev/null 2>&1; then
        log "✅ ${service_name} is running on port ${port}"
        return 0
    else
        log "❌ ${service_name} is not responding on port ${port}"
        return 1
    fi
}

# Start MCP server in background
log "🔧 Starting Syinfo MCP Server..."
cd "${WORKSPACE_ROOT}"

# Start the MCP server
nohup python3 python/syinfo/mcp/src/mcp_server.py > /tmp/mcp_logs/mcp_server.log 2>&1 &
MCP_PID=$!
echo $MCP_PID > /tmp/mcp_logs/mcp_server.pid

# Wait a moment for services to start
sleep 3

# Check services
log "🔍 Checking service status..."
if check_service 8000 "MCP Server"; then
    log "✅ All services started successfully!"
    log "📊 MCP Server: http://localhost:8000"
    log "📝 Logs available in /tmp/mcp_logs/"
else
    log "⚠️  Some services may not be fully ready yet"
    log "📝 Check logs in /tmp/mcp_logs/ for details"
fi

log "🎉 Syinfo MCP Development Environment is ready!"
log "💡 Use 'python python/syinfo/mcp/src/mcp_server.py' to run MCP server manually"
