"""
Template MCP Server

A generic, configurable MCP server template that can be adapted for any domain.
This preserves the production-ready infrastructure while making domain logic configurable.

Usage:
    python -m src.template_server
"""

import os
import sys
import logging
from typing import Union, Dict, List, Any, Optional, Callable
from dataclasses import dataclass

# Add project root to path
_here = os.path.dirname(__file__)
_project_root = os.path.abspath(os.path.join(_here, ".."))
if _project_root not in sys.path:
    sys.path.append(_project_root)

from tabulate import tabulate
from mcp.server.fastmcp import FastMCP

# Template-friendly imports with fallback
try:
    # Try domain-specific logger (can be any logging system)
    from src.common.config_manager import ConfigManager
    _logger = logging.getLogger(__name__)
    _has_domain_logger = False
except ImportError:
    # Fallback to standard logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    _logger = logging.getLogger(__name__)
    _has_domain_logger = False

__author__ = "Template Author"
__version__ = "1.0.0"

# Template Configuration
USE_COLORS = True
RESET = "\033[0m"
CYAN = "\033[36m"
MAGENTA = "\033[35m"
YELLOW = "\033[33m"
INDENT = "    "


@dataclass
class ServerCapabilities:
    """Configuration for server capabilities (tools, resources, prompts)."""
    
    tools_modules: List[str]
    resources_modules: List[str]
    prompts_modules: List[str]
    
    @classmethod
    def default(cls):
        """Default capabilities configuration."""
        return cls(
            tools_modules=[
                "src.tools.setup_and_syslog_tools",  # System tools
            ],
            resources_modules=[
                "src.resources.resources",  # API resources
            ],
            prompts_modules=[
                "src.prompts.prompts",  # LLM prompts
            ]
        )
    
    @classmethod
    def empty(cls):
        """Empty capabilities for custom configuration."""
        return cls(
            tools_modules=[],
            resources_modules=[],
            prompts_modules=[]
        )


