#!/usr/bin/env python3
"""
System Information MCP Server Example

This example shows how to use the syinfo-based tools in an MCP server.
It demonstrates system information gathering, network scanning, performance monitoring,
and system health checking capabilities.

Run with: python examples/syinfo_example.py
"""

import sys
import os

# Add project root to path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, project_root)

from src.template_server import TemplateMCPServer, ServerCapabilities


def register_syinfo_capabilities(mcp_server, http_client, config):
    """Register syinfo-specific capabilities for system monitoring."""
    
    # Import and register syinfo tools
    from src.tools.syinfo_tools import register_tools
    register_tools(mcp_server, http_client, config)
    
    # Add additional system monitoring resources
    @mcp_server.resource("resource://system/overview")
    def get_system_overview() -> str:
        """Get a comprehensive system overview combining multiple metrics."""
        
        overview = "# System Overview Dashboard\n\n"
        overview += "**Generated:** Real-time system information\n\n"
        
        overview += "## Available System Information Tools\n\n"
        overview += "- **System Information**: Complete hardware and OS details\n"
        overview += "- **Network Information**: Network interfaces and device discovery\n"
        overview += "- **Performance Metrics**: Real-time CPU, memory, disk, network usage\n"
        overview += "- **System Health Check**: Automated health assessment with recommendations\n\n"
        
        overview += "## Usage Examples\n\n"
        overview += "### Get System Information\n"
        overview += "Use the `get_system_information` tool to retrieve complete system specs:\n"
        overview += "```\n"
        overview += "get_system_information(include_sensitive=False)\n"
        overview += "```\n\n"
        
        overview += "### Network Discovery\n"
        overview += "Use the `get_network_information` tool to scan your network:\n"
        overview += "```\n"
        overview += "get_network_information(scan_time=10, include_devices=True, disable_vendor_search=False)\n"
        overview += "```\n\n"
        
        overview += "### Performance Monitoring\n"
        overview += "Use the `get_performance_metrics` tool for real-time metrics:\n"
        overview += "```\n"
        overview += "get_performance_metrics(detailed=True)\n"
        overview += "```\n\n"
        
        overview += "### Health Check\n"
        overview += "Use the `check_system_health` tool for comprehensive diagnostics:\n"
        overview += "```\n"
        overview += "check_system_health(include_network_scan=True)\n"
        overview += "```\n\n"
        
        overview += "## Requirements\n\n"
        overview += "This server requires the `syinfo` package:\n"
        overview += "```bash\n"
        overview += "pip install syinfo\n"
        overview += "```\n\n"
        
        overview += "**Note**: Some system information may require elevated privileges on certain systems.\n"
        
        return overview

    @mcp_server.resource("resource://system/quick-stats")
    def get_quick_stats() -> str:
        """Get quick system statistics for monitoring dashboards."""
        
        stats = "# Quick System Stats\n\n"
        stats += "**Real-time System Metrics**\n\n"
        
        # Note: In a real implementation, you would call the syinfo tools here
        # For this example, we're just showing the structure
        stats += "To get real-time metrics, use the MCP tools:\n\n"
        stats += "- `get_system_information()` - Complete system info\n"
        stats += "- `get_performance_metrics()` - Current performance\n"
        stats += "- `check_system_health()` - Health assessment\n\n"
        
        stats += "**Tool Status**: Ready to collect system information\n"
        
        return stats
    
    # Add system monitoring prompts
    @mcp_server.prompt()
    def get_system_monitoring_prompt() -> str:
        """Get prompt for system monitoring and diagnostics."""
        return """You are a system monitoring AI assistant with access to comprehensive system information tools.

## Your Capabilities:
- **System Information**: Retrieve detailed hardware, OS, and configuration data
- **Network Analysis**: Scan networks, discover devices, analyze topology
- **Performance Monitoring**: Track CPU, memory, disk, and network utilization
- **Health Assessment**: Perform comprehensive system health checks with recommendations

## Available Tools:
1. `get_system_information(include_sensitive=False)` - Complete system specs
2. `get_network_information(scan_time=5, disable_vendor_search=True, include_devices=False)` - Network analysis
3. `get_performance_metrics(detailed=False)` - Real-time performance data
4. `check_system_health(include_network_scan=False)` - Health diagnostics

## Usage Guidelines:
- Use `include_sensitive=False` by default for security
- Network scans with `include_devices=True` provide comprehensive discovery
- Performance metrics with `detailed=True` give in-depth analysis
- Health checks with `include_network_scan=True` provide complete assessment

## Example Interactions:
- "What are the system specifications of this machine?"
- "Scan the network and show me all connected devices"
- "Check current CPU and memory usage"
- "Run a complete health check including network connectivity"
- "Monitor system performance and identify any bottlenecks"

## Security Notes:
- Sensitive information is filtered by default
- Network scanning may require elevated privileges
- Some metrics may need admin/root access
- Always respect privacy and security policies

You provide actionable insights based on real system data, helping with monitoring, troubleshooting, and optimization.
"""

    @mcp_server.prompt()
    def get_network_analysis_prompt() -> str:
        """Get prompt for network analysis and security assessment."""
        return """You are a network analysis AI assistant specializing in network topology, device discovery, and security assessment.

## Network Analysis Capabilities:
- **Interface Analysis**: Detailed network interface information
- **Device Discovery**: Scan and identify connected network devices
- **Topology Mapping**: Understand network structure and connections
- **Security Assessment**: Identify potential security concerns
- **Performance Analysis**: Network utilization and performance metrics

## Key Tool: get_network_information()
Parameters:
- `scan_time` (1-60 seconds): Longer scans find more devices
- `disable_vendor_search` (True/False): Enable for device vendor identification
- `include_devices` (True/False): Enable for comprehensive device discovery

## Analysis Approach:
1. **Quick Scan**: `get_network_information(scan_time=3, include_devices=False)` for interface info
2. **Discovery Scan**: `get_network_information(scan_time=15, include_devices=True, disable_vendor_search=False)` for full topology
3. **Security Scan**: Look for unexpected devices, open ports, security concerns

## Example Queries:
- "What network interfaces are active on this system?"
- "Scan the network for 30 seconds and identify all connected devices"
- "Find all devices on the network with their vendor information"
- "Analyze network topology and identify potential security risks"
- "Check for unauthorized devices on the network"

## Security Considerations:
- Network scanning may trigger security alerts
- Some networks may block or limit scanning
- Respect network policies and permissions
- Report suspicious or unauthorized devices

Provide detailed network insights while maintaining security awareness.
"""


