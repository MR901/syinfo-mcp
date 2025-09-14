# -*- coding: utf-8 -*-

# FOGLAMP_BEGIN
# See: https://foglamp.dianomic.com
# FOGLAMP_END

"""
MCP RESOURCES - CORRECTED IMPLEMENTATION

Resources are data providers that can be queried by an MCP client.
They provide structured access to FogLAMP system information and data.

This implementation provides proper MCP resource definitions with:
- Correct resource URI patterns
- Proper error handling
- String-based responses (MCP requirement)
- Comprehensive documentation
- Alignment with actual FogLAMP API capabilities
"""

from __future__ import annotations

import requests
import logging
from typing import Dict, List, Any, Optional, Union
from datetime import datetime

try:
    from foglamp.common import logger
    _logger = logger.setup(__name__, level=logging.INFO)
except:
    logging.basicConfig(level=logging.INFO)
    _logger = logging.getLogger(__name__)

from foglamp.services.mcp.common.http_client import HTTPClient
from foglamp.services.mcp.common.config_manager import DEFAULT_FOGLAMP_HOST, DEFAULT_FOGLAMP_PORT

__author__ = "Mohit Rajput"
__copyright__ = "Copyright (c) 2025 Dianomic Systems Inc."
__license__ = "Apache 2.0"
__version__ = "${VERSION}"


