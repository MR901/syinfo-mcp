
import os
import sys
import logging
from typing import Union, Dict, List, Any, Optional

# Prefer PYTHONPATH; add project 'python' root as a fallback relative to this file
_here = os.path.dirname(__file__)
_python_root = os.path.abspath(os.path.join(_here, "..", "..", "..", ".."))
if _python_root not in sys.path:
    sys.path.append(_python_root)

from tabulate import tabulate
from mcp.server.fastmcp import FastMCP

try:
    from foglamp.common import logger
    _logger = logger.setup(__name__, level=logging.INFO)
except:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    _logger = logging.getLogger(__name__)
    _logger.warning("The execution is being performed outside FogLAMP.")

__author__ = "Mohit Rajput"
__copyright__ = "Copyright (c) 2025 Dianomic Systems Inc."
__license__ = "Apache 2.0"
__version__ = "${VERSION}"


USE_COLORS = True
RESET = "\033[0m"
CYAN = "\033[36m"
MAGENTA = "\033[35m"
YELLOW = "\033[33m"
INDENT = "    "


class MCPServer:

    def __init__(
        self, transport_route="streamable-http", stateless_http=True,
        host="0.0.0.0", port=8000, log_level="INFO", debug=False,
        http_client=None, capabilities_config: Dict[str, Any]=None
    ):
        """

        transport_route: options: "streamable-http", "stdio"
        """
        self.http_client = http_client

        # Create MCP server instance
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

        self.mcp_server = None
        self.mcp_registered_tools = []
        self.mcp_registered_static_resources = []
        self.mcp_registered_template_resources = []
        self.mcp_registered_prompts = []
        self.capabilities_config = capabilities_config

    def _log_mcp_summary(self):
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

        # Build pivot rows
        max_len = max(len(tools), len(static_resources), len(template_resources), len(prompts))
        rows = []
        for i in range(max_len):
            rows.append([
                tools[i] if i < len(tools) else "",
                static_resources[i] if i < len(static_resources) else "",
                template_resources[i] if i < len(template_resources) else "",
                prompts[i] if i < len(prompts) else ""
            ])

        # Create table with fancy_grid style (header separator as =)
        table_str = tabulate(
            rows,
            headers=[
                tools_header, static_resources_header,
                template_resources_header, prompts_header
            ],
            tablefmt="fancy_grid"  # Shows = separator under headers
        )

        # Add indentation to every line
        table_str = (
            "Registered capabilities in MCP server.\n" +
            "\n".join(INDENT + line for line in table_str.splitlines())
        )

        _logger.info("\n" + table_str)

    def _register_capabilities(self, capabilities_config):
        """Register tools, resources, and prompts with the MCP server."""
        _error = False

        # Import and register the capabilities
        try:
            from foglamp.services.mcp.src.tools.setup_and_syslog_tools import register_tools
            register_tools(self.mcp_server, self.http_client, config=capabilities_config)
            
            from foglamp.services.mcp.src.tools.foglamp_api_tools import register_tools
            register_tools(self.mcp_server, self.http_client, config=capabilities_config)

            from foglamp.services.mcp.src.tools.foglamp_db_tools import register_tools
            register_tools(self.mcp_server, self.http_client, config=capabilities_config)
            
            self.mcp_registered_tools = self.mcp_server._tool_manager.list_tools()
            _logger.info("MCP tools registration complete.")

        except Exception as e:
            _msg = f"Failed to register MCP Tools: {e}"
            _logger.error(_msg)
            _error = True

        try:
            from foglamp.services.mcp.src.resources.resources import register_resources
            register_resources(self.mcp_server, self.http_client, config=capabilities_config)
            self.mcp_registered_static_resources = self.mcp_server._resource_manager.list_resources()
            self.mcp_registered_template_resources = self.mcp_server._resource_manager._templates

            _logger.info("MCP resources registration complete.")

        except Exception as e:
            _msg = f"Failed to register MCP Resources: {e}"
            _logger.error(_msg)
            _error = True

        try:
            from foglamp.services.mcp.src.prompts.prompts import register_prompts
            register_prompts(self.mcp_server, config=capabilities_config)
            
            # Register dedicated Datalink Expert for Excel exports
            from foglamp.services.mcp.src.prompts.prompt_datalink_excel_exporter import register_datalink_expert
            register_datalink_expert(self.mcp_server, config=capabilities_config)
            
            self.mcp_registered_prompts = self.mcp_server._prompt_manager.list_prompts()
            _logger.info("MCP prompts registration complete.")

        except Exception as e:
            _msg = f"Failed to register MCP Prompts: {e}"
            _logger.error(_msg)
            _error = True

        if _error:
            raise Exception("Error/s observed during MCP capabilities registration.")

    def setup_mcp_server_and_capabilities(self):
        """Setup and start the MCP server."""
        # Initialize MCP server
        _logger.info("=" * 60)
        _logger.info(f"MCP FastMCP version: `{FastMCP.__module__}`")
        _logger.info(f"Python version: `{sys.version}`")

        if ((sys.version_info.major <= 3) and (sys.version_info.minor < 10)):
            raise Exception(
                "Python less than 3.10 are not supported with MCP server. "
                f"Current python version: {sys.version}"
            )
        try:
            self.mcp_server = FastMCP(
                "FogLAMP MCP Server",
                instructions="This server allows fetching information related to FogLAMP instance.",
                **self.server_args
            )
        except Exception as e:
            _msg = f"Failed to setup MCP server: {e}"
            _logger.error(_msg)
            raise Exception(_msg)

        # Register tools, resources, and prompts
        try:
            self._register_capabilities(self.capabilities_config)
        except Exception as e:
            _msg = f"Error: Failed to register mcp capabilities. {e} Continuing ..."
            _logger.error(_msg)
        finally:
            self._log_mcp_summary()

    def run(self):
        """Run server with either `streamable-http` or `stdio` transport."""
        _logger.info(f"Starting MCP Server with `{self.transport_route}` transport ...")
        if self.transport_route == "streamable-http":
            _logger.info(f"Server will be available at `{self.host}:{self.port}`")

        self.mcp_server.run(transport=self.transport_route)
        _logger.info("Server stopped.")


