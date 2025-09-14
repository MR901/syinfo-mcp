# -*- coding: utf-8 -*-

# FOGLAMP_BEGIN
# See: https://foglamp.dianomic.com
# FOGLAMP_END

"""
CONFIGURATION MANAGEMENT

Clean configuration management for the FogLAMP MCP Server.

Priority order:
    FogLAMP Config (high) > MCPConfig (the backbone config template)
    :: MCPConfig is passed around and FogLAMP config is used to overwrite this
"""

import os
import logging
from typing import Dict, Any, Optional
from dataclasses import dataclass

try:
    from foglamp.common import logger
    _logger = logger.setup(__name__, level=logging.INFO)
except:
    logging.basicConfig(level=logging.INFO)
    _logger = logging.getLogger(__name__)

# Get FogLAMP root directory
try:
    from foglamp.common.common import _FOGLAMP_ROOT
except ImportError:
    _FOGLAMP_ROOT = "/usr/local/foglamp"

__author__ = "Mohit Rajput"
__copyright__ = "Copyright (c) 2025 Dianomic Systems Inc."
__license__ = "Apache 2.0"
__version__ = "${VERSION}"


# ============================================================================
# ENVIRONMENT VARIABLES (for standalone mode only)
# ============================================================================
DEFAULT_FOGLAMP_HOST = os.getenv("FOGLAMP_HOST", "localhost")
DEFAULT_FOGLAMP_PORT = int(os.getenv("FOGLAMP_PORT", "8081"))
FOGLAMP_ROOT = os.getenv("FOGLAMP_ROOT", _FOGLAMP_ROOT)

# ============================================================================
# DEVELOPER CONSTANTS (not exposed to FogLAMP users)
# ============================================================================
MCP_TRANSPORT = os.getenv("MCP_TRANSPORT", "streamable-http")  # Options: "streamable-http", "stdio"
MCP_STATELESS_HTTP = True
MCP_HOST = os.getenv("MCP_HOST", "0.0.0.0")
MCP_PORT = int(os.getenv("MCP_PORT", "8000"))
MCP_DEBUG = False

# ============================================================================
# FOGLAMP CONFIGURATION (exposed to users)
# ============================================================================
_grp1 = "MCP Server"
_grp2 = "Permissions"


DEFAULT_CONFIG = {
    # ============================================================================
    # MCP SERVER CONFIGURATION
    # ============================================================================
    "mcp_host": {
        "order": "1",
        "group": _grp1,
        "displayName": "MCP Server Host",
        "description": "Host address for the MCP server to bind to",
        "type": "string",
        "default": MCP_HOST,
    },
    "mcp_port": {
        "order": "2",
        "group": _grp1,
        "displayName": "MCP Server Port",
        "description": "Port for the MCP server to listen on",
        "type": "integer",
        "default": MCP_PORT,
    },
    "log_level": {
        "order": "3",
        "group": _grp1,
        "displayName": "Log Level",
        "description": "Log level for diagnostic output",
        "type": "enumeration",
        "options": ["ERROR", "WARN", "INFO", "DEBUG"],
        "default": "INFO",
    },

    # ============================================================================
    # PERMISSION-BASED ACCESS CONTROL
    # ============================================================================
    "allow_read_access": {
        "order": "4",
        "group": _grp2,
        "displayName": "Allow Read Access",
        "description": "Allow read operations (GET requests) via MCP server",
        "type": "boolean",
        "default": "true",
    },
    "allow_write_access": {
        "order": "5",
        "group": _grp2,
        "displayName": "Allow Write Access",
        "description": "Allow write operations (PUT and POST requests) via MCP server",
        "type": "boolean",
        "default": "true",
    },
    "allow_delete_access": {
        "order": "6",
        "group": _grp2,
        "displayName": "Allow Delete Access",
        "description": "Allow delete operations (DELETE requests) via MCP server",
        "type": "boolean",
        "default": "false",
    },
    "allow_direct_db_access": {
        "order": "7",
        "group": _grp2,
        "displayName": "Enable Direct Database Access",
        "description": "Enable direct database connections for configdb and readingsdb (local device only; remote hosts not supported)",
        "type": "boolean",
        "default": "true",
    },
}


@dataclass 
class DatabaseConnectionInfo:
    """Database connection information for FogLAMP storage backends."""
    
    plugin: str = ""
    database: str = ""
    user: Optional[str] = None
    password: Optional[str] = None
    host: str = "localhost"
    port: Optional[int] = None
    schema: str = "foglamp"


