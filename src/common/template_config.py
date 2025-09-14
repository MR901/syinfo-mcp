"""
Template Configuration Manager

Generic configuration system that can be adapted for any domain.
Provides type-safe configuration with environment variable support and validation.
"""

import os
import logging
from typing import Dict, Any, Optional, Type, TypeVar, Union
from dataclasses import dataclass, fields
from abc import ABC, abstractmethod

# Setup logging with fallback
try:
    # Try to use existing logger setup
    from src.common.config_manager import _logger
except ImportError:
    logging.basicConfig(level=logging.INFO)
    _logger = logging.getLogger(__name__)

__author__ = "Template Author"
__version__ = "1.0.0"

T = TypeVar('T')


@dataclass
class ServerConfig:
    """Core server configuration that applies to any MCP server."""
    
    # Server identity
    server_name: str = "Template MCP Server"
    server_description: str = "A configurable MCP server template"
    server_version: str = "1.0.0"
    
    # MCP transport configuration
    mcp_transport_route: str = "streamable-http"  # "streamable-http" or "stdio"
    mcp_stateless_http: bool = True
    mcp_host: str = "0.0.0.0"
    mcp_port: int = 8000
    mcp_log_level: str = "INFO"
    mcp_debug: bool = False
    
    # Security and permissions
    allow_read_access: bool = True
    allow_write_access: bool = False
    allow_delete_access: bool = False
    
    # External service configuration
    external_api_host: Optional[str] = None
    external_api_port: Optional[int] = None
    external_api_protocol: str = "https"
    external_api_auth_token: Optional[str] = None
    external_api_timeout: int = 30
    
    # Database configuration (optional)
    database_enabled: bool = False
    database_type: str = "sqlite"  # sqlite, postgres
    database_host: str = "localhost"
    database_port: Optional[int] = None
    database_name: str = "template_mcp.db"
    database_user: Optional[str] = None
    database_password: Optional[str] = None
    database_pool_size: int = 5


@dataclass  
class CapabilitiesConfig:
    """Configuration for MCP capabilities (tools, resources, prompts)."""
    
    # Module paths for capabilities
    tools_modules: list = None
    resources_modules: list = None  
    prompts_modules: list = None
    
    # Feature flags
    enable_system_tools: bool = True
    enable_database_tools: bool = False
    enable_external_api_resources: bool = False
    enable_analysis_prompts: bool = True
    
    # Custom configuration for domain-specific logic
    custom_config: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.tools_modules is None:
            self.tools_modules = []
        if self.resources_modules is None:
            self.resources_modules = []
        if self.prompts_modules is None:
            self.prompts_modules = []
        if self.custom_config is None:
            self.custom_config = {}


class ConfigurationProvider(ABC):
    """Abstract base class for configuration providers."""
    
    @abstractmethod
    def load_config(self, config_class: Type[T]) -> T:
        """Load configuration of the specified type."""
        pass


class EnvironmentConfigProvider(ConfigurationProvider):
    """Load configuration from environment variables."""
    
    def __init__(self, prefix: str = "MCP_"):
        self.prefix = prefix
    
    def load_config(self, config_class: Type[T]) -> T:
        """Load configuration from environment variables with type conversion."""
        config_data = {}
        
        for field in fields(config_class):
            env_key = f"{self.prefix}{field.name.upper()}"
            env_value = os.getenv(env_key)
            
            if env_value is not None:
                # Type conversion based on field type
                try:
                    if field.type == bool:
                        config_data[field.name] = env_value.lower() in ("true", "1", "yes", "on")
                    elif field.type == int:
                        config_data[field.name] = int(env_value)
                    elif field.type == float:
                        config_data[field.name] = float(env_value)
                    elif field.type == str:
                        config_data[field.name] = env_value
                    elif hasattr(field.type, '__origin__') and field.type.__origin__ is list:
                        # Handle list types (comma-separated)
                        config_data[field.name] = [item.strip() for item in env_value.split(",")]
                    else:
                        config_data[field.name] = env_value
                        
                except (ValueError, TypeError) as e:
                    _logger.warning(f"Invalid environment variable {env_key}={env_value}: {e}")
        
        return config_class(**config_data)


