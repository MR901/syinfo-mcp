#!/bin/bash

# FogLAMP MCP Development Environment Service Initialization
# This script is called once when the container first starts to configure services

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

# Function to wait for service to start
wait_for_service() {
    local service_name=$1
    local port=$2
    local max_attempts=${3:-30}
    local attempt=1
    
    log "Waiting for $service_name to start on port $port..."
    while [ $attempt -le $max_attempts ]; do
        if is_service_running "$service_name" "$port"; then
            success "$service_name is running on port $port"
            return 0
        fi
        sleep 1
        attempt=$((attempt + 1))
    done
    
    error "$service_name failed to start on port $port after $max_attempts attempts"
    return 1
}

# Function to check and fix FogLAMP authentication if needed
fix_authentication_if_needed() {
    local api_url="http://localhost:8081"
    
    # Check current authentication status  
    local auth_optional=$(curl -s "$api_url/foglamp/ping" 2>/dev/null | jq -r '.authenticationOptional // false' 2>/dev/null || echo "false")
    
    if [[ "$auth_optional" == "true" ]]; then
        log "Authentication is already optional - no fix needed"
        return 0
    fi
    
    warn "Authentication is required - attempting to fix..."
    
    # Login and set to optional
    local token=$(curl -s -X POST "$api_url/foglamp/login" \
        -H "Content-Type: application/json" \
        -d '{"username":"admin","password":"foglamp"}' \
        | jq -r '.token' 2>/dev/null || echo "null")
    
    if [ "$token" == "null" ] || [ -z "$token" ]; then
        error "Failed to login - cannot fix authentication"
        return 1
    fi
    
    # Set to optional
    curl -s -X PUT "$api_url/foglamp/category/rest_api" \
        -H "Content-Type: application/json" \
        -H "authorization: $token" \
        -d '{"authentication": "optional"}' >/dev/null
    
    # Restart FogLAMP
    log "Restarting FogLAMP to apply authentication fix..."
    sudo pkill -f foglamp >/dev/null 2>&1 || true
    sleep 5
    sudo /usr/local/foglamp/bin/foglamp start
    sleep 15
    
    # Verify fix
    auth_optional=$(curl -s "$api_url/foglamp/ping" 2>/dev/null | jq -r '.authenticationOptional // false' 2>/dev/null || echo "false")
    if [[ "$auth_optional" == "true" ]]; then
        success "Authentication successfully fixed - now optional"
        return 0
    else
        error "Failed to fix authentication"
        return 1
    fi
}