@dataclass
class MCPConfig:
    """Configuration data class for MCP server settings."""

    # FogLAMP connection (from service registration)
    foglamp_host: Optional[str] = DEFAULT_FOGLAMP_HOST
    foglamp_port: Optional[int] = DEFAULT_FOGLAMP_PORT
    foglamp_protocol: str = "http"
    foglamp_authenticated: bool = False
    auth_token: Optional[str] = None

    # MCP Server settings
    mcp_transport_route: str = MCP_TRANSPORT
    mcp_stateless_http: bool = MCP_STATELESS_HTTP
    mcp_host: str = MCP_HOST
    mcp_port: int = MCP_PORT
    mcp_log_level: str = "INFO"
    mcp_debug: bool = MCP_DEBUG

    # Permission settings
    allow_read_access: bool = DEFAULT_CONFIG["allow_read_access"]["default"]
    allow_write_access: bool = DEFAULT_CONFIG["allow_write_access"]["default"]
    allow_delete_access: bool = DEFAULT_CONFIG["allow_delete_access"]["default"]
    allow_direct_db_access: bool = DEFAULT_CONFIG["allow_direct_db_access"]["default"]


class ConfigManager:
    """Simple configuration manager that provides the exact structure you want."""

    def __init__(self):
        """Initialize the configuration manager."""
        self._config = MCPConfig()

    def _parse_bool(self, value: Any) -> bool:
        """Parse boolean values from various formats."""
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            return value.lower() in ["true", "1", "yes", "on"]
        return bool(value)

    def parse_foglamp_config(self, raw_config: Dict[str, Any] = DEFAULT_CONFIG) -> None:
        """Parse FogLAMP configuration format.

        Args:
            raw_config: Raw configuration from FogLAMP
        """
        # FogLAMP connection (from service registration)
        try:
            for key, config_item in raw_config.items():
                if isinstance(config_item, dict) and "value" in config_item:
                    value = config_item["value"]

                    if key == "mcp_host":
                        self._config.mcp_host = str(value)
                    elif key == "mcp_port":
                        try:
                            self._config.mcp_port = int(value)
                        except (ValueError, TypeError):
                            _logger.warning(f"Invalid mcp_port value: {value}, using default")
                    elif key == "log_level":
                        self._config.mcp_log_level = str(value)
                    elif key == "allow_read_access":
                        self._config.allow_read_access = self._parse_bool(value)
                    elif key == "allow_write_access":
                        self._config.allow_write_access = self._parse_bool(value)
                    elif key == "allow_delete_access":
                        self._config.allow_delete_access = self._parse_bool(value)
                    elif key == "allow_direct_db_access":
                        self._config.allow_direct_db_access = self._parse_bool(value)

            _logger.info(f"Configuration parsed. Permissions: READ={self._config.allow_read_access}, WRITE={self._config.allow_write_access}, DELETE={self._config.allow_delete_access}, DB_ACCESS={self._config.allow_direct_db_access}")

        except Exception as e:
            _logger.error(f"Error parsing configuration: {e}. Using defaults.")

    def set_foglamp_connection(self, host: str, port: int, protocol: str = "http") -> None:
        """Set FogLAMP connection information from service registration.

        Args:
            host: FogLAMP host
            port: FogLAMP port
            protocol: FogLAMP protocol
        """
        self._config.foglamp_host = host
        self._config.foglamp_port = port
        self._config.foglamp_protocol = protocol

    def set_auth_token(self, auth_token: str) -> None:
        """Set authentication token from service registration.

        Args:
            auth_token: Authentication token
        """
        self._config.auth_token = auth_token

    def get_config_dict(self) -> Dict[str, Any]:
        """Get configuration as dict.

        Returns:
            Dict[str, Any]: Configuration summary
        """
        return {
            "foglamp_connection": {
                "host": self._config.foglamp_host,
                "port": self._config.foglamp_port,
                "protocol": self._config.foglamp_protocol,
                "authenticated": self._config.auth_token is not None
            },
            "mcp_server": {
                "transport_route": self._config.mcp_transport_route,
                "stateless_http": self._config.mcp_stateless_http,
                "host": self._config.mcp_host,
                "port": self._config.mcp_port,
                "log_level": self._config.mcp_log_level,
                "debug": self._config.mcp_debug
            },
            "permissions": {
                "read_access": self._config.allow_read_access,
                "write_access": self._config.allow_write_access,
                "delete_access": self._config.allow_delete_access,
                "database_access": self._config.allow_direct_db_access
            }
        }
