# MCP Server Template

A production-ready, configurable template for building Model Context Protocol (MCP) servers. This template provides a robust foundation with reusable components that can be adapted for any domain while maintaining production-grade infrastructure.

## 🌟 Features

### 🏗️ Production-Ready Infrastructure
- **Database Layer**: Connection pooling, retry logic, multi-database support (SQLite, PostgreSQL)
- **HTTP Client**: Production HTTP/HTTPS client with auth, SSL, timeouts
- **Configuration**: Type-safe config with environment variable support
- **Logging**: Comprehensive logging with configurable levels
- **Error Handling**: Robust error handling and recovery mechanisms

### 🔧 Template Architecture
- **Modular Design**: Clean separation of tools, resources, prompts
- **Domain Adaptable**: Easy customization for different use cases
- **Configurable Capabilities**: Enable/disable features as needed
- **Inter-component Linking**: Clean dependency injection and service registry
- **Development Ready**: DevContainer, testing, linting, formatting

### 📦 Reusable Components
- **Server Core**: FastMCP-based server with transport configuration
- **Database Abstraction**: Production database layer with health monitoring  
- **System Integration**: Syslog querying, platform detection, utilities
- **Plugin System**: Extensible plugin architecture for domain-specific logic

## 🚀 Quick Start

### 1. Clone and Setup
```bash
git clone <this-repo>
cd syinfo-mcp

# Option A: Use DevContainer (Recommended)
# Open in VS Code with DevContainer extension

# Option B: Local Setup
pip install -r requirements.txt
```

### 2. Run Template Server
```bash
# Run with defaults
python -m src.template_server

# Run with custom configuration
MCP_SERVER_NAME="My Custom Server" python -m src.template_server

# Run e-commerce example
python examples/ecommerce_server.py
```

### 3. Test the Server
```bash
# Check server health
python health_check.py

# Run tests
make test

# Check code quality
make lint
```

## 📁 Project Structure

```
syinfo-mcp/
├── src/
│   ├── common/           # 🏗️ Reusable infrastructure components
│   │   ├── app_manager.py      # aiohttp server management
│   │   ├── config_manager.py   # Original FogLAMP config (preserved)
│   │   ├── template_config.py  # 🆕 Generic template config system
│   │   ├── databases.py        # Production database layer
│   │   ├── http_client.py      # HTTP/HTTPS client
│   │   ├── plugins.py          # Plugin management
│   │   ├── service_registry.py # Service discovery
│   │   ├── syslogs.py          # System log integration
│   │   └── utils.py            # Common utilities
│   ├── tools/            # 🔧 MCP tools implementation
│   ├── resources/        # 📊 MCP resources implementation  
│   ├── prompts/          # 🤖 MCP prompts implementation
│   ├── mcp_server.py     # 🏠 Original FogLAMP server (preserved)
│   └── template_server.py # 🆕 Generic template server
├── examples/             # 📚 Domain-specific examples
│   └── ecommerce_server.py   # E-commerce MCP server example
├── .devcontainer/        # 🐳 Development container config
├── tests/                # 🧪 Test suite
├── TEMPLATE_GUIDE.md     # 📖 Comprehensive template guide
└── README.md             # This file
```

## 🎯 Template Usage

### For New Domains

1. **Copy the template structure**
2. **Define your configuration** (extend `ServerConfig`)
3. **Implement domain logic** (tools, resources, prompts)
4. **Configure capabilities** (enable/disable features)
5. **Customize and deploy**

### Example: Custom Domain Server

```python
from src.template_server import TemplateMCPServer, ServerCapabilities
from src.common.template_config import ServerConfig
from dataclasses import dataclass

# 1. Define domain-specific configuration
@dataclass
class MyDomainConfig(ServerConfig):
    server_name: str = "My Domain MCP Server"
    my_api_endpoint: str = "https://api.mydomain.com"
    enable_my_feature: bool = True

# 2. Register domain capabilities
def register_my_capabilities(mcp_server, http_client, config):
    @mcp_server.tool()
    def my_domain_tool(param: str) -> dict:
        """My domain-specific tool."""
        return {"result": f"Processed {param}"}
    
    @mcp_server.resource("resource://mydomain/data")
    def get_my_data() -> str:
        """My domain data resource."""
        return "# My Domain Data\n\nThis is my domain-specific data."

# 3. Create and run server
server = TemplateMCPServer(
    server_name="My Domain MCP Server",
    custom_registration_fn=register_my_capabilities
)
server.setup_mcp_server_and_capabilities()
server.run()
```

## 🔗 Component Interlinking

The template promotes clean interlinking through:

### 1. Configuration Injection
All components receive configuration objects, enabling consistent behavior across the system.

```python
from src.common.template_config import TemplateConfigManager

config_manager = TemplateConfigManager()
server_config = config_manager.load_server_config()
capabilities_config = config_manager.load_capabilities_config()
```

### 2. Dependency Injection
HTTP clients, database pools, and other services are injected into components.