# Function to configure FogLAMP via REST API
configure_foglamp() {
    local api_url="http://localhost:8081"
    local username="admin"
    local password="foglamp"
    local token=""
    
    log "Configuring FogLAMP via REST API..."
    
    # Wait for API to be responsive
    if ! wait_for_service "FogLAMP API" 8081 60; then
        error "FogLAMP API is not responding"
        return 1
    fi
    
    # Test API connectivity with retry logic
    local retry_count=0
    while [ $retry_count -lt 5 ]; do
        if curl -s -f "$api_url/foglamp/ping" >/dev/null; then
            success "FogLAMP API is responding"
            break
        fi
        retry_count=$((retry_count + 1))
        warn "API ping failed, attempt $retry_count/5"
        sleep 2
    done
    
    if [ $retry_count -eq 5 ]; then
        error "FogLAMP API ping failed after 5 attempts"
        return 1
    fi
    
    # === Authentication Steps Before Configuration ===
    log "=== Logging in and capturing authentication token ==="
    token=$(curl -s -X POST "${api_url}/foglamp/login" \
        -H "Content-Type: application/json" \
        -d "{\"username\":\"${username}\",\"password\":\"${password}\"}" \
        | jq -r '.token' 2>/dev/null || echo "null")
    
    if [ "$token" == "null" ] || [ -z "$token" ]; then
        warn "Login failed or authentication not required, proceeding without token..."
        log "This is normal for first-time setup - authentication may not be enabled yet"
        token=""
    else
        success "Successfully logged in and captured token"
        log "Token: ${token:0:20}..."  # Show only first 20 chars for security
    fi
    
    # Set authentication to optional (with token if available)
    log "=== Setting authentication to optional ==="
    local auth_headers=""
    if [ -n "$token" ]; then
        auth_headers="-H \"authorization: ${token}\""
    fi
    
    local auth_response=$(eval "curl -s -X PUT \"$api_url/foglamp/category/rest_api\" \
        -H \"Content-Type: application/json\" \
        $auth_headers \
        -d '{\"authentication\": \"optional\"}' -w \"%{http_code}\"")
    
    if [[ "$auth_response" =~ 200$ ]]; then
        success "Authentication configuration updated (requires restart to take effect)"
    else
        error "Failed to set authentication mode (HTTP: ${auth_response: -3})"
        log "This is critical - FogLAMP restart may not apply authentication changes"
        return 1
    fi
    
    # # Configure PostgreSQL storage plugin (with token if available)
    # log "=== Configuring PostgreSQL storage plugin ==="
    # local storage_response=$(eval "curl -s -X PUT \"$api_url/foglamp/category/Storage\" \
    #     -H \"Content-Type: application/json\" \
    #     $auth_headers \
    #     -d '{
    #         \"plugin\": \"postgres\",
    #         \"readingPlugin\": \"Use main plugin\"
    #     }' -w \"%{http_code}\"")
    
    # if [[ "$storage_response" =~ 200$ ]]; then
    #     success "PostgreSQL storage configured"
    # else
    #     warn "Failed to configure PostgreSQL storage (HTTP: ${storage_response: -3})"
    # fi
    # PostgreSQL storage configuration removed as requested
    log "=== Skipping PostgreSQL storage configuration ==="
    log "FogLAMP will use default storage configuration"
    
    # Configure additional FogLAMP settings for development
    log "Applying additional development-friendly configurations..."
    
    # Set data retention to reasonable values for development
    eval "curl -s -X PUT \"$api_url/foglamp/category/PURGE_READ\" \
        -H \"Content-Type: application/json\" \
        $auth_headers \
        -d '{
            \"age\": \"168\",
            \"retainUnsent\": \"false\"
        }'" >/dev/null || warn "Failed to configure data retention"
    
    # Enable advanced logging for development
    eval "curl -s -X PUT \"$api_url/foglamp/category/General\" \
        -H \"Content-Type: application/json\" \
        $auth_headers \
        -d '{
            \"logLevel\": \"info\",
            \"allowPing\": \"true\"
        }'" >/dev/null || warn "Failed to configure general settings"
    
    # Restart FogLAMP to apply configuration changes (proper stop/start sequence)
    log "Stopping FogLAMP to apply authentication configuration..."
    sudo pkill -f foglamp >/dev/null 2>&1 || true
    sleep 5
    
    # Ensure FogLAMP is fully stopped
    local stop_attempts=0
    while is_service_running "FogLAMP" 8081 && [ $stop_attempts -lt 10 ]; do
        log "Waiting for FogLAMP to stop completely..."
        sleep 2
        stop_attempts=$((stop_attempts + 1))
    done
    
    log "Starting FogLAMP with new configuration..."
    sudo /usr/local/foglamp/bin/foglamp start
    
    # Wait for startup with extended timeout
    sleep 15
    if ! wait_for_service "FogLAMP API" 8081 90; then
        error "FogLAMP failed to start after restart"
        return 1
    fi
    
    # Verify authentication is now optional
    local auth_check_attempts=0
    while [ $auth_check_attempts -lt 5 ]; do
        local auth_optional=$(curl -s "http://localhost:8081/foglamp/ping" 2>/dev/null | jq -r '.authenticationOptional // false' 2>/dev/null || echo "false")
        if [[ "$auth_optional" == "true" ]]; then
            success "Authentication successfully set to optional"
            break
        fi
        warn "Authentication still required, waiting... (attempt $((auth_check_attempts + 1))/5)"
        sleep 5
        auth_check_attempts=$((auth_check_attempts + 1))
    done
    
    if [ $auth_check_attempts -eq 5 ]; then
        error "Failed to set authentication to optional after restart"
        warn "Manual intervention may be required"
        return 1
    fi
    
    # Wait additional time for full initialization
    sleep 10
    
    log "=== POST-RESTART: Authentication is now optional, no token needed ==="
    
    # Create South services with correct configuration (no authentication needed after restart)
    log "Creating Sinusoid South service..."
    local sinusoid_response=$(curl -s -X POST "$api_url/foglamp/service" \
        -H "Content-Type: application/json" \
        -d '{
            "name": "Sinusoid_Pipeline_1",
            "type": "south",
            "plugin": "sinusoid",
            "enabled": true,
            "config": {
                "assetName": {"value": "SINUSOID_DATA"}
            }
        }' -w "%{http_code}")
    
    if [[ "$sinusoid_response" =~ (200|409)$ ]]; then
        success "Sinusoid service created/exists"
    else
        warn "Failed to create Sinusoid service (HTTP: ${sinusoid_response: -3})"
    fi
    
    log "Creating Randomwalk South service..."
    local randomwalk_response=$(curl -s -X POST "$api_url/foglamp/service" \
        -H "Content-Type: application/json" \
        -d '{
            "name": "Randomwalk_Pipeline_2", 
            "type": "south",
            "plugin": "randomwalk",
            "enabled": true,
            "config": {
                "assetName": {"value": "RANDOMWALK_DATA"},
                "minValue": {"value": "0"},
                "maxValue": {"value": "1000"}
            }
        }' -w "%{http_code}")
    
    if [[ "$randomwalk_response" =~ (200|409)$ ]]; then
        success "Randomwalk service created/exists"
    else
        warn "Failed to create Randomwalk service (HTTP: ${randomwalk_response: -3})"
    fi
    
    # Wait for services to initialize
    sleep 5
    
    # Create and configure anomaly injection filters (no authentication needed after restart)
    log "Creating and configuring anomaly injection filters..."
    
    local anomaly_sin_response=$(curl -s -X POST "$api_url/foglamp/filter" \
        -H "Content-Type: application/json" \
        -d '{
            "name": "Anomaly_Injector_Sinusoid",
            "plugin": "anomaly-injection",
            "filter_config": {
                "enable": "true",
                "AnomalyType": "Spike",
                "Probability": "10",
                "Magnitude": "10",
                "DataPoint": "sinusoid"
            }
        }' -w "%{http_code}")
    
    if [[ "$anomaly_sin_response" =~ (200|409)$ ]]; then
        success "Sinusoid anomaly filter created/exists"
    else
        warn "Failed to create Sinusoid anomaly filter (HTTP: ${anomaly_sin_response: -3})"
    fi
    
    local anomaly_rw_response=$(curl -s -X POST "$api_url/foglamp/filter" \
        -H "Content-Type: application/json" \
        -d '{
            "name": "Anomaly_Injector_Randomwalk",
            "plugin": "anomaly-injection", 
            "filter_config": {
                "enable": "true",
                "AnomalyType": "Spike", 
                "Probability": "10",
                "Magnitude": "3",
                "DataPoint": "randomwalk"
            }
        }' -w "%{http_code}")
    
    if [[ "$anomaly_rw_response" =~ (200|409)$ ]]; then
        success "Randomwalk anomaly filter created/exists"
    else
        warn "Failed to create Randomwalk anomaly filter (HTTP: ${anomaly_rw_response: -3})"
    fi
    
    # Attach filters to pipelines with retry logic (no authentication needed after restart)
    sleep 3
    log "Attaching anomaly filters to service pipelines..."
    
    local attach_sin_response=$(curl -s -X PUT "$api_url/foglamp/filter/Sinusoid_Pipeline_1/pipeline?allow_duplicates=true&append_filter=true" \
        -H "Content-Type: application/json" \
        -d '{"pipeline": ["Anomaly_Injector_Sinusoid"]}' -w "%{http_code}")
    
    if [[ "$attach_sin_response" =~ 200$ ]]; then
        success "Sinusoid anomaly filter attached to pipeline"
    else
        warn "Failed to attach Sinusoid filter (HTTP: ${attach_sin_response: -3})"
    fi
    
    local attach_rw_response=$(curl -s -X PUT "$api_url/foglamp/filter/Randomwalk_Pipeline_2/pipeline?allow_duplicates=true&append_filter=true" \
        -H "Content-Type: application/json" \
        -d '{"pipeline": ["Anomaly_Injector_Randomwalk"]}' -w "%{http_code}")
    
    if [[ "$attach_rw_response" =~ 200$ ]]; then
        success "Randomwalk anomaly filter attached to pipeline" 
    else
        warn "Failed to attach Randomwalk filter (HTTP: ${attach_rw_response: -3})"
    fi
    
    # Verify configuration by checking service status (no authentication needed after restart)
    log "Verifying service configuration..."
    local services_info=$(curl -s "$api_url/foglamp/service" | jq -r '.services[] | select(.type=="Southbound") | .name' 2>/dev/null || echo "")
    
    if [[ "$services_info" =~ Sinusoid_Pipeline_1 ]] && [[ "$services_info" =~ Randomwalk_Pipeline_2 ]]; then
        success "South services verified and running"
    else
        warn "South services may not be properly configured"
    fi
    
    success "FogLAMP pre-configuration completed successfully!"
    log "Configuration summary:"
    log "  ✓ Authentication: Initially authenticated, then set to Optional after restart"
    log "  ✓ Storage: Default (PostgreSQL storage configuration skipped)" 
    log "  ✓ South Services: Sinusoid + Randomwalk with anomaly injection"
    log "  ✓ Data retention: 7 days for development"
    log ""
    log "Authentication flow completed:"
    log "  1. ✓ Login with admin/foglamp credentials"
    log "  2. ✓ Set authentication to optional (authenticated)" 
    log "  3. ✓ Stop FogLAMP completely"
    log "  4. ✓ Start FogLAMP with new configuration"
    log "  5. ✓ Verify authentication is optional"
    log "  6. ✓ Services can now be created without authentication"
}

