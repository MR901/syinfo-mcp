#!/bin/bash

# FogLAMP Authentication Fix Script
# This script fixes the "401 Unauthorized" issue by setting authentication to optional

set -e

# Color output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

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

# Main fix function
fix_foglamp_authentication() {
    local api_url="http://localhost:8081"
    
    log "FogLAMP Authentication Fix Utility"
    log "=================================="
    
    # Check if FogLAMP is running
    if ! curl -s "$api_url/foglamp/ping" >/dev/null 2>&1; then
        error "FogLAMP is not running on port 8081"
        error "Please start FogLAMP first: sudo /usr/local/foglamp/bin/foglamp start"
        exit 1
    fi
    
    # Check current authentication status
    log "Checking current authentication status..."
    local auth_optional=$(curl -s "$api_url/foglamp/ping" 2>/dev/null | jq -r '.authenticationOptional // false' 2>/dev/null || echo "false")
    
    if [[ "$auth_optional" == "true" ]]; then
        success "Authentication is already optional - no fix needed!"
        log "You can now use FogLAMP API without authentication headers"
        log ""
        log "Example curl command:"
        log "curl -X POST \"$api_url/foglamp/service\" \\"
        log "  -H \"Content-Type: application/json\" \\"
        log "  -d '{\"name\": \"Test_Service\", \"type\": \"south\", \"plugin\": \"sinusoid\"}'"
        exit 0
    fi
    
    log "Authentication is currently required - applying fix..."
    
    # Login to get token
    log "Logging in as admin..."
    local token=$(curl -s -X POST "$api_url/foglamp/login" \
        -H "Content-Type: application/json" \
        -d '{"username":"admin","password":"foglamp"}' \
        | jq -r '.token' 2>/dev/null || echo "null")
    
    if [ "$token" == "null" ] || [ -z "$token" ]; then
        error "Failed to login with admin/foglamp credentials"
        error "Please check if FogLAMP is properly configured"
        exit 1
    fi
    
    success "Successfully logged in"
    
    # Set authentication to optional
    log "Setting authentication to optional..."
    local auth_response=$(curl -s -X PUT "$api_url/foglamp/category/rest_api" \
        -H "Content-Type: application/json" \
        -H "authorization: $token" \
        -d '{"authentication": "optional"}' -w "%{http_code}")
    
    if [[ "$auth_response" =~ 200$ ]]; then
        success "Authentication configuration updated"
    else
        error "Failed to update authentication configuration (HTTP: ${auth_response: -3})"
        exit 1
    fi
    
    # Restart FogLAMP to apply changes
    log "Restarting FogLAMP to apply authentication changes..."
    log "This may take up to 30 seconds..."
    
    # Stop FogLAMP
    sudo pkill -f foglamp >/dev/null 2>&1 || true
    sleep 5
    
    # Wait for complete shutdown
    local stop_attempts=0
    while curl -s "$api_url/foglamp/ping" >/dev/null 2>&1 && [ $stop_attempts -lt 10 ]; do
        log "Waiting for FogLAMP to stop..."
        sleep 2
        stop_attempts=$((stop_attempts + 1))
    done
    
    # Start FogLAMP
    sudo /usr/local/foglamp/bin/foglamp start
    sleep 15
    
    # Wait for startup
    local start_attempts=0
    while ! curl -s "$api_url/foglamp/ping" >/dev/null 2>&1 && [ $start_attempts -lt 20 ]; do
        log "Waiting for FogLAMP to start..."
        sleep 3
        start_attempts=$((start_attempts + 1))
    done
    
    if [ $start_attempts -eq 20 ]; then
        error "FogLAMP failed to start after restart"
        exit 1
    fi
    
    # Verify the fix
    log "Verifying authentication fix..."
    sleep 5
    auth_optional=$(curl -s "$api_url/foglamp/ping" 2>/dev/null | jq -r '.authenticationOptional // false' 2>/dev/null || echo "false")
    
    if [[ "$auth_optional" == "true" ]]; then
        success "✅ Authentication fix applied successfully!"
        log ""
        log "🎉 FogLAMP authentication is now OPTIONAL"
        log ""
        log "You can now use FogLAMP API without authentication headers:"
        log ""
        log "curl -X POST \"$api_url/foglamp/service\" \\"
        log "  -H \"Content-Type: application/json\" \\"
        log "  -d '{"
        log "    \"name\": \"Sinusoid_Pipeline_1\","
        log "    \"type\": \"south\","
        log "    \"plugin\": \"sinusoid\","
        log "    \"enabled\": true,"
        log "    \"config\": {"
        log "      \"assetName\": \"SINUSOID_DATA\","
        log "      \"readingsPerSec\": \"10\""
        log "    }"
        log "  }'"
        log ""
        log "The 401 Unauthorized error should now be resolved!"
    else
        error "❌ Authentication fix failed"
        error "Manual intervention may be required"
        exit 1
    fi
}

# Run the fix
fix_foglamp_authentication