```python
from src.common.http_client import HTTPClient
from src.common.databases import DatabaseFactory

# Create shared services
http_client = HTTPClient(config.api_host, config.api_port)
db_pool = DatabaseFactory.get_pool(db_config)

# Inject into capabilities
register_capabilities(mcp_server, http_client, config)
```

### 3. Service Registry
Central registration system for tools, resources, and prompts.

```python
# Automatic discovery and registration
capabilities = ServerCapabilities(
    tools_modules=["my_domain.tools"],
    resources_modules=["my_domain.resources"],
    prompts_modules=["my_domain.prompts"]
)
```

### 4. Event System
Components can emit and listen to events for loose coupling.

```python
# Example: Database health monitoring affects all components
db_pool.on_health_change(lambda healthy: update_all_components(healthy))
```

## 📚 Examples

### 1. E-commerce Server (`examples/ecommerce_server.py`)
Complete e-commerce MCP server with:
- **Tools**: Inventory management, order processing, analytics
- **Resources**: Product catalog, order history, dashboards
- **Prompts**: Customer service, inventory management, sales analysis

```bash
python examples/ecommerce_server.py
```

### 2. Original FogLAMP Server (Preserved)
The original functionality is preserved in `src/mcp_server.py`:

```bash
python -m src.mcp_server
```

### 3. Generic Template Server
Minimal template with example capabilities:

```bash
python -m src.template_server
```

## ⚙️ Configuration

### Environment Variables
```bash
# Server Configuration
MCP_SERVER_NAME="My Custom MCP Server"
MCP_HOST=0.0.0.0
MCP_PORT=8000
MCP_DEBUG=true

# External Services
MCP_EXTERNAL_API_HOST=api.example.com
MCP_EXTERNAL_API_AUTH_TOKEN=your-token

# Database (optional)
MCP_DATABASE_ENABLED=true
MCP_DATABASE_TYPE=postgresql
MCP_DATABASE_HOST=localhost
```

### Configuration Files
```json
{
  "server_name": "My MCP Server",
  "mcp_port": 8000,
  "allow_read_access": true,
  "database_enabled": true,
  "custom_config": {
    "my_feature_enabled": true
  }
}
```

## 🧪 Development

### DevContainer Setup
```bash
# Open in VS Code with DevContainer extension
# All dependencies and tools are automatically configured
```

### Local Development
```bash
# Install dependencies
make install dev

# Run tests
make test

# Code quality
make lint format

# Run server
make run-template
```

### Testing
```bash
# Run all tests
pytest tests/ -v --cov=src

# Test specific component
pytest tests/test_template.py -v

# Integration tests
python health_check.py
```

## 🐳 Deployment

### Docker
```bash
# Build image
make docker-build

# Run container
make docker-run

# With custom config
docker run -e MCP_SERVER_NAME="Production Server" -p 8000:8000 mcp-server-template
```

### Production Deployment
1. **Configure environment variables** for your domain
2. **Set up external services** (database, APIs)
3. **Enable production logging** and monitoring
4. **Configure security** (authentication, authorization)
5. **Deploy with container orchestration** (Kubernetes, Docker Compose)

## 📖 Documentation

- **[Template Guide](TEMPLATE_GUIDE.md)**: Comprehensive adaptation guide
- **[MCP Specification](https://modelcontextprotocol.io/)**: Official MCP documentation
- **[FastMCP Documentation](https://github.com/jlowin/fastmcp)**: FastMCP framework docs

## 🤝 Contributing

1. **Fork the repository**
2. **Create a feature branch** (`git checkout -b feature/amazing-feature`)
3. **Make changes and add tests**
4. **Run code quality checks** (`make lint test`)
5. **Commit changes** (`git commit -m 'Add amazing feature'`)
6. **Push to branch** (`git push origin feature/amazing-feature`)
7. **Open a Pull Request**

## 📝 License

This project is licensed under the Apache 2.0 License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **FogLAMP Project**: Original codebase foundation
- **MCP Team**: Model Context Protocol specification
- **FastMCP**: Excellent MCP server framework
- **Community Contributors**: Thank you for your contributions!

---

## 🎯 What Makes This Template Special

### ✅ **Preserves Original Functionality**
- Original FogLAMP MCP server remains fully functional
- All existing features and capabilities maintained
- Backward compatibility ensured

### 🔧 **Maximum Reusability**  
- **Database layer**: Production-ready with connection pooling
- **HTTP client**: Robust with auth, SSL, error handling
- **Configuration system**: Type-safe with environment support
- **System integration**: Syslog, platform detection, utilities

### 🎨 **Easy Customization**
- **Modular architecture**: Replace only what you need
- **Configuration-driven**: Enable/disable features via config
- **Domain examples**: Complete working examples for different domains
- **Development ready**: DevContainer, testing, CI/CD ready

### 🚀 **Production Grade**
- **Error handling**: Comprehensive error recovery
- **Logging**: Configurable, structured logging
- **Health monitoring**: Database and service health checks
- **Security**: Query validation, permission systems
- **Performance**: Connection pooling, caching, optimization

**This template bridges the gap between a proof-of-concept and a production-ready MCP server, giving you the best of both worlds: robust infrastructure and easy customization.**