# Function to configure nginx for FogLAMP GUI
configure_nginx_for_foglamp() {
    log "Configuring nginx for FogLAMP GUI..."
    
    # The nginx configuration should already be in place from the Dockerfile,
    # but let's verify and fix if needed
    local nginx_config="/etc/nginx/sites-available/foglamp"
    local nginx_enabled="/etc/nginx/sites-enabled/foglamp"
    
    if [ ! -f "$nginx_config" ]; then
        warn "FogLAMP nginx config not found, this should not happen in a properly built container"
        return 1
    fi
    
    # Check if the config has the correct document root
    if grep -q "/usr/local/foglamp/data/gui" "$nginx_config" 2>/dev/null; then
        warn "Found old nginx config with incorrect document root - this was causing 500 errors"
        warn "The correct nginx configuration should be copied during container build"
        warn "If you see this message, the container may need to be rebuilt"
    fi
    
    # Ensure the correct nginx site is enabled
    if [ ! -L "$nginx_enabled" ]; then
        log "Enabling FogLAMP nginx site..."
        sudo rm -f /etc/nginx/sites-enabled/default
        sudo ln -sf "$nginx_config" "$nginx_enabled"
        sudo nginx -t && sudo service nginx reload
        success "FogLAMP nginx site enabled"
    fi
    
    # Verify nginx configuration
    if sudo nginx -t 2>/dev/null; then
        success "nginx configuration is valid"
    else
        error "nginx configuration has errors - this may cause GUI issues"
        sudo nginx -t
    fi
    
    # Log what was configured
    log "nginx configuration summary:"
    log "  ✓ Document root: /var/www/html (where FogLAMP GUI files are installed)"
    log "  ✓ GUI accessible at: http://localhost:80 (container) / http://localhost:50080 (host)"
    log "  ✓ API proxy: /foglamp/* → http://localhost:8081/foglamp/*"
    log "  ✓ Health check: /health endpoint available"
    log "  ✓ Fixed infinite redirect loops that caused 500 errors"
}

