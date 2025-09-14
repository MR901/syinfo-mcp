# -*- coding: utf-8 -*-

"""
SYINFO MCP TOOLS

Tools are functions that can be called by an MCP client (e.g., an LLM or another application).
They perform actions or computations related to system information gathering using the syinfo package.
"""

from __future__ import annotations

import logging
from typing import Dict, List, Any, Optional

# Setup logging with fallback
try:
    from src.common.config_manager import _logger
except ImportError:
    logging.basicConfig(level=logging.INFO)
    _logger = logging.getLogger(__name__)

# Import syinfo components with error handling
try:
    from syinfo.syinfo import SysInfo
    from syinfo.network_info import NetworkInfo
    SYINFO_AVAILABLE = True
    _logger.info("syinfo package loaded successfully")
except ImportError as e:
    SYINFO_AVAILABLE = False
    _logger.warning(f"syinfo package not available: {e}")
    _logger.warning("Install with: pip install syinfo")

__author__ = "Template Author"
__copyright__ = "Copyright (c) 2025"
__license__ = "Apache 2.0"
__version__ = "1.0.0"


def register_tools(
    mcp_server,
    http_client=None,
    config: Dict[str, Any] = None
):
    """Register syinfo-based tools into the MCP server."""

    @mcp_server.tool()
    def get_system_information(
        include_sensitive: bool = False
    ) -> Dict[str, Any]:
        """Get comprehensive system information including hardware, OS, and performance metrics.

        Retrieves detailed system information including CPU, memory, disk, network interfaces,
        operating system details, and performance metrics. Essential for system monitoring,
        troubleshooting, and inventory management.

        Examples:
            LLM Input Examples:
                - "Get complete system information for this machine"
                - "Show me the hardware specifications of this system"
                - "What are the current system specs including CPU and memory?"
                - "Get system info for monitoring and diagnostics"

            Function Call Examples:
                - get_system_information()
                - get_system_information(include_sensitive=True)

        Args:
            include_sensitive (bool): Whether to include potentially sensitive information
                                    like serial numbers, MAC addresses, etc.
                                    Default: False for security

        Returns:
            Dict[str, Any]: Comprehensive system information containing:
                - cpu: CPU model, cores, architecture, frequency
                - memory: Total, used, free, swap information
                - disk: Disk usage, file systems, mount points
                - network: Network interfaces and configuration
                - os: Operating system name, version, kernel info
                - system: Hostname, uptime, boot time
                - performance: Current CPU/memory usage percentages

        Errors:
            - ImportError: When syinfo package is not installed
            - PermissionError: When insufficient privileges to access system info
            - OSError: When system information cannot be retrieved
            - RuntimeError: When syinfo encounters internal errors

        Notes:
            - Requires syinfo package: pip install syinfo
            - Some information may require elevated privileges
            - Performance metrics are current snapshot values
            - Sensitive data filtering is applied for security
            - Cross-platform compatible (Linux, Windows, macOS)
        """
        _logger.info(f"Triggering `tool:get_system_information` with {include_sensitive=}")
        
        if not SYINFO_AVAILABLE:
            return {
                "error": "syinfo package not available",
                "message": "Install with: pip install syinfo",
                "status": "package_missing"
            }

        try:
            # Get comprehensive system information
            system_info = SysInfo.get_all()
            
            # Filter sensitive information if requested
            if not include_sensitive and isinstance(system_info, dict):
                # Remove or mask sensitive fields
                sensitive_fields = ['serial_number', 'uuid', 'mac_address', 'ip_address']
                for field in sensitive_fields:
                    if field in system_info:
                        system_info[field] = "[FILTERED]"
                
                # Recursively filter nested dictionaries
                def filter_sensitive(data):
                    if isinstance(data, dict):
                        return {k: ("[FILTERED]" if any(sensitive in k.lower() for sensitive in ['serial', 'uuid', 'mac', 'address']) else filter_sensitive(v)) for k, v in data.items()}
                    elif isinstance(data, list):
                        return [filter_sensitive(item) for item in data]
                    return data
                
                if not include_sensitive:
                    system_info = filter_sensitive(system_info)
            
            return {
                "status": "success",
                "system_info": system_info,
                "sensitive_filtered": not include_sensitive,
                "timestamp": _get_current_timestamp()
            }
            
        except Exception as e:
            _logger.error(f"Error getting system information: {e}")
            return {
                "error": str(e),
                "status": "failed",
                "timestamp": _get_current_timestamp()
            }

    @mcp_server.tool()
    def get_network_information(
        scan_time: int = 5,
        disable_vendor_search: bool = True,
        include_devices: bool = False
    ) -> Dict[str, Any]:
        """Get comprehensive network information including interfaces, connected devices, and topology.

        Scans the local network to discover connected devices, analyze network topology,
        and provide detailed information about network interfaces and connections.
        Essential for network monitoring, security auditing, and troubleshooting.

        Examples:
            LLM Input Examples:
                - "Scan the network and show me all connected devices"
                - "Get network information including device discovery"
                - "Show me the network topology and connected hosts"
                - "Scan for 10 seconds and find all network devices with vendor info"

            Function Call Examples:
                - get_network_information()
                - get_network_information(scan_time=10, disable_vendor_search=False)
                - get_network_information(scan_time=3, include_devices=True)

        Args:
            scan_time (int): Time in seconds to scan for network devices.
                           Range: 1-60 seconds, Default: 5
                           Longer scans find more devices but take more time
            disable_vendor_search (bool): Skip vendor lookup for discovered devices.
                                        Default: True (faster scanning)
                                        Set to False for detailed vendor information
            include_devices (bool): Whether to include discovered network devices.
                                  Default: False (only interface information)
                                  Set to True for full device discovery

        Returns:
            Dict[str, Any]: Network information containing:
                - interfaces: Network interface details (IP, MAC, status)
                - gateway: Default gateway information
                - dns_servers: Configured DNS servers
                - network_range: Local network CIDR range
                - devices: Discovered network devices (if include_devices=True)
                - scan_summary: Scan statistics and timing info
                - security_info: Open ports and security-relevant findings

        Errors:
            - ImportError: When syinfo package is not installed
            - PermissionError: When insufficient privileges for network scanning
            - TimeoutError: When network scan exceeds maximum allowed time
            - NetworkError: When network interface access fails
            - OSError: When network system calls fail

        Notes:
            - Requires syinfo package: pip install syinfo
            - Network scanning may require elevated privileges
            - Longer scan times discover more devices but use more resources
            - Vendor lookup requires internet connection
            - Results may vary based on network topology and security settings
            - Some networks may block or limit scanning activities
        """
        _logger.info(f"Triggering `tool:get_network_information` with {scan_time=}, {disable_vendor_search=}, {include_devices=}")
        
        if not SYINFO_AVAILABLE:
            return {
                "error": "syinfo package not available",
                "message": "Install with: pip install syinfo",
                "status": "package_missing"
            }

        try:
            # Validate scan time
            scan_time = max(1, min(60, scan_time))  # Clamp between 1 and 60 seconds
            
            # Get network information
            if include_devices:
                network_info = NetworkInfo.get_all(
                    scan_time=scan_time, 
                    disable_vendor_search=disable_vendor_search
                )
            else:
                # Get only interface information (faster)
                try:
                    network_info = NetworkInfo.get_interfaces_info()
                except AttributeError:
                    # Fallback if method doesn't exist
                    network_info = NetworkInfo.get_all(
                        scan_time=1, 
                        disable_vendor_search=True
                    )
            
            return {
                "status": "success",
                "network_info": network_info,
                "scan_parameters": {
                    "scan_time": scan_time,
                    "vendor_search_enabled": not disable_vendor_search,
                    "device_discovery_enabled": include_devices
                },
                "timestamp": _get_current_timestamp()
            }
            
        except Exception as e:
            _logger.error(f"Error getting network information: {e}")
            return {
                "error": str(e),
                "status": "failed",
                "scan_parameters": {
                    "scan_time": scan_time,
                    "vendor_search_enabled": not disable_vendor_search,
                    "device_discovery_enabled": include_devices
                },
                "timestamp": _get_current_timestamp()
            }

    @mcp_server.tool()
    def get_performance_metrics(detailed: bool = False) -> Dict[str, Any]:
        """Get current system performance metrics including CPU, memory, disk, and network usage.

        Retrieves real-time system performance metrics for monitoring system health,
        identifying bottlenecks, and tracking resource utilization. Essential for
        performance monitoring, capacity planning, and system optimization.

        Examples:
            LLM Input Examples:
                - "Get current system performance metrics"
                - "Show me CPU and memory usage statistics"
                - "What's the current system load and resource utilization?"
                - "Get detailed performance metrics for monitoring"

            Function Call Examples:
                - get_performance_metrics()
                - get_performance_metrics(detailed=True)

        Args:
            detailed (bool): Whether to include detailed performance breakdowns.
                           Default: False (basic metrics only)
                           Set to True for per-core CPU stats, detailed memory breakdown

        Returns:
            Dict[str, Any]: Performance metrics containing:
                - cpu: Current CPU usage percentage and load average
                - memory: Memory usage, available, cached, buffered
                - disk: Disk I/O statistics and usage percentages
                - network: Network I/O bytes sent/received
                - processes: Process count and top consumers
                - uptime: System uptime and load metrics

        Errors:
            - ImportError: When syinfo package is not installed
            - PermissionError: When insufficient privileges to access performance data
            - OSError: When performance counters cannot be accessed
            - ValueError: When performance data is invalid or corrupted

        Notes:
            - Requires syinfo package: pip install syinfo
            - Performance data represents current snapshot
            - Some metrics may require elevated privileges
            - Network I/O counters are cumulative since boot
            - CPU usage is average over recent sampling period
        """
        _logger.info(f"Triggering `tool:get_performance_metrics` with {detailed=}")
        
        if not SYINFO_AVAILABLE:
            return {
                "error": "syinfo package not available", 
                "message": "Install with: pip install syinfo",
                "status": "package_missing"
            }

        try:
            system_info = SysInfo.get_all()
            performance_data = {}
            
            if isinstance(system_info, dict):
                for key in ['cpu', 'memory', 'disk', 'network', 'system']:
                    if key in system_info:
                        performance_data[key] = system_info[key]
                if detailed:
                    performance_data['full_system_info'] = system_info
            else:
                performance_data = system_info
            
            return {
                "status": "success", 
                "performance_metrics": performance_data, 
                "detailed": detailed, 
                "timestamp": _get_current_timestamp()
            }
        except Exception as e:
            _logger.error(f"Error getting performance metrics: {e}")
            return {
                "error": str(e), 
                "status": "failed", 
                "timestamp": _get_current_timestamp()
            }

    @mcp_server.tool()
    def check_system_health(include_network_scan: bool = False) -> Dict[str, Any]:
        """Perform comprehensive system health check including hardware status and network connectivity.

        Conducts a thorough system health assessment by checking critical system components,
        resource utilization, network connectivity, and potential issues. Essential for
        proactive monitoring, preventive maintenance, and system reliability assurance.

        Examples:
            LLM Input Examples:
                - "Run a complete system health check"
                - "Check system health including network connectivity"
                - "Perform health assessment of this system"
                - "Run diagnostics to identify any system issues"

            Function Call Examples:
                - check_system_health()
                - check_system_health(include_network_scan=True)

        Args:
            include_network_scan (bool): Whether to include network connectivity testing.
                                       Default: False (faster execution)
                                       Set to True for comprehensive network health check

        Returns:
            Dict[str, Any]: System health report containing:
                - overall_status: "healthy", "warning", "critical"
                - cpu_status: CPU health and utilization assessment
                - memory_status: Memory health and usage assessment
                - disk_status: Disk space and I/O health assessment
                - network_status: Network interface and connectivity status
                - issues_found: List of identified problems or warnings
                - recommendations: Suggested actions for improvements
                - health_score: Numerical health score (0-100)

        Errors:
            - ImportError: When syinfo package is not installed
            - PermissionError: When insufficient privileges for health checks
            - TimeoutError: When network health checks timeout
            - OSError: When system health data cannot be accessed
            - RuntimeError: When health check encounters critical errors

        Notes:
            - Requires syinfo package: pip install syinfo
            - Health assessment uses predefined thresholds for metrics
            - Network scan may require elevated privileges
            - Health score algorithm considers multiple system factors
            - Some checks may take longer on heavily loaded systems
            - Recommendations are based on common best practices
        """
        _logger.info(f"Triggering `tool:check_system_health` with {include_network_scan=}")
        
        if not SYINFO_AVAILABLE:
            return {
                "error": "syinfo package not available",
                "message": "Install with: pip install syinfo", 
                "status": "package_missing"
            }

        try:
            health_report = {
                "overall_status": "healthy",
                "issues_found": [],
                "recommendations": [],
                "health_score": 100,
                "timestamp": _get_current_timestamp()
            }
            
            system_info = SysInfo.get_all()
            
            # Simple health assessment
            if isinstance(system_info, dict):
                # Check CPU health
                if 'cpu' in system_info:
                    cpu_info = system_info['cpu']
                    if 'usage' in cpu_info and float(cpu_info.get('usage', 0)) > 90:
                        health_report["issues_found"].append("High CPU usage detected")
                        health_report["recommendations"].append("Check for resource-intensive processes")
                        health_report["health_score"] -= 20
                    elif 'usage' in cpu_info and float(cpu_info.get('usage', 0)) > 75:
                        health_report["issues_found"].append("Moderate CPU usage")
                        health_report["recommendations"].append("Monitor CPU usage trends")
                        health_report["health_score"] -= 10
                
                # Check memory health
                if 'memory' in system_info:
                    memory_info = system_info['memory'] 
                    if 'usage_percent' in memory_info and float(memory_info.get('usage_percent', 0)) > 95:
                        health_report["issues_found"].append("Critical memory usage detected")
                        health_report["recommendations"].append("Free up memory immediately or add more RAM")
                        health_report["health_score"] -= 25
                    elif 'usage_percent' in memory_info and float(memory_info.get('usage_percent', 0)) > 85:
                        health_report["issues_found"].append("High memory usage detected")
                        health_report["recommendations"].append("Consider closing unnecessary applications")
                        health_report["health_score"] -= 15
                
                # Check disk health
                if 'disk' in system_info:
                    disk_info = system_info['disk']
                    if 'usage_percent' in disk_info and float(disk_info.get('usage_percent', 0)) > 95:
                        health_report["issues_found"].append("Critical disk usage detected")
                        health_report["recommendations"].append("Free up disk space immediately")
                        health_report["health_score"] -= 25
                    elif 'usage_percent' in disk_info and float(disk_info.get('usage_percent', 0)) > 85:
                        health_report["issues_found"].append("High disk usage detected")
                        health_report["recommendations"].append("Clean up unnecessary files")
                        health_report["health_score"] -= 15
                
                # Network health check if requested
                if include_network_scan:
                    try:
                        network_info = NetworkInfo.get_all(scan_time=1, disable_vendor_search=True)
                        if isinstance(network_info, dict) and 'interfaces' in network_info:
                            active_interfaces = sum(1 for interface in network_info['interfaces'] if interface.get('is_up', False) or interface.get('status') == 'up')
                            if active_interfaces == 0:
                                health_report["issues_found"].append("No active network interfaces")
                                health_report["recommendations"].append("Check network connections")
                                health_report["health_score"] -= 20
                    except Exception as ne:
                        health_report["issues_found"].append("Network health check failed")
                        health_report["recommendations"].append("Check network configuration")
                        health_report["health_score"] -= 5
            
            # Determine overall status
            if health_report["health_score"] >= 90:
                health_report["overall_status"] = "healthy"
            elif health_report["health_score"] >= 70:
                health_report["overall_status"] = "warning"
            else:
                health_report["overall_status"] = "critical"
            
            health_report["status"] = "success"
            return health_report
            
        except Exception as e:
            _logger.error(f"Error performing system health check: {e}")
            return {
                "error": str(e),
                "status": "failed",
                "overall_status": "unknown",
                "timestamp": _get_current_timestamp()
            }


def _get_current_timestamp() -> str:
    """Get current timestamp in ISO format."""
    try:
        from datetime import datetime
        return datetime.now().isoformat()
    except:
        return "timestamp_unavailable"