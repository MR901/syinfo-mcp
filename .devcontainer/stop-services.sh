#!/bin/bash

# FogLAMP MCP Development Environment Service Shutdown
# This script stops all services started by init-services.sh

set -e  # Exit on error

# Color output for better readability
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log() {
    echo -e "${BLUE}[$(date '+%Y-%m-%d %H:%M:%S')]${NC} $1"
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

# Function to check if a service is running
is_service_running() {
    local service=$1
    local port=$2
    
    if command -v netstat >/dev/null 2>&1; then
        netstat -tlnp | grep -q ":$port "
    else
        lsof -i :$port >/dev/null 2>&1
    fi
}

# Function to wait for service to stop
wait_for_service_stop() {
    local service_name=$1
    local port=$2
    local max_attempts=${3:-30}
    local attempt=1
    
    log "Waiting for $service_name to stop on port $port..."
    while [ $attempt -le $max_attempts ]; do
        if ! is_service_running "$service_name" "$port"; then
            success "$service_name stopped successfully"
            return 0
        fi
        sleep 1
        attempt=$((attempt + 1))
    done
    
    warn "$service_name still running on port $port after $max_attempts attempts"
    return 1
}

# Function to stop FogLAMP
stop_foglamp() {
    log "Stopping FogLAMP..."
    
    if is_service_running "FogLAMP" 8081; then
        # Try graceful shutdown first
        if command -v /usr/local/foglamp/bin/foglamp >/dev/null 2>&1; then
            sudo /usr/local/foglamp/bin/foglamp stop
            
            # Wait for graceful shutdown
            if wait_for_service_stop "FogLAMP" 8081 30; then
                success "FogLAMP stopped gracefully"
            else
                warn "FogLAMP did not stop gracefully, attempting force stop..."
                
                # Find and kill FogLAMP processes
                local foglamp_pids=$(ps aux | grep '[f]oglamp' | awk '{print $2}' || true)
                if [ -n "$foglamp_pids" ]; then
                    log "Force stopping FogLAMP processes: $foglamp_pids"
                    sudo kill -TERM $foglamp_pids 2>/dev/null || true
                    sleep 5
                    
                    # Check if still running, use KILL signal
                    foglamp_pids=$(ps aux | grep '[f]oglamp' | awk '{print $2}' || true)
                    if [ -n "$foglamp_pids" ]; then
                        log "Force killing FogLAMP processes: $foglamp_pids"
                        sudo kill -KILL $foglamp_pids 2>/dev/null || true
                    fi
                fi
                
                if wait_for_service_stop "FogLAMP" 8081 10; then
                    success "FogLAMP stopped forcefully"
                else
                    error "Failed to stop FogLAMP completely"
                fi
            fi
        else
            warn "FogLAMP binary not found, attempting to kill processes..."
            local foglamp_pids=$(ps aux | grep '[f]oglamp' | awk '{print $2}' || true)
            if [ -n "$foglamp_pids" ]; then
                sudo kill -TERM $foglamp_pids 2>/dev/null || true
                sleep 3
                sudo kill -KILL $foglamp_pids 2>/dev/null || true
            fi
        fi
    else
        log "FogLAMP is not running"
    fi
}

# Function to stop nginx
stop_nginx() {
    log "Stopping nginx..."
    
    if is_service_running "nginx" 80; then
        sudo service nginx stop
        
        if wait_for_service_stop "nginx" 80 10; then
            success "nginx stopped successfully"
        else
            warn "nginx may still be running, attempting force stop..."
            sudo pkill -f nginx || true
            sleep 2
            
            if wait_for_service_stop "nginx" 80 5; then
                success "nginx stopped forcefully"
            else
                error "Failed to stop nginx completely"
            fi
        fi
    else
        log "nginx is not running"
    fi
}

# Function to stop PostgreSQL
stop_postgresql() {
    log "Stopping PostgreSQL..."
    
    if is_service_running "PostgreSQL" 5432; then
        sudo service postgresql stop
        
        if wait_for_service_stop "PostgreSQL" 5432 20; then
            success "PostgreSQL stopped successfully"
        else
            warn "PostgreSQL may still be running, attempting force stop..."
            sudo su - postgres -c "pg_ctl stop -D /var/lib/postgresql/*/main -m fast" 2>/dev/null || true
            sleep 3
            
            if wait_for_service_stop "PostgreSQL" 5432 10; then
                success "PostgreSQL stopped forcefully"
            else
                error "Failed to stop PostgreSQL completely"
            fi
        fi
    else
        log "PostgreSQL is not running"
    fi
}

# Function to clean up MCP server processes
stop_mcp_server() {
    log "Stopping MCP server processes..."
    
    # Find and stop any running MCP server processes
    local mcp_pids=$(ps aux | grep '[m]cp_server.py' | awk '{print $2}' || true)
    if [ -n "$mcp_pids" ]; then
        log "Found MCP server processes: $mcp_pids"
        kill -TERM $mcp_pids 2>/dev/null || true
        sleep 3
        
        # Check if still running
        mcp_pids=$(ps aux | grep '[m]cp_server.py' | awk '{print $2}' || true)
        if [ -n "$mcp_pids" ]; then
            log "Force killing MCP server processes: $mcp_pids"
            kill -KILL $mcp_pids 2>/dev/null || true
        fi
        success "MCP server processes stopped"
    else
        log "No MCP server processes found"
    fi
    
    # Also check for any processes on port 8000
    if is_service_running "MCP" 8000; then
        local port_pids=$(lsof -t -i:8000 2>/dev/null || true)
        if [ -n "$port_pids" ]; then
            log "Found processes on port 8000: $port_pids"
            kill -TERM $port_pids 2>/dev/null || true
            sleep 2
            kill -KILL $port_pids 2>/dev/null || true
        fi
    fi
}

# Function to clean up temporary files and markers
cleanup_temp_files() {
    log "Cleaning up temporary files..."
    
    # Remove initialization marker
    if [ -f "/tmp/.services-initialized" ]; then
        rm -f "/tmp/.services-initialized"
        log "Removed initialization marker"
    fi
    
    # Clean up any temporary log files
    if [ -d "/tmp/foglamp" ]; then
        rm -rf "/tmp/foglamp"
        log "Removed temporary FogLAMP files"
    fi
    
    # Clean up any PID files
    for pid_file in /tmp/foglamp*.pid /tmp/mcp*.pid; do
        if [ -f "$pid_file" ]; then
            rm -f "$pid_file"
            log "Removed PID file: $(basename $pid_file)"
        fi
    done
    
    success "Cleanup completed"
}

# Main shutdown function
main() {
    log "Starting FogLAMP MCP Development Environment Shutdown"
    log "=========================================================="
    
    # Display current service status before shutdown
    log "Current Service Status:"
    is_service_running "PostgreSQL" 5432 && log "  ✓ PostgreSQL (running)" || log "  ✗ PostgreSQL (stopped)"
    is_service_running "nginx" 80 && log "  ✓ nginx (running)" || log "  ✗ nginx (stopped)"
    is_service_running "FogLAMP" 8081 && log "  ✓ FogLAMP API (running)" || log "  ✗ FogLAMP API (stopped)"
    is_service_running "MCP" 8000 && log "  ✓ MCP Server (running)" || log "  ✗ MCP Server (stopped)"
    log ""
    
    # Stop services in reverse order of startup
    
    # Stop MCP server processes first
    stop_mcp_server
    
    # Stop FogLAMP (main application)
    stop_foglamp
    
    # Stop nginx (web server)
    stop_nginx
    
    # Stop PostgreSQL (database)
    stop_postgresql
    
    # Clean up temporary files
    cleanup_temp_files
    
    success "Service shutdown completed!"
    log "=========================================================="
    
    # Display final service status
    log "Final Service Status:"
    is_service_running "PostgreSQL" 5432 && error "  ✗ PostgreSQL still running" || success "  ✓ PostgreSQL stopped"
    is_service_running "nginx" 80 && error "  ✗ nginx still running" || success "  ✓ nginx stopped"
    is_service_running "FogLAMP" 8081 && error "  ✗ FogLAMP still running" || success "  ✓ FogLAMP stopped"
    is_service_running "MCP" 8000 && error "  ✗ MCP Server still running" || success "  ✓ MCP Server stopped"
    
    log ""
    log "All services have been stopped."
    log "To restart services, run: ./init-services.sh"
    log ""
}

# Handle script arguments
case "${1:-}" in
    --force)
        log "Force shutdown mode enabled"
        # Set shorter timeouts for force mode
        export FORCE_MODE=true
        main
        ;;
    --help|-h)
        echo "FogLAMP MCP Development Environment - Stop Services"
        echo ""
        echo "Usage: $0 [OPTION]"
        echo ""
        echo "Options:"
        echo "  --force    Force stop all services with shorter timeouts"
        echo "  --help     Show this help message"
        echo ""
        echo "This script stops all services started by init-services.sh:"
        echo "  - MCP Server processes"
        echo "  - FogLAMP application server"
        echo "  - nginx web server"
        echo "  - PostgreSQL database"
        echo ""
        exit 0
        ;;
    "")
        main
        ;;
    *)
        error "Unknown option: $1"
        echo "Use --help for usage information"
        exit 1
        ;;
esac