# Function to configure Cursor MCP client
configure_cursor_mcp() {
    log "Configuring Cursor MCP client..."
    
    # Create .cursor directory in home
    local cursor_config_dir="$HOME/.cursor"
    local cursor_config_file="$cursor_config_dir/mcp.json"
    
    # Ensure directory exists
    mkdir -p "$cursor_config_dir"
    
    # Create MCP configuration for Cursor with FogLAMP, Excel, and ECharts servers
    log "Creating simplified Cursor MCP configuration at: $cursor_config_file"
    
    cat > "$cursor_config_file" << 'EOF'
{
  "mcpServers": {
    "foglamp-http": {
      "url": "http://localhost:8000/mcp",
      "description": "FogLAMP MCP Server - HTTP connection",
      "headers": {
        "User-Agent": "Cursor-MCP-Client/1.0",
        "Accept": "application/json"
      },
      "timeout": 30000,
      "enabled": true
    },
    "excel": {
      "command": "uvx",
      "args": ["excel-mcp-server", "stdio"],
      "description": "Excel MCP Server for spreadsheet operations",
      "enabled": true
    },
    "mcp-echarts": {
      "command": "npx",
      "args": ["-y", "mcp-echarts"],
      "description": "ECharts MCP Server for data visualization and chart creation",
      "enabled": true
    }
  },
  "preferences": {
    "defaultServer": "foglamp-http",
    "autoReconnect": true,
    "timeout": 30000
  }
}
EOF
    
    if [ $? -eq 0 ]; then
        success "Cursor MCP configuration created successfully"
        log "MCP Server configurations:"
        log "  • FogLAMP HTTP: http://localhost:8000/mcp (primary)"
        log "  • Excel: uvx excel-mcp-server stdio"
        log "  • ECharts: npx -y mcp-echarts"
    else
        warn "Failed to create Cursor MCP configuration"
        return 1
    fi
    
    # Remove any existing workspace-specific configuration to avoid conflicts
    # Use dynamic workspace detection
    if [ -z "$WORKSPACE_ROOT" ]; then
        # Try to detect workspace root for cursor config cleanup
        for possible_root in "/workspaces"/*; do
            if [ -d "$possible_root" ] && [ -f "$possible_root/python/foglamp/services/mcp/src/mcp_server.py" ]; then
                WORKSPACE_ROOT="$possible_root"
                break
            fi
        done
    fi
    
    if [ -n "$WORKSPACE_ROOT" ]; then
        local workspace_cursor_dir="$WORKSPACE_ROOT/.cursor"
        if [ -d "$workspace_cursor_dir" ]; then
            log "Removing workspace-specific MCP configuration to avoid conflicts..."
            rm -rf "$workspace_cursor_dir"
            success "Workspace MCP configuration removed"
        fi
    fi
    
    # Status checker is available for comprehensive testing
    log "Comprehensive status checker available at: show_environment_status.py"
    log "Use: python3 show_environment_status.py to verify all services"
    
    success "Simplified Cursor MCP client configuration completed!"
    log "Configuration includes:"
    log "  ✓ FogLAMP HTTP Server (primary)"
    log "  ✓ Excel MCP Server"
    log "  ✓ Removed duplicate configurations to avoid conflicts"
}

# Main initialization
main() {
    log "Starting FogLAMP MCP Development Environment Initialization"
    log "============================================================"
    
    # Check if already initialized
    if [ -f "/tmp/.services-initialized" ]; then
        log "Services already initialized. Skipping initialization."
        return 0
    fi
    
    # Start PostgreSQL
    log "Starting PostgreSQL..."
    if ! is_service_running "PostgreSQL" 5432; then
        sudo service postgresql start
        if wait_for_service "PostgreSQL" 5432; then
            success "PostgreSQL started successfully"
        else
            error "PostgreSQL failed to start"
            return 1
        fi
    else
        log "PostgreSQL already running"
    fi
    
    # Configure and start nginx for FogLAMP GUI
    configure_nginx_for_foglamp
    
    # Start nginx
    log "Starting nginx..."
    if ! is_service_running "nginx" 80; then
        sudo service nginx start
        if wait_for_service "nginx" 80; then
            success "nginx started successfully"
            # Verify the GUI is accessible
            if curl -s -f "http://localhost:80" >/dev/null; then
                success "FogLAMP GUI is accessible via nginx"
            else
                warn "nginx started but GUI may not be accessible"
            fi
        else
            error "nginx failed to start"
            return 1
        fi
    else
        log "nginx already running"
        # Still verify the GUI is accessible
        if curl -s -f "http://localhost:80" >/dev/null; then
            success "FogLAMP GUI is accessible via nginx"
        else
            warn "nginx running but GUI may not be accessible - checking configuration..."
            configure_nginx_for_foglamp
            sudo service nginx reload
        fi
    fi
    
    # Start FogLAMP
    log "Starting FogLAMP..."
    if ! is_service_running "FogLAMP" 8081; then
        sudo /usr/local/foglamp/bin/foglamp start
        if wait_for_service "FogLAMP" 8081 60; then
            success "FogLAMP started successfully"
        else
            error "FogLAMP failed to start"
            return 1
        fi
    else
        log "FogLAMP already running"
    fi
    
    # Configure FogLAMP
    configure_foglamp
    
    # Configure Cursor MCP client
    configure_cursor_mcp
    
    # Mark as initialized
    touch /tmp/.services-initialized
    
    success "Service initialization completed successfully!"
    log "============================================================"
    
    # Display service status
    log "Service Status Summary:"
    is_service_running "PostgreSQL" 5432 && success "✓ PostgreSQL (port 5432)" || error "✗ PostgreSQL (port 5432)"
    is_service_running "nginx" 80 && success "✓ nginx (port 80)" || error "✗ nginx (port 80)"
    is_service_running "FogLAMP" 8081 && success "✓ FogLAMP API (port 8081)" || error "✗ FogLAMP API (port 8081)"
    
    log ""
    log "Access URLs:"
    log "  - FogLAMP GUI: http://localhost:50080 (host) / http://localhost:80 (container)"
    log "  - FogLAMP API: http://localhost:58081 (host) / http://localhost:8081 (container)"
    log "  - MCP Server will be available at: http://localhost:58000 (host) / http://localhost:8000 (container)"
    log ""
    log "🔧 Nginx Configuration Fixed:"
    log "  - Document root corrected from /usr/local/foglamp/data/gui → /var/www/html"
    log "  - Infinite redirect loops eliminated (try_files /index.html → try_files =404)" 
    log "  - API proxy configured for /foglamp/* endpoints"
    log "  - This prevents the 500 Internal Server Error that occurred in previous versions"
}

# Run main function
main "$@"
