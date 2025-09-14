# -*- coding: utf-8 -*-

# FOGLAMP_BEGIN
# See: https://foglamp.dianomic.com
# FOGLAMP_END

"""
MCP TOOLS

Tools are functions that can be called by an MCP client (e.g., an LLM or another application).
They perform actions or computations related to FogLAMP operations.
"""

from __future__ import annotations

import os
import requests
import logging
import subprocess
from typing import Union, Dict, List, Any, Optional

try:
    from foglamp.common import logger
    _logger = logger.setup(__name__, level=logging.INFO)
except:
    logging.basicConfig(level=logging.INFO)
    _logger = logging.getLogger(__name__)

from foglamp.services.mcp.src.general.plugins import FogLAMPPlugin
from foglamp.services.mcp.src.general.syslogs import query_syslog as _query_syslog


__author__ = "Mohit Rajput"
__copyright__ = "Copyright (c) 2025 Dianomic Systems Inc."
__license__ = "Apache 2.0"
__version__ = "${VERSION}"


def register_tools(
    mcp_server,
    http_client=None,
    config: Dict[str, Any] = None
):
    """Register tools into the MCP server."""

    @mcp_server.tool()
    def search_syslog(
        match: str = "", severity: str = "", limit: int = 5
    ) -> List[str]:
        """Query system log entries with filtering by text match, severity level, and result limit.

        Enables real-time system monitoring and debugging by filtering syslog entries
        for specific events, error conditions, or keywords. Essential for troubleshooting
        FogLAMP system issues and monitoring operational health.

        Examples:
            LLM Input Examples:
                - "Get the last 5 ERROR logs that contain the word 'disk' from syslog"
                - "Show me all recent syslog entries at error severity in raw format"
                - "Find any logs mentioning 'connection failed' in the last 10 entries"
                - "Check for any CRITICAL severity messages in syslog"

            Function Call Examples:
                - query_syslog(match="disk", severity="ERROR", limit=5)
                - query_syslog(severity="WARNING", limit=10)
                - query_syslog(match="connection", limit=20)

        Args:
            match (str): Substring to search for in log lines (case-insensitive).
                        Empty string means no text filtering. Example: "failed", "error", "disk"
            severity (str): Filter by syslog severity level. Case-insensitive.
                           Options: "INFO", "WARNING", "ERROR", "CRITICAL", "DEBUG"
                           Empty string means no severity filtering
            limit (int): Maximum number of matching log lines to return.
                        Default: 5, Range: 1-1000

        Returns:
            List[str]: List of matching syslog lines, newest first.
                      Each line includes timestamp, severity, and message.
                      Empty list if no matches found or file doesn't exist.

        Errors:
            - FileNotFoundError: When /var/log/syslog doesn't exist
            - PermissionError: When syslog file is not readable
            - OSError: When file system errors occur during reading

        Notes:
            - Reads from /var/log/syslog (Ubuntu/Debian systems)
            - Searches from newest to oldest entries
            - Text matching is case-insensitive for better usability
            - Returns raw log lines without parsing or formatting
        """
        _logger.info(f"Triggering `tool:search_syslog` with {match=}, {severity=}, {limit=}.")
        return _query_syslog(match, severity, limit)

    @mcp_server.tool()
    def discover_plugins(
        plugin_type: str = "",
        search_term: str = "",
        os_type: str = "ubuntu2004",
        architecture: str = "x86_64",
        repository_url: str = "http://archives.dianomic.com/foglamp/latest/",
        include_details: bool = False,
        sort_by: str = "name"
    ) -> Dict[str, Any]:
        """Discover and search available FogLAMP plugins/packages from Dianomic archives repository.

        Enables plugin discovery for system expansion, dependency management, and
        installation planning. Essential for administrators to understand available
        capabilities and for automated deployment workflows.

        Examples:
            LLM Input Examples:
                - "List all available FogLAMP plugins/packages"
                - "Show me all south plugins for Ubuntu 24.04"
                - "Search for sinusoid plugin"
                - "Find PI Server plugins for x86_64 architecture"
                - "List all filter plugins with details"
                - "What north plugins are available for Raspberry Pi?"

            Function Call Examples:
                - list_foglamp_plugins()
                - list_foglamp_plugins(plugin_type="south", os_type="ubuntu2004")
                - list_foglamp_plugins(search_term="sinusoid", include_details=True)
                - list_foglamp_plugins(plugin_type="north", architecture="arm64")

        Args:
            plugin_type (str, optional): Filter by plugin category.
                                        Options: "south", "north", "filter", "notification", "rule", "service"
            search_term (str, optional): Text to search in plugin names and descriptions.
                                       Case-insensitive partial matching
            os_type (str): Target operating system for plugin compatibility.
                          Options: "ubuntu2204", "ubuntu2204", "rpi-bookworm"
                          Default: "ubuntu2404"
            architecture (str): System architecture for plugin compatibility.
                               Options: "x86_64", "arm64", "armhf"
                               Default: "x86_64"
            repository_url (str): Base URL for plugin repository.
                                 Default: Dianomic official repository
            include_details (bool): Include file size and modification date in results.
                                   Default: False (faster response)
            sort_by (str): Result sorting order.
                          Options: "name", "version", "size", "date"
                          Default: "name"

        Returns:
            Dict[str, Any]: Plugin discovery results containing:
                - plugins (list): List of matching plugins with metadata
                - summary (dict): Count statistics and filter information
                - repository_info (dict): Repository URL and access status

        Errors:
            - ConnectionError: When repository is unreachable
            - TimeoutError: When repository request times out
            - ValueError: When invalid plugin_type or sort_by values provided
            - HTTPError: When repository returns error status

        Notes:
            - Searches Dianomic's official FogLAMP plugin repository
            - Results are filtered by OS and architecture compatibility
            - Large result sets may take several seconds to retrieve
            - include_details=True significantly increases response time
        """
        _logger.info(
            f"Triggering `tool:discover_plugins` with {plugin_type=}, "
            f"{search_term=}, {os_type=}, {architecture=}, {repository_url=}, "
            f"{include_details=}, {sort_by=}."
        )
        # Convert empty strings to None for optional parameters
        plugin_type_param = plugin_type if plugin_type else None
        search_term_param = search_term if search_term else None
        
        return FogLAMPPlugin.list_foglamp_plugins(
            plugin_type_param, search_term_param, os_type, architecture, repository_url,
            include_details, sort_by
        )

    @mcp_server.tool()
    def get_platform_info() -> Dict[str, Any]:
        """Detect the current platform (Ubuntu/Raspberry Pi).

        Automatically identifies the system platform and provides platform-specific
        information for proper plugin installation and configuration. Essential for
        determining the correct package repository and architecture for FogLAMP plugins.

        Examples:
            LLM Input Examples:
                - "What platform am I running on"
                - "Detect my system platform"
                - "Check if this is Raspberry Pi or Ubuntu"
                - "What's my system architecture and OS version?"

            Function Call Examples:
                - detect_platform()

        Args:
            None: This function requires no parameters

        Returns:
            Dict[str, Any]: Platform information containing:
                - status (str): "success" or "failed"
                - platform_info (dict): Detailed system information including:
                    - system (str): Operating system name
                    - release (str): OS release version
                    - machine (str): Machine architecture
                    - processor (str): CPU processor information
                    - platform (str): "raspberry_pi", "ubuntu", or "unknown"
                    - model (str): Specific model information
                    - os_version (str): OS version number
                    - os_codename (str): OS codename
                    - recommended_platform (str): Suggested platform string for plugins

        Errors:
            - OSError: When system information cannot be retrieved
            - FileNotFoundError: When /proc/cpuinfo is not accessible
            - subprocess.CalledProcessError: When lsb_release command fails

        Notes:
            - Reads /proc/cpuinfo to detect Raspberry Pi hardware
            - Uses lsb_release command for Ubuntu version detection
            - Provides recommended platform string for plugin installation
            - Supports Ubuntu 22.04, 24.04 and Raspberry Pi Bookworm
        """
        _logger.info(f"Triggering `tool:get_platform_info`.")
        return FogLAMPPlugin.detect_platform()

    @mcp_server.tool()
    def install_plugin_package(
        package_name: str,
        version: str = "",
        platform: str = "ubuntu2404"
    ) -> Dict[str, Any]:
        """Install a FogLAMP package from the repository.

        Downloads and installs FogLAMP plugins/packages from the Dianomic repository
        using the system's package manager. Validates package availability, checks
        existing installations, and handles platform-specific dependencies.

        Examples:
            LLM Input Examples:
                - "Install sinusoid south plugin"
                - "Install PI Server north plugin version 3.1.0"
                - "Install change detection filter on Raspberry Pi"
                - "Add the OMF north plugin to my system"

            Function Call Examples:
                - install_foglamp_package(package_name="foglamp-south-sinusoid")
                - install_foglamp_package(package_name="foglamp-north-omf", version="3.1.0")
                - install_foglamp_package(package_name="foglamp-filter-change", platform="rpi-bookworm")

        Args:
            package_name (str): Full package name (e.g., foglamp-south-sinusoid, foglamp-north-omf).
                               Must start with "foglamp-" prefix
            version (str, optional): Specific version to install.
                                   If not specified, installs the latest available version
            platform (str): Platform type for package compatibility.
                           Options: "ubuntu2404", "ubuntu2204", "rpi-bookworm"
                           Default: "ubuntu2404"

        Returns:
            Dict[str, Any]: Installation result containing:
                - status (str): "success", "failed", "already_installed", "not_found", "not_available"
                - message (str): Human-readable result message
                - version (str): Installed version (if successful)
                - platform (str): Target platform used
                - architecture (str): System architecture detected

        Errors:
            - ValueError: When package name doesn't start with "foglamp-"
            - ConnectionError: When repository is unreachable
            - subprocess.TimeoutExpired: When installation times out (5 minutes)
            - subprocess.CalledProcessError: When apt installation fails
            - FileNotFoundError: When package not found in repository

        Notes:
            - Uses apt package manager (works on both Ubuntu and Raspberry Pi)
            - Downloads .deb package to /tmp before installation
            - Automatically cleans up downloaded files after installation
            - Checks for existing installations to avoid duplicates
            - Validates package availability before attempting installation
            - Installation timeout is 5 minutes
        """
        _logger.info(f"Triggering `tool:install_plugin_package` with {package_name=}, {version=}, {platform=}.")
        # Convert empty string to None for optional parameter
        version_param = version if version else None
        return FogLAMPPlugin.install_foglamp_package(package_name, version_param, platform)

    @mcp_server.tool()
    def list_installed_packages() -> Dict[str, Any]:
        """Check for installed FogLAMP packages on Ubuntu/Raspberry Pi.

        Scans the system for installed FogLAMP packages using both dpkg (for .deb packages)
        and pip (for Python packages). Provides comprehensive inventory of all FogLAMP
        components currently installed on the system.

        Examples:
            LLM Input Examples:
                - "What FogLAMP packages are installed"
                - "Check installed plugins"
                - "List installed FogLAMP packages"
                - "Show me all FogLAMP components on this system"

            Function Call Examples:
                - check_installed_packages()

        Args:
            None: This function requires no parameters

        Returns:
            Dict[str, Any]: List of installed FogLAMP packages containing:
                - status (str): "success" or "failed"
                - package_manager (str): "dpkg/pip" indicating package sources
                - packages (list): List of installed packages with details:
                    - package_name (str): Full package name
                    - version (str): Installed version
                    - architecture (str): Package architecture or "python"
                    - description (str): Package description
                - total_count (int): Total number of installed packages

        Errors:
            - subprocess.CalledProcessError: When dpkg or pip commands fail
            - OSError: When system commands cannot be executed
            - Exception: When unexpected errors occur during scanning

        Notes:
            - Checks both system packages (dpkg) and Python packages (pip)
            - Parses dpkg output format: "ii package_name version arch description"
            - Parses pip output format: "package_name version"
            - Returns empty list if no FogLAMP packages found
            - Works on both Ubuntu and Raspberry Pi systems
        """
        _logger.info(f"Triggering `tool:list_installed_packages`.")
        return FogLAMPPlugin.check_installed_packages()
