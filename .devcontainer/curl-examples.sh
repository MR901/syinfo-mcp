#!/bin/bash

# FogLAMP API Curl Examples
# Working examples for common FogLAMP operations

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

FOGLAMP_URL="http://localhost:8081"

echo -e "${BLUE}FogLAMP API Examples${NC}"
echo "===================="
echo ""

# Check if FogLAMP is running
echo -e "${YELLOW}1. Health Check:${NC}"
echo "curl -s \"$FOGLAMP_URL/foglamp/ping\" | jq ."
echo ""

# List services
echo -e "${YELLOW}2. List Services:${NC}"
echo "curl -s \"$FOGLAMP_URL/foglamp/service\" | jq '.services[] | {name: .name, type: .type, enabled: .enabled}'"
echo ""

# Create Sinusoid South Service (with authentication if needed)
echo -e "${YELLOW}3a. Create Sinusoid Service (no auth):${NC}"
cat << 'EOF'
curl -X POST "$FOGLAMP_URL/foglamp/service" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Sinusoid_Pipeline_1", 
    "type": "south", 
    "plugin": "sinusoid",
    "enabled": true,
    "config": {
      "assetName": "SINUSOID_DATA",
      "readingsPerSec": "10",
      "amplitude": "100",
      "frequency": "1.0"
    }
  }'
EOF
echo ""

# Create service with authentication
echo -e "${YELLOW}3b. Create Service (with authentication):${NC}"
cat << 'EOF'
# Get token first
TOKEN=$(curl -s -X POST "$FOGLAMP_URL/foglamp/login" \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"foglamp"}' | jq -r '.token')

# Create service with token
curl -X POST "$FOGLAMP_URL/foglamp/service" \
  -H "Content-Type: application/json" \
  -H "authorization: $TOKEN" \
  -d '{
    "name": "Sinusoid_Pipeline_1", 
    "type": "south", 
    "plugin": "sinusoid",
    "enabled": true,
    "config": {
      "assetName": "SINUSOID_DATA",
      "readingsPerSec": "10"
    }
  }'
EOF
echo ""

# Check authentication status
echo -e "${YELLOW}4. Check Authentication Status:${NC}"
echo "curl -s \"$FOGLAMP_URL/foglamp/ping\" | jq .authenticationOptional"
echo ""

# Get readings
echo -e "${YELLOW}5. Get Latest Readings:${NC}"
echo "curl -s \"$FOGLAMP_URL/foglamp/asset\" | jq ."
echo ""

# Set authentication to optional
echo -e "${YELLOW}6. Fix Authentication (set to optional):${NC}"
cat << 'EOF'
# Login first
TOKEN=$(curl -s -X POST "$FOGLAMP_URL/foglamp/login" \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"foglamp"}' | jq -r '.token')

# Set authentication to optional
curl -X PUT "$FOGLAMP_URL/foglamp/category/rest_api" \
  -H "Content-Type: application/json" \
  -H "authorization: $TOKEN" \
  -d '{"authentication": "optional"}'

# Restart FogLAMP to apply changes
sudo pkill -f foglamp && sleep 5 && sudo /usr/local/foglamp/bin/foglamp start
EOF
echo ""

echo -e "${GREEN}Quick Fix Scripts:${NC}"
echo "- Run authentication fix: ./fix-auth.sh"
echo "- Stop all services: ./stop-services.sh"  
echo "- Initialize services: ./init-services.sh"
echo ""

# Interactive mode
if [ "${1}" == "--run" ]; then
    echo -e "${BLUE}Running examples interactively...${NC}"
    echo ""
    
    echo -e "${YELLOW}Testing FogLAMP connection...${NC}"
    if curl -s "$FOGLAMP_URL/foglamp/ping" >/dev/null 2>&1; then
        echo -e "${GREEN}✓ FogLAMP is running${NC}"
        
        # Check authentication status
        auth_optional=$(curl -s "$FOGLAMP_URL/foglamp/ping" 2>/dev/null | grep -o '"authenticationOptional":[^,}]*' | cut -d: -f2)
        if [[ "$auth_optional" == "true" ]]; then
            echo -e "${GREEN}✓ Authentication is optional${NC}"
        else
            echo -e "${YELLOW}⚠ Authentication is required - run ./fix-auth.sh to fix${NC}"
        fi
        
        # List current services
        echo ""
        echo -e "${YELLOW}Current services:${NC}"
        curl -s "$FOGLAMP_URL/foglamp/service" | jq -r '.services[] | "  - \(.name) (\(.type))"' 2>/dev/null || echo "  No services found or API error"
    else
        echo -e "${YELLOW}⚠ FogLAMP is not running on port 8081${NC}"
        echo "Start with: sudo /usr/local/foglamp/bin/foglamp start"
    fi
fi



