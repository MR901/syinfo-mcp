#!/bin/bash

# FogLAMP MCP Complete Service Startup Script
# Modern, robust service management for development environment

set -e

# Color output for better readability
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

log() {
    echo -e "${BLUE}[$(date '+%H:%M:%S')]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1" >&2
}

warn() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

header() {
    echo -e "${CYAN}$1${NC}"
}

# Function to check if a service is running on a port
is_service_running() {
    local port=$1
    if command -v netstat >/dev/null 2>&1; then
        netstat -tlnp 2>/dev/null | grep -q ":$port "
    else
        lsof -i :$port >/dev/null 2>&1
    fi
}

# Function to wait for a service to start
wait_for_service() {
    local service_name=$1
    local port=$2
    local max_attempts=${3:-15}
    local attempt=1
    
    log "Waiting for $service_name (port $port)..."
    while [ $attempt -le $max_attempts ]; do
        if is_service_running "$port"; then
            success "$service_name is running on port $port"
            return 0
        fi
        printf "."
        sleep 2
        attempt=$((attempt + 1))
    done
    
    echo "" # New line after dots
    error "$service_name failed to start on port $port after $((max_attempts * 2)) seconds"
    return 1
}

# Function to start a service if not running
start_service() {
    local service_name=$1
    local port=$2
    local start_command=$3
    local check_command=${4:-""}
    
    if is_service_running "$port"; then
        success "$service_name already running on port $port"
        return 0
    fi
    
    log "Starting $service_name..."
    eval "$start_command"
    
    if wait_for_service "$service_name" "$port"; then
        if [ -n "$check_command" ]; then
            log "Running health check for $service_name..."
            if eval "$check_command"; then
                success "$service_name health check passed"
            else
                warn "$service_name started but health check failed"
            fi
        fi
        return 0
    else
        error "Failed to start $service_name"
        return 1
    fi
}

