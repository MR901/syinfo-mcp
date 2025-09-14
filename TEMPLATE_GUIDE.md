# MCP Server Template Guide

This codebase serves as a comprehensive template for building Model Context Protocol (MCP) servers. It provides a production-ready foundation with reusable components that can be adapted for different domains and use cases.

## 🏗️ Architecture Overview

```
src/
├── common/           # Reusable core components
│   ├── app_manager.py      # aiohttp server management
│   ├── config_manager.py   # Configuration management
│   ├── databases.py        # Database abstraction layer
│   ├── http_client.py      # HTTP/HTTPS client
│   ├── plugins.py          # Plugin management system
│   ├── service_registry.py # Service discovery/registration
│   ├── syslogs.py          # System log integration
│   └── utils.py            # Common utilities
├── tools/            # MCP tools implementation
├── resources/        # MCP resources implementation  
├── prompts/          # MCP prompts implementation
└── mcp_server.py     # Main server entry point
```

## 🔧 Core Reusable Components

### 1. Database System (`common/databases.py`)
**Production-ready database layer with:**
- Connection pooling and retry logic
- Multi-database support (SQLite, PostgreSQL)
- Query validation and security
- Health monitoring
- Abstract base classes for extensibility

**Usage in your domain:**
```python
from src.common.databases import DatabaseFactory, DatabaseConnectionInfo

# Configure for your database
db_info = DatabaseConnectionInfo(
    plugin="postgres",
    database="your_app_db",
    host="localhost",
    port=5432,
    user="your_user",
    password="your_password"
)

pool = DatabaseFactory.get_pool(db_info)
result = pool.execute_query("SELECT * FROM your_table LIMIT 10")
```

### 2. Configuration Management (`common/config_manager.py`)
**Type-safe configuration with environment support:**
```python
from src.common.config_manager import ConfigManager
import os
from dataclasses import dataclass

# Define your app's config
@dataclass
class YourAppConfig:
    app_name: str = "Your MCP Server"
    api_host: str = os.getenv("API_HOST", "localhost")
    api_port: int = int(os.getenv("API_PORT", "8080"))
    debug_mode: bool = False

# Use the config manager pattern
config_manager = ConfigManager()
# Adapt parsing logic for your config format
```

### 3. HTTP Client (`common/http_client.py`)
**Production HTTP client with auth, SSL, timeouts:**
```python
from src.common.http_client import HTTPClient

client = HTTPClient("api.yourdomain.com", 443, 
                   auth_token="your-token", is_tls_enabled=True)
success, data = client.make_request("GET", "/api/v1/data")
```

### 4. MCP Server Core (`mcp_server.py`)
**Structured MCP server initialization:**
- Capability registration system
- Transport configuration (HTTP/stdio)  
- Logging and error handling
- Modular component loading

## 🎯 Adapting to Your Domain

### Step 1: Update Configuration
1. Modify `MCPConfig` dataclass in `config_manager.py`
2. Update `DEFAULT_CONFIG` dictionary for your app's settings
3. Change environment variable names and defaults

### Step 2: Replace Domain Logic
1. **Tools** (`tools/`): Replace with your domain's operations
2. **Resources** (`resources/`): Replace with your API/data endpoints  
3. **Prompts** (`prompts/`): Update for your LLM use cases

### Step 3: Update References
1. Search and replace domain-specific imports
2. Update server name and descriptions
3. Modify Docker and deployment configurations

### Step 4: Add Your Integrations
1. Extend database models for your schema
2. Add authentication/authorization as needed
3. Implement your specific business logic

## 📁 Template Usage Examples

### Example 1: E-commerce MCP Server
```python
# tools/ecommerce_tools.py
@mcp_server.tool()
def get_product_inventory(product_id: str) -> Dict[str, Any]:
    """Get real-time inventory for a product."""
    # Your e-commerce logic here
    
# resources/ecommerce_resources.py
@mcp_server.resource("resource://ecommerce/orders/{order_id}")
def get_order_details(order_id: str) -> str:
    """Get order details and status."""
    # Your order management logic
```

### Example 2: DevOps Monitoring Server
```python
# tools/devops_tools.py  
@mcp_server.tool()
def check_service_health(service_name: str) -> Dict[str, Any]:
    """Check health of deployed services."""
    # Your monitoring logic

# resources/devops_resources.py
@mcp_server.resource("resource://devops/deployments")
def get_deployment_status() -> str:
    """Get current deployment status across environments."""
    # Your deployment status logic
```

## 🚀 Quick Start

1. **Clone this template**
2. **Update `requirements.txt`** with your specific dependencies
3. **Modify `src/common/config_manager.py`** for your configuration
4. **Replace tools/resources/prompts** with your domain logic
5. **Update `mcp_server.py`** server name and initialization
6. **Test with `python -m src.mcp_server`**

## 🔗 Inter-component Linking

The template promotes clean interlinking through:

- **Configuration injection** - All components receive config objects
- **Dependency injection** - HTTP clients, DB pools passed to components
- **Event system** - Components can emit/listen to events
- **Registry pattern** - Central registration of tools/resources/prompts
- **Factory pattern** - Database and service factories for clean instantiation

## 🐳 Deployment

### Docker Support
```dockerfile
FROM python:3.10-slim
COPY requirements.txt .
RUN pip install -r requirements.txt  
COPY src/ ./src/
CMD ["python", "-m", "src.mcp_server"]
```

### Environment Configuration
```bash
# .env file
APP_NAME="Your MCP Server"
API_HOST=localhost
API_PORT=8080
LOG_LEVEL=INFO
DATABASE_URL=postgresql://user:pass@localhost/dbname
```

## 📚 Additional Resources

- [MCP Specification](https://modelcontextprotocol.io/docs)
- [FastMCP Documentation](https://github.com/jlowin/fastmcp)
- Template examples in `examples/` directory (to be created)

---

**This template provides production-ready patterns while remaining flexible enough to adapt to any domain. Focus on replacing domain-specific logic while leveraging the robust infrastructure components.**