class TemplateMCPServer:
    """
    Template MCP Server with configurable capabilities.
    
    This class provides a production-ready MCP server foundation that can be
    customized for any domain by configuring capabilities and providing
    custom registration functions.
    """
    
    def __init__(
        self,
        server_name: str = "Template MCP Server",
        server_description: str = "A configurable MCP server template",
        transport_route: str = "streamable-http",
        stateless_http: bool = True,
        host: str = "0.0.0.0",
        port: int = 8000,
        log_level: str = "INFO",
        debug: bool = False,
        http_client: Optional[Any] = None,
        capabilities_config: Optional[Dict[str, Any]] = None,
        capabilities: Optional[ServerCapabilities] = None,
        custom_registration_fn: Optional[Callable] = None
    ):
        """
        Initialize the template MCP server.
        
        Args:
            server_name: Display name for the MCP server
            server_description: Server description for MCP clients
            transport_route: Transport method ("streamable-http" or "stdio")
            stateless_http: Whether to use stateless HTTP mode
            host: Host address to bind to
            port: Port to listen on
            log_level: Logging level
            debug: Enable debug mode
            http_client: HTTP client instance for external API calls
            capabilities_config: Configuration passed to capability modules
            capabilities: Server capabilities configuration
            custom_registration_fn: Custom function for registering capabilities
        """
        self.server_name = server_name
        self.server_description = server_description
        self.http_client = http_client
        
        # Server configuration
        self.transport_route = transport_route
        self.host = host
        self.port = int(port)
        
        if self.transport_route == "stdio":
            self.server_args = {}
        else:
            self.server_args = {
                "stateless_http": stateless_http,
                "host": self.host,
                "port": self.port,
                "log_level": log_level,
                "debug": debug,
            }
        
        # MCP server instance and registries
        self.mcp_server = None
        self.mcp_registered_tools = []
        self.mcp_registered_static_resources = []
        self.mcp_registered_template_resources = []
        self.mcp_registered_prompts = []
        
        # Configuration
        self.capabilities_config = capabilities_config or {}
        self.capabilities = capabilities or ServerCapabilities.default()
        self.custom_registration_fn = custom_registration_fn
    
    def _log_mcp_summary(self):
        """Log a formatted summary of registered MCP capabilities."""
        # Extract names
        tools = [e.name for e in self.mcp_registered_tools]
        static_resources = [e.name for e in self.mcp_registered_static_resources]
        template_resources = [e for e in self.mcp_registered_template_resources]
        prompts = [e.name for e in self.mcp_registered_prompts]
        
        # Header with counts and optional colors
        if USE_COLORS:
            tools_header = f"{CYAN}Tools ({len(tools)}){RESET}"
            static_resources_header = f"{MAGENTA}Resources [Static] ({len(static_resources)}){RESET}"
            template_resources_header = f"{MAGENTA}Resources [Template] ({len(template_resources)}){RESET}"
            prompts_header = f"{YELLOW}Prompts ({len(prompts)}){RESET}"
        else:
            tools_header = f"Tools ({len(tools)})"
            static_resources_header = f"Resources ({len(static_resources)})"
            template_resources_header = f"Resources2 ({len(template_resources)})"
            prompts_header = f"Prompts ({len(prompts)})"
        
        # Build pivot rows for table display
        max_len = max(len(tools), len(static_resources), len(template_resources), len(prompts))
        rows = []
        for i in range(max_len):
            rows.append([
                tools[i] if i < len(tools) else "",
                static_resources[i] if i < len(static_resources) else "",
                template_resources[i] if i < len(template_resources) else "",
                prompts[i] if i < len(prompts) else ""
            ])
        
        # Create formatted table
        table_str = tabulate(
            rows,
            headers=[
                tools_header, static_resources_header,
                template_resources_header, prompts_header
            ],
            tablefmt="fancy_grid"
        )
        
        # Add indentation to every line
        table_str = (
            f"Registered capabilities in {self.server_name}.\n" +
            "\n".join(INDENT + line for line in table_str.splitlines())
        )
        
        _logger.info("\n" + table_str)
    
    def _register_capabilities_from_modules(self):
        """Register capabilities from configured modules."""
        error_occurred = False
        
        # Register tools
        for module_path in self.capabilities.tools_modules:
            try:
                # Dynamic import with error handling
                module = self._import_module(module_path)
                if hasattr(module, 'register_tools'):
                    module.register_tools(
                        self.mcp_server, 
                        self.http_client, 
                        config=self.capabilities_config
                    )
                    _logger.info(f"Registered tools from {module_path}")
                else:
                    _logger.warning(f"Module {module_path} has no register_tools function")
            except Exception as e:
                _logger.error(f"Failed to register tools from {module_path}: {e}")
                error_occurred = True
        
        # Register resources  
        for module_path in self.capabilities.resources_modules:
            try:
                module = self._import_module(module_path)
                if hasattr(module, 'register_resources'):
                    module.register_resources(
                        self.mcp_server,
                        self.http_client,
                        config=self.capabilities_config
                    )
                    _logger.info(f"Registered resources from {module_path}")
                else:
                    _logger.warning(f"Module {module_path} has no register_resources function")
            except Exception as e:
                _logger.error(f"Failed to register resources from {module_path}: {e}")
                error_occurred = True
        
        # Register prompts
        for module_path in self.capabilities.prompts_modules:
            try:
                module = self._import_module(module_path)
                if hasattr(module, 'register_prompts'):
                    module.register_prompts(
                        self.mcp_server,
                        config=self.capabilities_config
                    )
                    _logger.info(f"Registered prompts from {module_path}")
                else:
                    _logger.warning(f"Module {module_path} has no register_prompts function")
            except Exception as e:
                _logger.error(f"Failed to register prompts from {module_path}: {e}")
                error_occurred = True
        
        # Update registries
        try:
            self.mcp_registered_tools = self.mcp_server._tool_manager.list_tools()
            self.mcp_registered_static_resources = self.mcp_server._resource_manager.list_resources()
            self.mcp_registered_template_resources = getattr(
                self.mcp_server._resource_manager, '_templates', []
            )
            self.mcp_registered_prompts = self.mcp_server._prompt_manager.list_prompts()
        except Exception as e:
            _logger.warning(f"Error updating capability registries: {e}")
        
        if error_occurred:
            _logger.warning("Some errors occurred during capability registration")
    
    def _import_module(self, module_path: str):
        """Safely import a module by path."""
        import importlib
        return importlib.import_module(module_path)
    
    def _register_custom_capabilities(self):
        """Register custom capabilities using provided function."""
        if self.custom_registration_fn:
            try:
                self.custom_registration_fn(
                    self.mcp_server,
                    self.http_client,
                    self.capabilities_config
                )
                _logger.info("Custom capabilities registered successfully")
            except Exception as e:
                _logger.error(f"Failed to register custom capabilities: {e}")
                raise
    
    def setup_mcp_server_and_capabilities(self):
        """Initialize the MCP server and register all capabilities."""
        # Log server info
        _logger.info("=" * 60)
        _logger.info(f"MCP FastMCP version: `{FastMCP.__module__}`")
        _logger.info(f"Python version: `{sys.version}`")
        _logger.info(f"Server name: {self.server_name}")
        
        # Python version check
        if sys.version_info < (3, 10):
            raise RuntimeError(
                f"Python 3.10+ required for MCP server. "
                f"Current version: {sys.version}"
            )
        
        # Initialize MCP server
        try:
            self.mcp_server = FastMCP(
                self.server_name,
                instructions=self.server_description,
                **self.server_args
            )
            _logger.info(f"MCP server '{self.server_name}' initialized successfully")
        except Exception as e:
            _logger.error(f"Failed to initialize MCP server: {e}")
            raise
        
        # Register capabilities
        try:
            if self.custom_registration_fn:
                self._register_custom_capabilities()
            else:
                self._register_capabilities_from_modules()
                
            _logger.info("MCP capabilities registration complete")
        except Exception as e:
            _logger.error(f"Failed to register MCP capabilities: {e}")
            # Don't raise - continue with partial capabilities
        finally:
            self._log_mcp_summary()
    
    def run(self):
        """Start the MCP server."""
        _logger.info(f"Starting {self.server_name} with `{self.transport_route}` transport...")
        if self.transport_route == "streamable-http":
            _logger.info(f"Server will be available at `{self.host}:{self.port}`")
        
        self.mcp_server.run(transport=self.transport_route)
        _logger.info("Server stopped.")