def register_resources(
    mcp_server,
    http_client: Optional[HTTPClient] = None,
    config: Optional[Dict[str, Any]] = None
):
    """Register all MCP resources to the MCP server.

    Registers comprehensive resource providers for FogLAMP system information,
    data access, and monitoring capabilities. Each resource provides structured
    access to specific FogLAMP API endpoints and data.

    Args:
        mcp_server: The MCP server instance to register resources with
        http_client: HTTP client for FogLAMP API communication
        config: Configuration dictionary for resource settings
    """

    # Initialize HTTP client if not provided
    if http_client is None:
        http_client = HTTPClient(
            DEFAULT_FOGLAMP_HOST,
            DEFAULT_FOGLAMP_PORT,
            auth_token=None,
            is_tls_enabled=False
        )

    # ============================================================================
    # SYSTEM HEALTH AND STATUS RESOURCES
    # ============================================================================

    @mcp_server.resource("resource://foglamp/system/health")
    def get_system_health_resource() -> str:
        """Get comprehensive FogLAMP system health and status information.

        Provides real-time system health metrics including uptime, data statistics,
        authentication status, and operational health indicators.

        Returns:
            str: Formatted system health information as markdown text
        """
        try:
            status, response = http_client.make_request(
                action="GET",
                uri="/foglamp/ping",
                params=None
            )

            if not status:
                result = "# System Health Error\n\n"
                result += "**Error:** Failed to retrieve system health\n\n"
                result += f"**Details:** {response.get('error', 'Unknown error')}\n\n"
                result += f"**Timestamp:** {datetime.now().isoformat()}\n"
                return result

            # Build the result string incrementally
            result = "# FogLAMP System Health\n\n"
            result += f"**Uptime:** {response.get('uptime', 'N/A')} seconds\n\n"
            result += f"**Data Read:** {response.get('dataRead', 'N/A')}\n\n"
            result += f"**Data Sent:** {response.get('dataSent', 'N/A')}\n\n"
            result += f"**Data Purged:** {response.get('dataPurged', 'N/A')}\n\n"
            result += f"**Authentication Optional:** {response.get('authenticationOptional', 'N/A')}\n\n"
            result += f"**Service Name:** {response.get('serviceName', 'N/A')}\n\n"
            result += f"**Host Name:** {response.get('hostName', 'N/A')}\n\n"

            # IP addresses
            ip_addresses = response.get("ipAddresses", [])
            if ip_addresses:
                result += f"**IP Addresses:** {', '.join(ip_addresses)}\n\n"

            result += f"**Health:** {response.get('health', 'N/A')}\n\n"
            result += f"**Safe Mode:** {response.get('safeMode', 'N/A')}\n\n"
            result += f"**Retrieved:** {datetime.now().isoformat()}\n"

            return result

        except Exception as e:
            _logger.error(f"Error fetching system health: {str(e)}")
            result = "# System Health Error\n\n"
            result += "**Error:** Failed to retrieve system health\n\n"
            result += f"**Details:** {str(e)}\n\n"
            result += f"**Timestamp:** {datetime.now().isoformat()}\n"
            return result

    @mcp_server.resource("resource://foglamp/system/statistics")
    def get_system_statistics_resource() -> str:
        """Get comprehensive FogLAMP system statistics.

        Provides detailed performance metrics including reading counts, buffered data,
        purged data, and system throughput statistics.

        Returns:
            str: Formatted system statistics as markdown text
        """
        try:
            status, response = http_client.make_request(
                action="GET",
                uri="/foglamp/statistics",
                params=None
            )

            if not status:
                result = "# System Statistics Error\n\n"
                result += "**Error:** Failed to retrieve system statistics\n\n"
                result += f"**Details:** {response.get('error', 'Unknown error')}\n\n"
                result += f"**Timestamp:** {datetime.now().isoformat()}\n"
                return result

            # Handle both list and dict responses
            if isinstance(response, list):
                stats = {}
                for item in response:
                    if isinstance(item, dict) and "key" in item and "value" in item:
                        stats[item["key"]] = item["value"]
            else:
                stats = response

            # Build the result string incrementally
            result = "# FogLAMP System Statistics\n\n"
            result += f"**Readings:** {stats.get('READINGS', 0):,}\n\n"
            result += f"**Buffered:** {stats.get('BUFFERED', 0):,}\n\n"
            result += f"**Purged:** {stats.get('PURGED', 0):,}\n\n"
            result += f"**Unsent:** {stats.get('UNSENT', 0):,}\n\n"
            result += f"**Sent:** {stats.get('SENT', 0):,}\n\n"
            result += f"**Filtered:** {stats.get('FILTERED', 0):,}\n\n"
            result += f"**Assets:** {stats.get('ASSETS', 0):,}\n\n"
            result += f"**Retrieved:** {datetime.now().isoformat()}\n"

            return result

        except Exception as e:
            _logger.error(f"Error fetching system statistics: {str(e)}")
            result = "# System Statistics Error\n\n"
            result += "**Error:** Failed to retrieve system statistics\n\n"
            result += f"**Details:** {str(e)}\n\n"
            result += f"**Timestamp:** {datetime.now().isoformat()}\n"
            return result

    # ============================================================================
    # USER MANAGEMENT RESOURCES
    # ============================================================================

    @mcp_server.resource("resource://foglamp/users")
    def get_users_resource() -> str:
        """Get comprehensive user management information.

        Provides detailed information about all registered users including their
        roles, access methods, and account details.

        Returns:
            str: Formatted user information as markdown text
        """
        try:
            status, response = http_client.make_request(
                action="GET",
                uri="/foglamp/user",
                params=None
            )

            if not status:
                result = "# Users Error\n\n"
                result += "**Error:** Failed to retrieve user information\n\n"
                result += f"**Details:** {response.get('error', 'Unknown error')}\n\n"
                result += f"**Timestamp:** {datetime.now().isoformat()}\n"
                return result

            users = response.get("users", [])

            # Build the result string incrementally
            result = "# FogLAMP Users\n\n"
            result += f"**Total Users:** {len(users)}\n\n"

            if users:
                for i, user in enumerate(users, 1):
                    result += f"## User {i}\n\n"
                    result += f"\t**Username:** {user.get('userName', 'N/A')}\n\n"
                    result += f"\t**Role ID:** {user.get('roleId', 'N/A')}\n\n"
                    result += f"\t**Real Name:** {user.get('realName', 'N/A')}\n\n"
                    result += f"\t**Description:** {user.get('description', 'N/A')}\n\n"
                    result += f"\t**Access Method:** {user.get('accessMethod', 'N/A')}\n\n"
            else:
                result += "**No users found.**\n\n"

            result += f"**Retrieved:** {datetime.now().isoformat()}\n"

            return result

        except Exception as e:
            _logger.error(f"Error fetching users: {str(e)}")
            result = "# Users Error\n\n"
            result += "**Error:** Failed to retrieve user information\n\n"
            result += f"**Details:** {str(e)}\n\n"
            result += f"**Timestamp:** {datetime.now().isoformat()}\n"
            return result

    # ============================================================================
    # SERVICE MANAGEMENT RESOURCES
    # ============================================================================

    @mcp_server.resource("resource://foglamp/services")
    def get_services_resource() -> str:
        """Get comprehensive service information.

        Provides detailed information about all FogLAMP services including their
        status, configuration, and operational details.

        Returns:
            str: Formatted service information as markdown text
        """
        try:
            status, response = http_client.make_request(
                action="GET",
                uri="/foglamp/service",
                params=None
            )

            if not status:
                result = "# Services Error\n\n"
                result += "**Error:** Failed to retrieve service information\n\n"
                result += f"**Details:** {response.get('error', 'Unknown error')}\n\n"
                result += f"**Timestamp:** {datetime.now().isoformat()}\n"
                return result

            services = response.get("services", [])

            # Build the result string incrementally
            result = "# FogLAMP Services\n\n"
            result += f"**Total Services:** {len(services)}\n\n"

            if services:
                for i, service in enumerate(services, 1):
                    result += f"## Service {i}\n\n"
                    result += f"\t**Name:** {service.get('name', 'N/A')}\n\n"
                    result += f"\t**Type:** {service.get('type', 'N/A')}\n\n"
                    result += f"\t**Status:** {service.get('status', 'N/A')}\n\n"
                    result += f"\t**Address:** {service.get('address', 'N/A')}\n\n"
                    result += f"\t**Protocol:** {service.get('protocol', 'N/A')}\n\n"
            else:
                result += "**No services found.**\n\n"

            result += f"**Retrieved:** {datetime.now().isoformat()}\n"

            return result

        except Exception as e:
            _logger.error(f"Error fetching services: {str(e)}")
            result = "# Services Error\n\n"
            result += "**Error:** Failed to retrieve service information\n\n"
            result += f"**Details:** {str(e)}\n\n"
            result += f"**Timestamp:** {datetime.now().isoformat()}\n"
            return result

    @mcp_server.resource("resource://foglamp/services/south")
    def get_south_services_resource() -> str:
        """Get detailed south service information.

        Provides comprehensive information about southbound services including
        assets they ingest, reading counts, and plugin details.

        Returns:
            str: Formatted south service information as markdown text
        """
        try:
            status, response = http_client.make_request(
                action="GET",
                uri="/foglamp/south",
                params=None
            )

            if not status:
                result = "# South Services Error\n\n"
                result += "**Error:** Failed to retrieve south service information\n\n"
                result += f"**Details:** {response.get('error', 'Unknown error')}\n\n"
                result += f"**Timestamp:** {datetime.now().isoformat()}\n"
                return result

            services = response.get("services", [])
            total_assets = sum(len(service.get("assets", [])) for service in services)

            # Build the result string incrementally
            result = "# FogLAMP South Services\n\n"
            result += f"**Total Services:** {len(services)}\n\n"
            result += f"**Total Assets:** {total_assets}\n\n"

            if services:
                for i, service in enumerate(services, 1):
                    result += f"## South Service {i}\n\n"
                    result += f"\t**Name:** {service.get('name', 'N/A')}\n\n"
                    result += f"\t**Plugin:** {service.get('plugin', 'N/A')}\n\n"
                    result += f"\t**Status:** {service.get('status', 'N/A')}\n\n"
                    result += f"\t**Address:** {service.get('address', 'N/A')}\n\n"

                    # Assets
                    assets = service.get("assets", [])
                    if assets:
                        result += f"\t**Assets ({len(assets)}):** {', '.join(assets)}\n\n"

                    # Reading counts
                    reading_counts = service.get("reading_counts", {})
                    if reading_counts:
                        result += "\t**Reading Counts:**\n\n"
                        for asset, count in reading_counts.items():
                            result += f"\t\t- {asset}: {count:,}\n\n"
            else:
                result += "**No south services found.**\n\n"

            result += f"**Retrieved:** {datetime.now().isoformat()}\n"

            return result

        except Exception as e:
            _logger.error(f"Error fetching south services: {str(e)}")
            result = "# South Services Error\n\n"
            result += "**Error:** Failed to retrieve south service information\n\n"
            result += f"**Details:** {str(e)}\n\n"
            result += f"**Timestamp:** {datetime.now().isoformat()}\n"
            return result

    @mcp_server.resource("resource://foglamp/services/north")
    def get_north_services_resource() -> str:
        """Get detailed north service information.

        Provides comprehensive information about northbound services including
        their destinations, transmission statistics, and plugin details.

        Returns:
            str: Formatted north service information as markdown text
        """
        try:
            status, response = http_client.make_request(
                action="GET",
                uri="/foglamp/north",
                params=None
            )

            if not status:
                result = "# North Services Error\n\n"
                result += "**Error:** Failed to retrieve north service information\n\n"
                result += f"**Details:** {response.get('error', 'Unknown error')}\n\n"
                result += f"**Timestamp:** {datetime.now().isoformat()}\n"
                return result

            services = response.get("services", [])
            destinations = set()
            for service in services:
                if "destination" in service:
                    destinations.add(service["destination"])

            # Build the result string incrementally
            result = "# FogLAMP North Services\n\n"
            result += f"**Total Services:** {len(services)}\n\n"
            result += f"**Total Destinations:** {len(destinations)}\n\n"

            if services:
                for i, service in enumerate(services, 1):
                    result += f"## North Service {i}\n\n"
                    result += f"\t**Name:** {service.get('name', 'N/A')}\n\n"
                    result += f"\t**Plugin:** {service.get('plugin', 'N/A')}\n\n"
                    result += f"\t**Destination:** {service.get('destination', 'N/A')}\n\n"
                    result += f"\t**Status:** {service.get('status', 'N/A')}\n\n"
                    result += f"\t**Address:** {service.get('address', 'N/A')}\n\n"

                    # Transmission stats
                    transmission_stats = service.get("transmission_stats", {})
                    if transmission_stats:
                        result += "\t**Transmission Statistics:**\n\n"
                        for key, value in transmission_stats.items():
                            result += f"\t\t- {key}: {value}\n\n"
            else:
                result += "**No north services found.**\n\n"

            result += f"**Retrieved:** {datetime.now().isoformat()}\n"

            return result

        except Exception as e:
            _logger.error(f"Error fetching north services: {str(e)}")
            result = "# North Services Error\n\n"
            result += "**Error:** Failed to retrieve north service information\n\n"
            result += f"**Details:** {str(e)}\n\n"
            result += f"**Timestamp:** {datetime.now().isoformat()}\n"
            return result

    # ============================================================================
    # ASSET AND DATA RESOURCES
    # ============================================================================

    @mcp_server.resource("resource://foglamp/assets")
    def get_assets_resource() -> str:
        """Get comprehensive asset information.

        Provides detailed information about all data assets in the FogLAMP system
        including their names, types, and basic metadata.

        Returns:
            str: Formatted asset information as markdown text
        """
        try:
            status, response = http_client.make_request(
                action="GET",
                uri="/foglamp/asset",
                params=None
            )

            if not status:
                result = "# Assets Error\n\n"
                result += "**Error:** Failed to retrieve asset information\n\n"
                result += f"**Details:** {response.get('error', 'Unknown error')}\n\n"
                result += f"**Timestamp:** {datetime.now().isoformat()}\n"
                return result

            assets = response if isinstance(response, list) else []

            # Build the result string incrementally
            result = "# FogLAMP Assets\n\n"
            result += f"**Total Assets:** {len(assets)}\n\n"

            if assets:
                for i, asset in enumerate(assets, 1):
                    result += f"## Asset {i}\n\n"
                    result += f"\t**Name:** {asset.get('name', asset) if isinstance(asset, dict) else asset}\n\n"
                    result += f"\t**Type:** {asset.get('type', 'unknown') if isinstance(asset, dict) else 'unknown'}\n\n"
                    result += f"\t**Description:** {asset.get('description', '') if isinstance(asset, dict) else ''}\n\n"

                    # Metadata
                    metadata = asset.get("metadata", {}) if isinstance(asset, dict) else {}
                    if metadata:
                        result += "\t**Metadata:**\n\n"
                        for key, value in metadata.items():
                            result += f"\t\t- {key}: {value}\n\n"
            else:
                result += "**No assets found.**\n\n"

            result += f"**Retrieved:** {datetime.now().isoformat()}\n"

            return result

        except Exception as e:
            _logger.error(f"Error fetching assets: {str(e)}")
            result = "# Assets Error\n\n"
            result += "**Error:** Failed to retrieve asset information\n\n"
            result += f"**Details:** {str(e)}\n\n"
            result += f"**Timestamp:** {datetime.now().isoformat()}\n"
            return result

    @mcp_server.resource("resource://foglamp/assets/{asset_name}")
    def get_asset_detail_resource(asset_name: str) -> str:
        """Get detailed information about a specific asset.

        Provides comprehensive information about a specific asset including
        its readings, metadata, and operational status.

        Args:
            asset_name (str): Name of the asset to retrieve details for

        Returns:
            str: Formatted asset details as markdown text
        """
        try:
            # Get asset readings
            status, readings_response = http_client.make_request(
                action="GET",
                uri=f"/foglamp/asset/{asset_name}",
                params={"limit": 10}
            )

            # Get asset summary
            status_summary, summary_response = http_client.make_request(
                action="GET",
                uri=f"/foglamp/asset/{asset_name}/summary",
                params=None
            )

            readings = []
            if status and readings_response:
                if isinstance(readings_response, list):
                    readings = readings_response[:10]  # Limit to 10 readings
                elif isinstance(readings_response, dict) and "readings" in readings_response:
                    readings = readings_response["readings"][:10]

            summary = {}
            if status_summary and summary_response:
                summary = summary_response

            # Build the result string incrementally
            result = f"# Asset Details: {asset_name}\n\n"
            result += f"**Asset Name:** {asset_name}\n\n"
            result += f"**Total Readings:** {len(readings)}\n\n"

            # Summary information
            if summary:
                result += "## Summary Statistics\n\n"
                for key, value in summary.items():
                    result += f"\t**{key}:** {value}\n\n"

            # Recent readings
            if readings:
                result += "## Recent Readings\n\n"
                for i, reading in enumerate(readings[:5], 1):  # Show first 5 readings
                    result += f"### Reading {i}\n\n"
                    if isinstance(reading, dict):
                        for key, value in reading.items():
                            result += f"\t**{key}:** {value}\n\n"
                    else:
                        result += f"\t**Value:** {reading}\n\n"

            result += f"**Retrieved:** {datetime.now().isoformat()}\n"

            return result

        except Exception as e:
            _logger.error(f"Error fetching asset details for {asset_name}: {str(e)}")
            result = f"# Asset Details Error\n\n"
            result += f"**Asset:** {asset_name}\n\n"
            result += "**Error:** Failed to retrieve asset details\n\n"
            result += f"**Details:** {str(e)}\n\n"
            result += f"**Timestamp:** {datetime.now().isoformat()}\n"
            return result

    # ============================================================================
    # CONFIGURATION RESOURCES
    # ============================================================================

    @mcp_server.resource("resource://foglamp/configuration")
    def get_configuration_categories_resource() -> str:
        """Get all configuration categories.

        Provides comprehensive information about all configuration categories
        in the FogLAMP system.

        Returns:
            str: Formatted configuration categories as markdown text
        """
        try:
            status, response = http_client.make_request(
                action="GET",
                uri="/foglamp/category",
                params=None
            )

            if not status:
                result = "# Configuration Categories Error\n\n"
                result += "**Error:** Failed to retrieve configuration categories\n\n"
                result += f"**Details:** {response.get('error', 'Unknown error')}\n\n"
                result += f"**Timestamp:** {datetime.now().isoformat()}\n"
                return result

            categories = response.get("categories", [])

            # Build the result string incrementally
            result = "# FogLAMP Configuration Categories\n\n"
            result += f"**Total Categories:** {len(categories)}\n\n"

            if categories:
                for i, cat in enumerate(categories, 1):
                    result += f"## Category {i}\n\n"
                    result += f"\t**Key:** {cat.get('key', 'N/A')}\n\n"
                    result += f"\t**Description:** {cat.get('description', 'N/A')}\n\n"
                    result += f"\t**Display Name:** {cat.get('displayName', 'N/A')}\n\n"
                    result += f"\t**Type:** {cat.get('type', 'N/A')}\n\n"
            else:
                result += "**No configuration categories found.**\n\n"

            result += f"**Retrieved:** {datetime.now().isoformat()}\n"

            return result

        except Exception as e:
            _logger.error(f"Error fetching configuration categories: {str(e)}")
            result = "# Configuration Categories Error\n\n"
            result += "**Error:** Failed to retrieve configuration categories\n\n"
            result += f"**Details:** {str(e)}\n\n"
            result += f"**Timestamp:** {datetime.now().isoformat()}\n"
            return result

    @mcp_server.resource("resource://foglamp/configuration/{category_name}")
    def get_configuration_detail_resource(category_name: str) -> str:
        """Get detailed configuration for a specific category.

        Provides comprehensive configuration information for a specific
        configuration category including all its settings and values.

        Args:
            category_name (str): Name of the configuration category

        Returns:
            str: Formatted configuration details as markdown text
        """
        try:
            status, response = http_client.make_request(
                action="GET",
                uri=f"/foglamp/category/{category_name}",
                params=None
            )

            if not status:
                result = f"# Configuration Error\n\n"
                result += f"**Category:** {category_name}\n\n"
                result += "**Error:** Failed to retrieve configuration\n\n"
                result += f"**Details:** {response.get('error', 'Unknown error')}\n\n"
                result += f"**Timestamp:** {datetime.now().isoformat()}\n"
                return result

            # Build the result string incrementally
            result = f"# Configuration: {category_name}\n\n"
            result += f"**Category Key:** {response.get('key', category_name)}\n\n"
            result += f"**Description:** {response.get('description', 'N/A')}\n\n"
            result += f"**Display Name:** {response.get('displayName', category_name)}\n\n"
            result += f"**Type:** {response.get('type', 'N/A')}\n\n"
            result += "## Configuration Items\n\n"

            # Add configuration items
            value = response.get("value", {})
            if value:
                for item_name, item_data in value.items():
                    result += f"### {item_name}\n\n"

                    if isinstance(item_data, dict):
                        result += f"\t**Description:** {item_data.get('description', 'N/A')}\n\n"
                        result += f"\t**Type:** {item_data.get('type', 'N/A')}\n\n"
                        result += f"\t**Default:** {item_data.get('default', 'N/A')}\n\n"
                        result += f"\t**Current Value:** {item_data.get('value', 'N/A')}\n\n"
                        result += f"\t**Mandatory:** {item_data.get('mandatory', 'N/A')}\n\n"
                    else:
                        result += f"\t**Value:** {item_data}\n\n"
            else:
                result += "\tNo configuration items found.\n\n"

            result += f"**Retrieved:** {datetime.now().isoformat()}\n"

            return result

        except Exception as e:
            _logger.error(f"Error fetching configuration for {category_name}: {str(e)}")
            result = f"# Configuration Error\n\n"
            result += f"**Category:** {category_name}\n\n"
            result += "**Error:** Failed to retrieve configuration\n\n"
            result += f"**Details:** {str(e)}\n\n"
            result += f"**Timestamp:** {datetime.now().isoformat()}\n"
            return result

    # ============================================================================
    # AUDIT AND LOGGING RESOURCES
    # ============================================================================

    @mcp_server.resource("resource://foglamp/audit")
    def get_audit_logs_resource() -> str:
        """Get recent audit log entries.

        Provides comprehensive audit trail information including system events,
        configuration changes, and operational activities.

        Returns:
            str: Formatted audit log information as markdown text
        """
        try:
            status, response = http_client.make_request(
                action="GET",
                uri="/foglamp/audit",
                params={"limit": 20}
            )

            if not status:
                result = "# Audit Logs Error\n\n"
                result += "**Error:** Failed to retrieve audit logs\n\n"
                result += f"**Details:** {response.get('error', 'Unknown error')}\n\n"
                result += f"**Timestamp:** {datetime.now().isoformat()}\n"
                return result

            audit_entries = response.get("audit", [])

            # Build the result string incrementally
            result = "# Recent Audit Log Entries\n\n"
            result += f"**Total Entries:** {len(audit_entries)}\n\n"
            result += f"**Retrieved:** {datetime.now().isoformat()}\n\n"

            if audit_entries:
                result += "## Audit Entries\n\n"

                for i, entry in enumerate(audit_entries, 1):
                    result += f"### Entry {i}\n\n"
                    result += f"\t**Timestamp:** {entry.get('timestamp', 'N/A')}\n\n"
                    result += f"\t**Source:** {entry.get('source', 'N/A')}\n\n"
                    result += f"\t**Severity:** {entry.get('severity', 'N/A')}\n\n"
                    result += f"\t**Message:** {entry.get('details', {}).get('message', 'N/A')}\n\n"

                    # Add additional details if available
                    details = entry.get('details', {})
                    if details and len(details) > 1:  # More than just 'message'
                        result += "\t**Additional Details:**\n\n"
                        for key, value in details.items():
                            if key != 'message':  # Skip message as it's already shown
                                result += f"\t\t- **{key}:** {value}\n\n"
            else:
                result += "**No audit entries found.**\n"

            return result

        except Exception as e:
            _logger.error(f"Error fetching audit logs: {str(e)}")
            result = "# Audit Logs Error\n\n"
            result += "**Error:** Failed to retrieve audit logs\n\n"
            result += f"**Details:** {str(e)}\n\n"
            result += f"**Timestamp:** {datetime.now().isoformat()}\n"
            return result

    # ============================================================================
    # SCHEDULE MANAGEMENT RESOURCES
    # ============================================================================

    @mcp_server.resource("resource://foglamp/schedules")
    def get_schedules_resource() -> str:
        """Get all scheduled tasks.

        Provides comprehensive information about all scheduled tasks in the
        FogLAMP system including their configuration and status.

        Returns:
            str: Formatted schedule information as markdown text
        """
        try:
            status, response = http_client.make_request(
                action="GET",
                uri="/foglamp/schedule",
                params=None
            )

            if not status:
                result = "# Schedules Error\n\n"
                result += "**Error:** Failed to retrieve schedules\n\n"
                result += f"**Details:** {response.get('error', 'Unknown error')}\n\n"
                result += f"**Timestamp:** {datetime.now().isoformat()}\n"
                return result

            schedules = response.get("schedules", [])

            # Build the result string incrementally
            result = "# FogLAMP Schedules\n\n"
            result += f"**Total Schedules:** {len(schedules)}\n\n"

            if schedules:
                for i, schedule in enumerate(schedules, 1):
                    result += f"## Schedule {i}\n\n"
                    result += f"\t**ID:** {schedule.get('id', 'N/A')}\n\n"
                    result += f"\t**Name:** {schedule.get('name', 'N/A')}\n\n"
                    result += f"\t**Type:** {schedule.get('type', 'N/A')}\n\n"
                    result += f"\t**Process Name:** {schedule.get('processName', 'N/A')}\n\n"
                    result += f"\t**Repeat:** {schedule.get('repeat', 'N/A')}\n\n"
                    result += f"\t**Time:** {schedule.get('time', 'N/A')}\n\n"
                    result += f"\t**Day:** {schedule.get('day', 'N/A')}\n\n"
                    result += f"\t**Exclusive:** {schedule.get('exclusive', 'N/A')}\n\n"
                    result += f"\t**Enabled:** {schedule.get('enabled', 'N/A')}\n\n"
            else:
                result += "**No schedules found.**\n\n"

            result += f"**Retrieved:** {datetime.now().isoformat()}\n"

            return result

        except Exception as e:
            _logger.error(f"Error fetching schedules: {str(e)}")
            result = "# Schedules Error\n\n"
            result += "**Error:** Failed to retrieve schedules\n\n"
            result += f"**Details:** {str(e)}\n\n"
            result += f"**Timestamp:** {datetime.now().isoformat()}\n"
            return result

    # ============================================================================
    # PLUGIN MANAGEMENT RESOURCES
    # ============================================================================

    @mcp_server.resource("resource://foglamp/plugins/installed")
    def get_installed_plugins_resource() -> str:
        """Get installed plugin information.

        Provides comprehensive information about all installed plugins
        in the FogLAMP system.

        Returns:
            str: Formatted plugin information as markdown text
        """
        try:
            status, response = http_client.make_request(
                action="GET",
                uri="/foglamp/service/installed",
                params=None
            )

            if not status:
                result = "# Installed Plugins Error\n\n"
                result += "**Error:** Failed to retrieve installed plugins\n\n"
                result += f"**Details:** {response.get('error', 'Unknown error')}\n\n"
                result += f"**Timestamp:** {datetime.now().isoformat()}\n"
                return result

            plugins = response.get("services", [])

            # Build the result string incrementally
            result = "# FogLAMP Installed Plugins\n\n"
            result += f"**Total Plugins:** {len(plugins)}\n\n"

            if plugins:
                for i, plugin in enumerate(plugins, 1):
                    result += f"## Plugin {i}\n\n"
                    result += f"\t**Name:** {plugin.get('name', 'N/A')}\n\n"
                    result += f"\t**Type:** {plugin.get('type', 'N/A')}\n\n"
                    result += f"\t**Description:** {plugin.get('description', 'N/A')}\n\n"
                    result += f"\t**Installed Count:** {plugin.get('installed_count', 'N/A')}\n\n"
            else:
                result += "**No installed plugins found.**\n\n"

            result += f"**Retrieved:** {datetime.now().isoformat()}\n"

            return result

        except Exception as e:
            _logger.error(f"Error fetching installed plugins: {str(e)}")
            result = "# Installed Plugins Error\n\n"
            result += "**Error:** Failed to retrieve installed plugins\n\n"
            result += f"**Details:** {str(e)}\n\n"
            result += f"**Timestamp:** {datetime.now().isoformat()}\n"
            return result

    _logger.info("MCP Resources registered successfully")
