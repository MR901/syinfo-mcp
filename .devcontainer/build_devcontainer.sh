#!/bin/bash

# DevContainer Build Script
# Builds the custom FogLAMP MCP development image

set -e

# Color output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

log() {
    echo -e "${BLUE}[BUILD]${NC} $1"
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

# Configuration
IMAGE_NAME="foglamp-mcp-devcontainer"
IMAGE_TAG="latest"
FULL_IMAGE_NAME="${IMAGE_NAME}:${IMAGE_TAG}"

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

log "Building FogLAMP MCP DevContainer"
log "================================="
log "Image: $FULL_IMAGE_NAME"
log "Context: $PROJECT_ROOT"
log "Dockerfile: $SCRIPT_DIR/Dockerfile.devcontainer"
log ""

# Check if Docker is available
if ! command -v docker >/dev/null 2>&1; then
    error "Docker is not installed or not available in PATH"
    exit 1
fi

# Check if Dockerfile exists
if [ ! -f "$SCRIPT_DIR/Dockerfile.devcontainer" ]; then
    error "Dockerfile not found: $SCRIPT_DIR/Dockerfile.devcontainer"
    exit 1
fi

# Change to project root for build context
cd "$PROJECT_ROOT"

# Build the image
log "Building Docker image..."
if docker build \
    -f ".devcontainer/Dockerfile.devcontainer" \
    -t "$FULL_IMAGE_NAME" \
    --progress=plain \
    . ; then
    success "Docker image built successfully: $FULL_IMAGE_NAME"
else
    error "Docker build failed"
    exit 1
fi

# Show image info
log ""
log "Image Information:"
docker images "$FULL_IMAGE_NAME" --format "table {{.Repository}}\t{{.Tag}}\t{{.Size}}\t{{.CreatedAt}}"

log ""
success "Build completed successfully!"
log "You can now rebuild your devcontainer in VS Code/Cursor:"
log "1. Press F1"
log "2. Select 'Dev Containers: Rebuild Container'"
log "3. Or run: docker run -it --rm $FULL_IMAGE_NAME bash"

# Cleanup dangling images if requested
if [ "${1:-}" = "--cleanup" ]; then
    log ""
    log "Cleaning up dangling images..."
    docker image prune -f || warn "Failed to cleanup dangling images"
fi