# Example custom registration function
def register_example_capabilities(mcp_server, http_client, config):
    """
    Example custom capability registration.
    
    This shows how to register capabilities directly without modules.
    """
    
    @mcp_server.tool()
    def example_tool(message: str = "Hello") -> str:
        """An example tool that echoes a message."""
        return f"Template server says: {message}"
    
    @mcp_server.resource("resource://template/info")
    def get_template_info() -> str:
        """Get information about this template server."""
        return f"""# Template Server Information

**Server Name:** Template MCP Server
**Version:** {__version__}
**Status:** Running
**Description:** This is an example template MCP server.

This server demonstrates how to create configurable MCP servers
that can be adapted for different domains and use cases.
"""
    
    @mcp_server.prompt()
    def get_template_prompt() -> str:
        """Get a template prompt for LLM interactions."""
        return """You are interacting with a template MCP server.

This server provides:
- Example tools for demonstration
- Template resources for information
- Configurable capabilities

You can use this template to build your own domain-specific MCP servers.
"""


def create_server_from_config() -> TemplateMCPServer:
    """Create server instance from configuration (environment or config file)."""
    
    # Try to load domain-specific configuration
    config_manager = None
    config = None
    
    try:
        # Attempt to load existing configuration system
        config_manager = ConfigManager()
        config_manager.parse_foglamp_config()  # This will use defaults if no FogLAMP config
        config = config_manager._config
        
        # Use existing configuration
        server = TemplateMCPServer(
            server_name=getattr(config, 'server_name', "Template MCP Server"),
            server_description="Template MCP server with configurable capabilities",
            transport_route=getattr(config, 'mcp_transport_route', "streamable-http"),
            stateless_http=getattr(config, 'mcp_stateless_http', True),
            host=getattr(config, 'mcp_host', "0.0.0.0"),
            port=getattr(config, 'mcp_port', 8000),
            log_level=getattr(config, 'mcp_log_level', "INFO"),
            debug=getattr(config, 'mcp_debug', False),
            capabilities_config={
                "allow_read_access": getattr(config, 'allow_read_access', True),
                "allow_write_access": getattr(config, 'allow_write_access', True),
                "allow_delete_access": getattr(config, 'allow_delete_access', False),
                "allow_direct_db_access": getattr(config, 'allow_direct_db_access', True)
            }
        )
        
        _logger.info("Server configured with existing configuration system")
        
    except Exception as e:
        _logger.info(f"Using default template configuration (could not load domain config: {e})")
        
        # Use template defaults with environment variable overrides
        server = TemplateMCPServer(
            server_name=os.getenv("MCP_SERVER_NAME", "Template MCP Server"),
            server_description=os.getenv("MCP_SERVER_DESCRIPTION", "A configurable MCP server template"),
            transport_route=os.getenv("MCP_TRANSPORT", "streamable-http"),
            stateless_http=os.getenv("MCP_STATELESS_HTTP", "true").lower() == "true",
            host=os.getenv("MCP_HOST", "0.0.0.0"),
            port=int(os.getenv("MCP_PORT", "8000")),
            log_level=os.getenv("MCP_LOG_LEVEL", "INFO"),
            debug=os.getenv("MCP_DEBUG", "false").lower() == "true",
            capabilities_config={
                "template_mode": True,
                "allow_read_access": True,
                "allow_write_access": False,
                "allow_delete_access": False
            },
            # Use example capabilities for template mode
            custom_registration_fn=register_example_capabilities
        )
        
        _logger.info("Server configured with template defaults")
    
    return server


if __name__ == "__main__":
    """Entry point for template server."""
    try:
        # Create and configure server
        server = create_server_from_config()
        
        # Setup and start
        server.setup_mcp_server_and_capabilities()
        server.run()
        
    except KeyboardInterrupt:
        _logger.info("Server stopped by user")
    except Exception as e:
        _logger.error(f"Server error: {e}")
        sys.exit(1)