class FileConfigProvider(ConfigurationProvider):
    """Load configuration from JSON/YAML file."""
    
    def __init__(self, config_file: str):
        self.config_file = config_file
    
    def load_config(self, config_class: Type[T]) -> T:
        """Load configuration from file."""
        try:
            import json
            
            if not os.path.exists(self.config_file):
                _logger.warning(f"Config file {self.config_file} not found, using defaults")
                return config_class()
            
            with open(self.config_file, 'r') as f:
                if self.config_file.endswith(('.yml', '.yaml')):
                    try:
                        import yaml
                        config_data = yaml.safe_load(f)
                    except ImportError:
                        raise ImportError("PyYAML required for YAML config files")
                else:
                    config_data = json.load(f)
            
            return config_class(**config_data)
            
        except Exception as e:
            _logger.error(f"Error loading config from {self.config_file}: {e}")
            return config_class()


class TemplateConfigManager:
    """
    Generic configuration manager for MCP server templates.
    
    Supports multiple configuration sources with precedence:
    1. Environment variables (highest priority)
    2. Configuration file 
    3. Default values (lowest priority)
    """
    
    def __init__(
        self,
        config_file: Optional[str] = None,
        env_prefix: str = "MCP_",
        server_config_class: Type = ServerConfig,
        capabilities_config_class: Type = CapabilitiesConfig
    ):
        self.config_file = config_file
        self.env_prefix = env_prefix
        self.server_config_class = server_config_class
        self.capabilities_config_class = capabilities_config_class
        
        # Configuration providers
        self.providers = []
        
        # Environment provider (highest priority)
        self.providers.append(EnvironmentConfigProvider(env_prefix))
        
        # File provider (if specified)  
        if config_file:
            self.providers.append(FileConfigProvider(config_file))
        
        # Loaded configurations
        self._server_config = None
        self._capabilities_config = None
    
    def load_server_config(self) -> ServerConfig:
        """Load server configuration from providers."""
        if self._server_config is None:
            # Start with defaults
            config = self.server_config_class()
            
            # Apply providers in reverse order (file first, then environment)
            for provider in reversed(self.providers):
                try:
                    provider_config = provider.load_config(self.server_config_class)
                    # Merge configurations (environment variables take precedence)
                    config = self._merge_configs(config, provider_config)
                except Exception as e:
                    _logger.warning(f"Error loading config from {provider.__class__.__name__}: {e}")
            
            self._server_config = config
            _logger.info("Server configuration loaded successfully")
        
        return self._server_config
    
    def load_capabilities_config(self) -> CapabilitiesConfig:
        """Load capabilities configuration from providers."""
        if self._capabilities_config is None:
            # Start with defaults
            config = self.capabilities_config_class()
            
            # Apply providers in reverse order
            for provider in reversed(self.providers):
                try:
                    provider_config = provider.load_config(self.capabilities_config_class)
                    config = self._merge_configs(config, provider_config)
                except Exception as e:
                    _logger.warning(f"Error loading capabilities config from {provider.__class__.__name__}: {e}")
            
            self._capabilities_config = config
            _logger.info("Capabilities configuration loaded successfully")
        
        return self._capabilities_config
    
    def _merge_configs(self, base_config: T, override_config: T) -> T:
        """Merge two configuration objects, with override taking precedence."""
        merged_data = {}
        
        # Start with base config
        for field in fields(base_config):
            merged_data[field.name] = getattr(base_config, field.name)
        
        # Override with non-default values from override config
        for field in fields(override_config):
            override_value = getattr(override_config, field.name)
            
            # Only override if the value is not the default
            default_value = field.default if field.default != field.default_factory else field.default_factory()
            
            if override_value != default_value:
                merged_data[field.name] = override_value
        
        return type(base_config)(**merged_data)
    
    def get_config_summary(self) -> Dict[str, Any]:
        """Get a summary of current configuration for logging/debugging."""
        server_config = self.load_server_config()
        capabilities_config = self.load_capabilities_config()
        
        return {
            "server": {
                "name": server_config.server_name,
                "version": server_config.server_version,
                "transport": {
                    "route": server_config.mcp_transport_route,
                    "host": server_config.mcp_host,
                    "port": server_config.mcp_port,
                    "stateless": server_config.mcp_stateless_http,
                },
                "logging": {
                    "level": server_config.mcp_log_level,
                    "debug": server_config.mcp_debug,
                },
                "permissions": {
                    "read": server_config.allow_read_access,
                    "write": server_config.allow_write_access,
                    "delete": server_config.allow_delete_access,
                }
            },
            "capabilities": {
                "tools_modules": len(capabilities_config.tools_modules),
                "resources_modules": len(capabilities_config.resources_modules),
                "prompts_modules": len(capabilities_config.prompts_modules),
                "features": {
                    "system_tools": capabilities_config.enable_system_tools,
                    "database_tools": capabilities_config.enable_database_tools,
                    "external_api_resources": capabilities_config.enable_external_api_resources,
                    "analysis_prompts": capabilities_config.enable_analysis_prompts,
                }
            },
            "external_services": {
                "api_host": server_config.external_api_host,
                "database_enabled": server_config.database_enabled,
                "database_type": server_config.database_type,
            }
        }