if __name__ == "__main__":
    """Main entry point if we want to have standalone execution."""
    try:
        # Import ConfigManager for standalone testing
        from foglamp.services.mcp.common.config_manager import ConfigManager
        
        # Create a config object for standalone testing
        config_manager = ConfigManager()
        # config_manager.set_foglamp_connection()
        # config_manager.set_auth_token()
        config_manager.parse_foglamp_config()
        config = config_manager._config

        _msg = "\n" + "="*60 + "\n"
        _msg += "Starting FogLAMP MCP Server with following configurations.\n"
        _msg += "\n" + "-"*60
        _msg += "\n\t FogLAMP Connection\n" + "."*60 + "\n"
        _msg += f"\t foglamp_host           = {config.foglamp_host}\n"
        _msg += f"\t foglamp_port           = {config.foglamp_port}\n"
        _msg += f"\t foglamp_protocol       = {config.foglamp_protocol}\n"
        _msg += f"\t foglamp_authenticated  = {config.foglamp_authenticated}\n"
        _msg += f"\t auth_token             = {config.auth_token}\n"
        _msg += "-"*60 + "\n\t MCP transport\n" + "."*60 + "\n"
        _msg += f"\t mcp_transport_route    = {config.mcp_transport_route}\n"
        _msg += f"\t mcp_stateless_http     = {config.mcp_stateless_http}\n"
        _msg += f"\t mcp_host               = {config.mcp_host}\n"
        _msg += f"\t mcp_port               = {config.mcp_port}\n"
        _msg += f"\t mcp_log_level          = {config.mcp_log_level}\n"
        _msg += f"\t mcp_debug              = {config.mcp_debug}\n"
        _msg += "-"*60 + "\n\t Permission\n" + "."*60 + "\n"
        _msg += f"\t allow_read_access      = {config.allow_read_access}\n"
        _msg += f"\t allow_write_access     = {config.allow_write_access}\n"
        _msg += f"\t allow_delete_access    = {config.allow_delete_access}\n"
        _msg += f"\t allow_direct_db_access = {config.allow_direct_db_access}\n"
        _msg += "-"*60 + "\n"
        _msg += "="*60 + "\n"
        _logger.info(_msg)
        
        server = MCPServer(
            transport_route=config.mcp_transport_route,
            stateless_http=config.mcp_stateless_http,
            host=config.mcp_host,
            port=config.mcp_port,
            log_level=config.mcp_log_level,
            debug=config.mcp_debug,
            http_client=None,
            capabilities_config={
                "allow_read_access": config.allow_read_access,
                "allow_write_access": config.allow_write_access,
                "allow_delete_access": config.allow_delete_access,
                "allow_direct_db_access": config.allow_direct_db_access
            }
        )
        server.setup_mcp_server_and_capabilities()
        server.run()

    except KeyboardInterrupt:
        _logger.info("Server stopped by user.")
    except Exception as e:
        _logger.error(f"Server error: {e}")