def main():
    """Run the system information MCP server example."""
    
    config = {
        "server_name": "System Information MCP Server",
        "server_description": "MCP server for comprehensive system monitoring, network analysis, and performance tracking using syinfo",
        "allow_read_access": True,
        "allow_write_access": False,  # Read-only for safety
        "allow_delete_access": False,
        "syinfo_enabled": True,
        "network_scanning_enabled": True,
        "performance_monitoring_enabled": True
    }
    
    print("🖥️  Starting System Information MCP Server...")
    print(f"📊 Server: {config['server_name']}")
    print(f"🔧 Features: System Info, Network Discovery, Performance Monitoring, Health Checks")
    print("=" * 60)
    
    # Show requirements
    print("📋 Requirements:")
    print("   - syinfo package: pip install syinfo")
    print("   - Some features may require elevated privileges")
    print("")
    
    # Create server with syinfo capabilities
    server = TemplateMCPServer(
        server_name=config["server_name"],
        server_description=config["server_description"],
        host=os.getenv("MCP_HOST", "0.0.0.0"),
        port=int(os.getenv("MCP_PORT", "8000")),
        debug=os.getenv("MCP_DEBUG", "false").lower() == "true",
        capabilities_config=config,
        capabilities=ServerCapabilities.empty(),  # Use custom registration
        custom_registration_fn=register_syinfo_capabilities
    )
    
    # Setup and run
    server.setup_mcp_server_and_capabilities()
    server.run()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n👋 System Information server stopped by user")
    except Exception as e:
        print(f"❌ System Information server error: {e}")
        sys.exit(1)