# Pre-configured domain examples

@dataclass
class EcommerceServerConfig(ServerConfig):
    """Configuration for an e-commerce MCP server."""
    
    server_name: str = "E-commerce MCP Server"
    server_description: str = "MCP server for e-commerce operations and analytics"
    
    # E-commerce specific settings
    store_api_host: str = "api.mystore.com"
    store_api_key: Optional[str] = None
    inventory_sync_interval: int = 300  # seconds
    enable_order_management: bool = True
    enable_inventory_tracking: bool = True
    enable_customer_analytics: bool = True


@dataclass
class DevOpsServerConfig(ServerConfig):
    """Configuration for a DevOps monitoring MCP server."""
    
    server_name: str = "DevOps MCP Server"
    server_description: str = "MCP server for DevOps monitoring and management"
    
    # DevOps specific settings
    kubernetes_endpoint: Optional[str] = None
    docker_socket: str = "/var/run/docker.sock"
    monitoring_interval: int = 60  # seconds
    enable_deployment_management: bool = True
    enable_container_monitoring: bool = True
    enable_log_aggregation: bool = True


@dataclass
class DataAnalysisServerConfig(ServerConfig):
    """Configuration for a data analysis MCP server."""
    
    server_name: str = "Data Analysis MCP Server"
    server_description: str = "MCP server for data analysis and machine learning operations"
    
    # Data analysis specific settings
    data_sources: list = None
    ml_model_path: Optional[str] = None
    enable_statistical_analysis: bool = True
    enable_ml_predictions: bool = False
    enable_data_visualization: bool = True
    max_dataset_size_mb: int = 100
    
    def __post_init__(self):
        if self.data_sources is None:
            self.data_sources = []


# Utility functions for quick setup

def create_template_config_manager(domain: str = "generic", config_file: Optional[str] = None) -> TemplateConfigManager:
    """Create a configuration manager for a specific domain."""
    
    domain_configs = {
        "ecommerce": (EcommerceServerConfig, CapabilitiesConfig),
        "devops": (DevOpsServerConfig, CapabilitiesConfig),  
        "data_analysis": (DataAnalysisServerConfig, CapabilitiesConfig),
        "generic": (ServerConfig, CapabilitiesConfig)
    }
    
    if domain not in domain_configs:
        _logger.warning(f"Unknown domain '{domain}', using generic configuration")
        domain = "generic"
    
    server_config_class, capabilities_config_class = domain_configs[domain]
    
    return TemplateConfigManager(
        config_file=config_file,
        server_config_class=server_config_class,
        capabilities_config_class=capabilities_config_class
    )


def load_config_from_env(domain: str = "generic") -> tuple:
    """Quick utility to load configuration from environment variables."""
    config_manager = create_template_config_manager(domain)
    server_config = config_manager.load_server_config()
    capabilities_config = config_manager.load_capabilities_config()
    return server_config, capabilities_config


if __name__ == "__main__":
    """Example usage and testing."""
    
    # Example 1: Generic template
    print("=== Generic Template Configuration ===")
    config_manager = create_template_config_manager("generic")
    server_config = config_manager.load_server_config()
    print(f"Server: {server_config.server_name}")
    print(f"Host:Port: {server_config.mcp_host}:{server_config.mcp_port}")
    
    # Example 2: E-commerce domain
    print("\n=== E-commerce Domain Configuration ===")
    ecommerce_manager = create_template_config_manager("ecommerce")
    ecommerce_config = ecommerce_manager.load_server_config()
    print(f"Server: {ecommerce_config.server_name}")
    print(f"Store API: {ecommerce_config.store_api_host}")
    
    # Example 3: Environment variable override
    print("\n=== Environment Variable Testing ===")
    os.environ["MCP_SERVER_NAME"] = "Test Server"
    os.environ["MCP_MCP_PORT"] = "9000"
    
    test_manager = create_template_config_manager("generic")
    test_config = test_manager.load_server_config()
    print(f"Overridden Server: {test_config.server_name}")
    print(f"Overridden Port: {test_config.mcp_port}")
    
    # Example 4: Configuration summary
    print("\n=== Configuration Summary ===")
    summary = test_manager.get_config_summary()
    import json
    print(json.dumps(summary, indent=2))
