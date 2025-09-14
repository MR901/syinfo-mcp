#!/bin/bash

# Simple MCP Server Runner
# Streamlined version focused on just starting the MCP server

set -e

# Source common workspace detection
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/common_workspace.sh"

# Environment variables with defaults
export MCP_HOST="${MCP_HOST:-0.0.0.0}"
export MCP_PORT="${MCP_PORT:-8000}"
export FOGLAMP_HOST="${FOGLAMP_HOST:-localhost}"
export FOGLAMP_PORT="${FOGLAMP_PORT:-8081}"
export MCP_TRANSPORT="${MCP_TRANSPORT:-streamable-http}"

# Setup workspace environment (will set WORKSPACE_ROOT and MCP_SCRIPT)
if ! setup_workspace_env; then
    error "Failed to setup workspace environment"
    exit 1
fi

# Change to workspace root
cd "$WORKSPACE_ROOT"

# Validate workspace structure
if ! validate_workspace; then
    exit 1
fi
    
# Create log directory
mkdir -p /tmp/mcp_logs

log "Starting MCP Server"
log "Configuration:"
log "  Host: $MCP_HOST"
log "  Port: $MCP_PORT"  
log "  FogLAMP: $FOGLAMP_HOST:$FOGLAMP_PORT"
log "  Transport: $MCP_TRANSPORT"
log "  Working Directory: $(pwd)"
log "  Python: $(python3 --version)"
log ""

# Start MCP server
log "Executing: python3 $MCP_SCRIPT"
exec python3 "$MCP_SCRIPT"