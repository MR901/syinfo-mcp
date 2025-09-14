#!/bin/bash
# Common Workspace Detection Functions
# This file provides portable workspace detection for all devcontainer scripts
# Usage: source .devcontainer/common_workspace.sh

# Color output functions
if [ -z "$_COLORS_DEFINED" ]; then
    export _COLORS_DEFINED=1
    export GREEN='\033[0;32m'
    export BLUE='\033[0;34m'
    export YELLOW='\033[1;33m'
    export RED='\033[0;31m'
    export CYAN='\033[0;36m'
    export NC='\033[0m'
fi

# Common logging functions
log() {
    echo -e "${BLUE}[WORKSPACE]${NC} $1"
}

warn() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1" >&2
}

success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

# Function to detect workspace root dynamically
detect_workspace_root() {
    local workspace_root=""
    local quiet="${1:-false}"
    
    # Method 1: Use environment variable (preferred in devcontainer)
    if [ -n "$WORKSPACE_ROOT" ] && [ -d "$WORKSPACE_ROOT" ]; then
        workspace_root="$WORKSPACE_ROOT"
        [ "$quiet" != "true" ] && log "Workspace root from WORKSPACE_ROOT env var: $workspace_root" >&2
    
    # Method 2: Use current directory if it contains the project structure
    elif [ -f "python/foglamp/services/mcp/src/mcp_server.py" ]; then
        workspace_root="$(pwd)"
        [ "$quiet" != "true" ] && log "Workspace root detected from current directory: $workspace_root" >&2
    
    # Method 3: Search up the directory tree
    else
        local current_dir="$(pwd)"
        local search_dir="$current_dir"
        
        # Go up directories looking for project markers
        while [ "$search_dir" != "/" ]; do
            if [ -f "$search_dir/python/foglamp/services/mcp/src/mcp_server.py" ]; then
                workspace_root="$search_dir"
                [ "$quiet" != "true" ] && log "Workspace root found by searching up: $workspace_root" >&2
                break
            fi
            search_dir="$(dirname "$search_dir")"
        done
        
        # Method 4: Try common devcontainer locations
        if [ -z "$workspace_root" ]; then
            for possible_root in "/workspaces"/*; do
                if [ -d "$possible_root" ] && [ -f "$possible_root/python/foglamp/services/mcp/src/mcp_server.py" ]; then
                    workspace_root="$possible_root"
                    [ "$quiet" != "true" ] && log "Workspace root found in /workspaces: $workspace_root" >&2
                    break
                fi
            done
        fi
    fi
    
    # Validate the detected workspace
    if [ -n "$workspace_root" ] && [ -f "$workspace_root/python/foglamp/services/mcp/src/mcp_server.py" ]; then
        echo "$workspace_root"
        return 0
    else
        error "Could not detect workspace root. Please ensure you're in the FogLAMP MCP project directory." >&2
        error "Looking for: python/foglamp/services/mcp/src/mcp_server.py" >&2
        return 1
    fi
}

# Function to set up workspace environment
setup_workspace_env() {
    local quiet="${1:-false}"
    local workspace_root
    workspace_root=$(detect_workspace_root true)
    
    if [ $? -ne 0 ]; then
        return 1
    fi
    
    # Export workspace variables
    export WORKSPACE_ROOT="$workspace_root"
    export WORKSPACE_NAME="$(basename "$workspace_root")"
    export MCP_SCRIPT="$workspace_root/python/foglamp/services/mcp/src/mcp_server.py"
    
    # Set Python path
    export PYTHONPATH="${PYTHONPATH:+$PYTHONPATH:}$workspace_root/python"
    
    if [ "$quiet" != "true" ]; then
        success "Workspace environment configured:" >&2
        log "  WORKSPACE_ROOT: $WORKSPACE_ROOT" >&2
        log "  WORKSPACE_NAME: $WORKSPACE_NAME" >&2
        log "  MCP_SCRIPT: $MCP_SCRIPT" >&2
    fi
    
    return 0
}

# Function to validate workspace structure
validate_workspace() {
    local workspace_root="${1:-$WORKSPACE_ROOT}"
    
    if [ -z "$workspace_root" ]; then
        error "No workspace root specified"
        return 1
    fi
    
    local required_files=(
        "python/foglamp/services/mcp/src/mcp_server.py"
        "requirements.txt"
        ".devcontainer/devcontainer.json"
    )
    
    local missing_files=()
    
    for file in "${required_files[@]}"; do
        if [ ! -f "$workspace_root/$file" ]; then
            missing_files+=("$file")
        fi
    done
    
    if [ ${#missing_files[@]} -gt 0 ]; then
        error "Workspace validation failed. Missing files:"
        for file in "${missing_files[@]}"; do
            error "  - $file"
        done
        return 1
    fi
    
    success "Workspace structure validated successfully"
    return 0
}

# Auto-setup when sourced (unless NO_AUTO_SETUP is set)
if [ -z "$NO_AUTO_SETUP" ] && [ -z "$WORKSPACE_ROOT" ]; then
    setup_workspace_env true >/dev/null 2>&1
fi
