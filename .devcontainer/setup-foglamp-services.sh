#!/bin/bash

# FogLAMP Services Setup Script
# Creates Sinusoid and Randomwalk South services with anomaly injection filters

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

FOGLAMP_URL="http://localhost:8081"

log() {
    echo -e "${BLUE}[$(date '+%H:%M:%S')]${NC} $1"
}

success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

warn() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# Check if FogLAMP is running and authentication is optional
check_foglamp_status() {
    log "Checking FogLAMP status..."
    
    if ! curl -s "${FOGLAMP_URL}/foglamp/ping" >/dev/null 2>&1; then
        error "FogLAMP is not running on port 8081"
        error "Please start FogLAMP first: sudo /usr/local/foglamp/bin/foglamp start"
        exit 1
    fi
    
    local auth_optional=$(curl -s "${FOGLAMP_URL}/foglamp/ping" 2>/dev/null | jq -r '.authenticationOptional // false' 2>/dev/null || echo "false")
    if [[ "$auth_optional" != "true" ]]; then
        error "FogLAMP authentication is not optional"
        error "Run ./fix-auth.sh to fix authentication first"
        exit 1
    fi
    
    success "FogLAMP is running and authentication is optional"
}

# Create South services
create_south_services() {
    log "Creating South services..."
    
    # Create Sinusoid service with correct configuration
    log "Creating Sinusoid South service..."
    local sinusoid_response=$(curl -s -X POST "${FOGLAMP_URL}/foglamp/service" \
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
        success "Sinusoid service created/already exists"
    else
        error "Failed to create Sinusoid service"
        echo "Response: ${sinusoid_response%???}"
    fi
    
    # Create Randomwalk service with correct configuration
    log "Creating Randomwalk South service..."
    local randomwalk_response=$(curl -s -X POST "${FOGLAMP_URL}/foglamp/service" \
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
        success "Randomwalk service created/already exists"
    else
        error "Failed to create Randomwalk service"
        echo "Response: ${randomwalk_response%???}"
    fi
}

# Create anomaly injection filters
create_anomaly_filters() {
    log "Creating anomaly injection filters..."
    
    # Create Sinusoid anomaly filter
    log "Creating anomaly filter for Sinusoid..."
    local sinusoid_filter_response=$(curl -s -X POST "${FOGLAMP_URL}/foglamp/filter" \
        -H "Content-Type: application/json" \
        -d '{
            "name": "Anomaly_Injector_Sinusoid",
            "plugin": "anomaly-injection",
            "filter_config": {
                "enable": "true",
                "AnomalyType": "Spike",
                "Probability": "10",
                "Magnitude": "2",
                "DataPoint": "sinusoid"
            }
        }' -w "%{http_code}")
    
    if [[ "$sinusoid_filter_response" =~ (200|409)$ ]]; then
        success "Sinusoid anomaly filter created/already exists"
    else
        warn "Failed to create Sinusoid anomaly filter"
        echo "Response: ${sinusoid_filter_response%???}"
    fi
    
    # Create Randomwalk anomaly filter  
    log "Creating anomaly filter for Randomwalk..."
    local randomwalk_filter_response=$(curl -s -X POST "${FOGLAMP_URL}/foglamp/filter" \
        -H "Content-Type: application/json" \
        -d '{
            "name": "Anomaly_Injector_Randomwalk",
            "plugin": "anomaly-injection",
            "filter_config": {
                "enable": "true",
                "AnomalyType": "Spike", 
                "Probability": "10",
                "Magnitude": "2",
                "DataPoint": "randomwalk"
            }
        }' -w "%{http_code}")
    
    if [[ "$randomwalk_filter_response" =~ (200|409)$ ]]; then
        success "Randomwalk anomaly filter created/already exists"
    else
        warn "Failed to create Randomwalk anomaly filter"
        echo "Response: ${randomwalk_filter_response%???}"
    fi
}

# Attach filters to pipelines
attach_filters_to_pipelines() {
    log "Attaching filters to service pipelines..."
    
    # Wait for filters to be fully created
    sleep 2
    
    # Attach Sinusoid filter
    log "Attaching anomaly filter to Sinusoid pipeline..."
    local attach_sinusoid_response=$(curl -s -X PUT "${FOGLAMP_URL}/foglamp/filter/Sinusoid_Pipeline_1/pipeline?allow_duplicates=true&append_filter=true" \
        -H "Content-Type: application/json" \
        -d '{"pipeline": ["Anomaly_Injector_Sinusoid"]}' -w "%{http_code}")
    
    if [[ "$attach_sinusoid_response" =~ 200$ ]]; then
        success "Sinusoid anomaly filter attached to pipeline"
    else
        warn "Failed to attach Sinusoid filter to pipeline"
        echo "Response: ${attach_sinusoid_response%???}"
    fi
    
    # Attach Randomwalk filter
    log "Attaching anomaly filter to Randomwalk pipeline..."
    local attach_randomwalk_response=$(curl -s -X PUT "${FOGLAMP_URL}/foglamp/filter/Randomwalk_Pipeline_2/pipeline?allow_duplicates=true&append_filter=true" \
        -H "Content-Type: application/json" \
        -d '{"pipeline": ["Anomaly_Injector_Randomwalk"]}' -w "%{http_code}")
    
    if [[ "$attach_randomwalk_response" =~ 200$ ]]; then
        success "Randomwalk anomaly filter attached to pipeline"
    else
        warn "Failed to attach Randomwalk filter to pipeline"
        echo "Response: ${attach_randomwalk_response%???}"
    fi
}

# Display status
show_final_status() {
    log "Setup completed! Checking final status..."
    
    echo ""
    echo -e "${GREEN}=== FogLAMP Services Status ===${NC}"
    curl -s "${FOGLAMP_URL}/foglamp/service" | jq '.services[] | select(.type == "Southbound") | {name: .name, type: .type, status: .status}' 2>/dev/null || echo "Could not retrieve service status"
    
    echo ""
    echo -e "${GREEN}=== FogLAMP Health Check ===${NC}"
    local health_info=$(curl -s "${FOGLAMP_URL}/foglamp/ping" 2>/dev/null)
    if [ $? -eq 0 ]; then
        echo "$health_info" | jq '{health: .health, authenticationOptional: .authenticationOptional, dataRead: .dataRead, dataSent: .dataSent}' 2>/dev/null || echo "$health_info"
    else
        error "Could not retrieve FogLAMP health status"
    fi
    
    echo ""
    echo -e "${BLUE}=== Useful Commands ===${NC}"
    echo "• Check services: curl -s \"${FOGLAMP_URL}/foglamp/service\" | jq ."
    echo "• Check assets: curl -s \"${FOGLAMP_URL}/foglamp/asset\" | jq ."
    echo "• Check readings: curl -s \"${FOGLAMP_URL}/foglamp/reading\" | jq ."
    echo "• FogLAMP GUI: http://localhost:50080 (host) / http://localhost:80 (container)"
    echo "• Stop services: ./stop-services.sh"
    echo ""
}

# Main execution
main() {
    echo -e "${BLUE}FogLAMP Services Setup${NC}"
    echo "======================"
    echo ""
    
    check_foglamp_status
    create_south_services
    create_anomaly_filters
    attach_filters_to_pipelines
    show_final_status
    
    success "🎉 FogLAMP services setup completed successfully!"
}

# Handle command line arguments
case "${1:-}" in
    --help|-h)
        echo "FogLAMP Services Setup Script"
        echo ""
        echo "This script creates:"
        echo "  • Sinusoid_Pipeline_1 (South service)"
        echo "  • Randomwalk_Pipeline_2 (South service)" 
        echo "  • Anomaly injection filters for both services"
        echo ""
        echo "Prerequisites:"
        echo "  • FogLAMP must be running on port 8081"
        echo "  • Authentication must be set to optional (run ./fix-auth.sh if needed)"
        echo ""
        echo "Usage: $0 [--help]"
        echo ""
        exit 0
        ;;
    *)
        main
        ;;
esac