# Function to start MCP server
start_mcp_server() {
    # Simple workspace detection
    if [ -z "$WORKSPACE_ROOT" ]; then
        if [ -f "python/foglamp/services/mcp/src/mcp_server.py" ]; then
            export WORKSPACE_ROOT="$(pwd)"
        else
            for possible_root in "/workspaces"/*; do
                if [ -d "$possible_root" ] && [ -f "$possible_root/python/foglamp/services/mcp/src/mcp_server.py" ]; then
                    export WORKSPACE_ROOT="$possible_root"
                    break
                fi
            done
        fi
    fi
    
    if [ -z "$MCP_SCRIPT" ]; then
        export MCP_SCRIPT="$WORKSPACE_ROOT/python/foglamp/services/mcp/src/mcp_server.py"
    fi
    
    local project_root="$WORKSPACE_ROOT"
    
    if ! [ -d "$project_root" ]; then
        error "Project root not found: $project_root"
        return 1
    fi
    
    cd "$project_root"
    
    # Kill any existing MCP processes
    pkill -f "mcp_server.py" 2>/dev/null || true
    pkill -f "mcp_supervisor.sh" 2>/dev/null || true
    sleep 2
    
    # Make sure log directory exists
    mkdir -p /tmp/mcp_logs
    
    # Set environment variables
    export MCP_HOST="0.0.0.0"
    export MCP_PORT="8000"
    export FOGLAMP_HOST="localhost"
    export FOGLAMP_PORT="8081"
    export MCP_TRANSPORT="streamable-http"
    
    # Start MCP server in background
    log "Starting MCP Server..."
    
    if [ -z "$MCP_SCRIPT" ] || [ ! -f "$MCP_SCRIPT" ]; then
        error "MCP_SCRIPT not found: $MCP_SCRIPT"
        return 1
    fi
    
    nohup python3 "$MCP_SCRIPT" \
        > /tmp/mcp_logs/mcp_server.log 2> /tmp/mcp_logs/mcp_error.log &
    
    local mcp_pid=$!
    echo $mcp_pid > /tmp/mcp_server.pid
    
    if wait_for_service "MCP Server" 8000; then
        # Test MCP server response
        if curl -s -w "%{http_code}" -o /dev/null "http://localhost:8000/mcp" | grep -q "406"; then
            success "MCP Server responding correctly (HTTP 406 expected for GET)"
        else
            warn "MCP Server started but response test inconclusive"
        fi
        return 0
    else
        error "MCP Server failed to start"
        if [ -f /tmp/mcp_logs/mcp_error.log ]; then
            log "Recent MCP error log:"
            tail -10 /tmp/mcp_logs/mcp_error.log
        fi
        return 1
    fi
}

# Function to display service summary
show_service_summary() {
    header "🎯 Service Status Summary"
    header "========================"
    
    # Check each service
    if is_service_running 5432; then
        success "✓ PostgreSQL (port 5432)"
    else
        error "✗ PostgreSQL (port 5432)"
    fi
    
    if is_service_running 80; then
        success "✓ nginx/FogLAMP GUI (port 80)"
    else
        error "✗ nginx/FogLAMP GUI (port 80)"
    fi
    
    if is_service_running 8081; then
        success "✓ FogLAMP API (port 8081)"
    else
        error "✗ FogLAMP API (port 8081)"
    fi
    
    if is_service_running 8000; then
        success "✓ MCP Server (port 8000)"
    else
        error "✗ MCP Server (port 8000)"
    fi
    
    echo ""
    header "🌍 Access URLs"
    header "============="
    log "From host machine:"
    log "  • FogLAMP GUI:  http://localhost:50080"
    log "  • FogLAMP API:  http://localhost:58081/foglamp/ping"
    log "  • MCP Server:   http://localhost:58000/mcp"
    log ""
    log "From inside container:"
    log "  • FogLAMP GUI:  http://localhost:80"
    log "  • FogLAMP API:  http://localhost:8081/foglamp/ping"
    log "  • MCP Server:   http://localhost:8000/mcp"
    
    echo ""
    header "📋 Log Locations"
    header "================"
    log "  • MCP Server:   /tmp/mcp_logs/mcp_server.log"
    log "  • MCP Errors:   /tmp/mcp_logs/mcp_error.log"
    log "  • FogLAMP:      /usr/local/foglamp/data/logs/"
}

# Main function
main() {
    header "🚀 FogLAMP MCP Development Environment Startup"
    header "==============================================="
    log "Starting at: $(date)"
    echo ""
    
    # Initialize services if needed
    if [ ! -f "/tmp/.services-initialized" ]; then
        log "First run detected - initializing services..."
        if [ -x "/usr/local/bin/init-services.sh" ]; then
            /usr/local/bin/init-services.sh
        else
            warn "Service initialization script not found, continuing with manual startup..."
        fi
    fi
    
    # Start PostgreSQL
    if ! start_service "PostgreSQL" 5432 "sudo service postgresql start"; then
        error "PostgreSQL startup failed"
        exit 1
    fi
    
    # Start nginx
    if ! start_service "nginx" 80 "sudo service nginx start" "curl -s http://localhost:80/health >/dev/null"; then
        error "nginx startup failed"
        exit 1
    fi
    
    # Start FogLAMP
    if ! start_service "FogLAMP API" 8081 "sudo /usr/local/foglamp/bin/foglamp start" "curl -s http://localhost:8081/foglamp/ping >/dev/null"; then
        error "FogLAMP startup failed"
        exit 1
    fi
    
    # Start MCP Server
    if ! start_mcp_server; then
        error "MCP Server startup failed"
        exit 1
    fi
    
    echo ""
    success "All services started successfully!"
    
    # Show summary
    echo ""
    show_service_summary
    
    echo ""
    header "🎉 Environment Ready for Development!"
    header "====================================="
    log "You can now:"
    log "  1. Access FogLAMP GUI at http://localhost:50080"
    log "  2. Use MCP server with Cursor - configurations auto-generated!"
    log "     • Cursor config: ~/.cursor/mcp.json (primary stdio connection)"
    log "     • Workspace config: .cursor/mcp.json (HTTP fallback)"
    log "     • HTTP endpoint: http://localhost:58000/mcp"
    log "  3. Test connectivity: python3 show_environment_status.py"
    log "  4. Monitor logs: tail -f /tmp/mcp_logs/mcp_server.log"
    log "  5. Check FogLAMP status: /usr/local/foglamp/bin/foglamp status"
    log ""
    log "💡 MCP Features Available in Cursor:"
    log "   • Query FogLAMP services and readings"
    log "   • Direct PostgreSQL database access"
    log "   • System monitoring and log analysis"
    log "   • Configuration management tools"
}

# Handle script interruption
trap 'echo -e "\n${YELLOW}Startup interrupted by user${NC}"; exit 1' INT TERM

# Run main function
main "$@"