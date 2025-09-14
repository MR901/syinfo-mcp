# DevContainer Troubleshooting Guide

If you're experiencing issues with the DevContainer setup, try these solutions in order:

## 🔧 Solution 1: Use the Simplified DevContainer (Recommended)

I've already updated your `devcontainer.json` with a simplified configuration. Try reopening the container:

1. **Close VS Code**
2. **Delete any existing containers**: `docker system prune -a` (optional)
3. **Reopen VS Code** in the project folder
4. **Click "Reopen in Container"** when prompted

## 🔧 Solution 2: Use Minimal DevContainer

If the main configuration still fails, try the minimal version:

```bash
# Rename current config
mv .devcontainer/devcontainer.json .devcontainer/devcontainer.full.json

# Use minimal config
mv .devcontainer/devcontainer.minimal.json .devcontainer/devcontainer.json

# Restart VS Code and try container again
```

## 🔧 Solution 3: Manual Local Setup (Fastest)

Skip DevContainer entirely and set up locally:

```bash
# Install Python 3.10+ if not already installed
python --version  # Should be 3.10 or higher

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Install dev dependencies
pip install black isort flake8 pytest

# Test the setup
python -m src.template_server
```

## 🔧 Solution 4: Docker Issues

If you're having Docker-related issues:

### Check Docker Status
```bash
# Check if Docker is running
docker --version
docker info

# Test Docker functionality
docker run hello-world
```

### Docker Desktop Issues
1. **Restart Docker Desktop**
2. **Check available disk space** (Docker needs ~2GB for the container)
3. **Update Docker Desktop** to the latest version
4. **Reset Docker Desktop** if necessary (Settings → Troubleshoot → Reset to factory defaults)

### Docker Permission Issues (Linux)
```bash
# Add user to docker group
sudo usermod -aG docker $USER

# Log out and back in, then test
docker run hello-world
```

## 🔧 Solution 5: VS Code Issues

### Update Extensions
1. **Update VS Code** to the latest version
2. **Update DevContainer extension** (Dev Containers by Microsoft)
3. **Disable other extensions** temporarily to avoid conflicts

### Clear VS Code Cache
```bash
# Close VS Code completely
# Delete VS Code cache (adjust path for your OS)

# Linux/Mac:
rm -rf ~/.vscode/extensions/ms-vscode-remote.*

# Windows:
# Delete: %USERPROFILE%\.vscode\extensions\ms-vscode-remote.*
```

## 🔧 Solution 6: Network Issues

If you're behind a corporate firewall:

```bash
# Configure Docker to use proxy (if applicable)
# Add to ~/.docker/config.json:
{
  "proxies": {
    "default": {
      "httpProxy": "http://proxy.company.com:port",
      "httpsProxy": "http://proxy.company.com:port"
    }
  }
}
```

## 🔧 Solution 7: Alternative: Use GitHub Codespaces

If local setup continues to fail, use GitHub Codespaces:

1. **Push your code to GitHub** (if not already there)
2. **Go to your repository** on GitHub
3. **Click "Code" → "Codespaces" → "Create codespace"**
4. **Wait for environment to load** (uses the same devcontainer.json)

## 🔧 Solution 8: Quick Test Without Container

Test the MCP server directly to ensure the code works:

```bash
# Navigate to project directory
cd /home/mohit/Documents/new_age/syinfo/syinfo-mcp

# Set Python path
export PYTHONPATH=$(pwd)/src

# Install minimal requirements
pip install mcp aiohttp requests tabulate

# Test template server
python -m src.template_server

# Test original server (if preferred)
python -m src.mcp_server

# Test e-commerce example
python examples/ecommerce_server.py
```

## 🆘 Still Having Issues?

### Common Error Messages and Solutions

#### "Failed to run devcontainer command"
- **Solution**: Use Solution 2 (minimal config) or Solution 3 (local setup)

#### "docker buildx build" errors
- **Solution**: Update Docker Desktop or use minimal config without buildx features

#### "Permission denied" errors
- **Linux/Mac**: `sudo chown -R $USER:$USER .devcontainer`
- **Windows**: Run VS Code as administrator (not recommended for regular use)

#### "Port already in use"
- **Change port**: Edit `devcontainer.json` and change 8000 to 8001 or another port
- **Kill existing process**: `lsof -ti:8000 | xargs kill -9` (Linux/Mac)

### Get Help
1. **Check Docker logs**: `docker logs <container-id>`
2. **Check VS Code logs**: Help → Toggle Developer Tools → Console
3. **Create issue** with specific error messages and system info

## ✅ Verify Setup Works

Once you have a working environment (local or container), verify everything works:

```bash
# Check Python version
python --version

# Test imports
python -c "import mcp; import aiohttp; import requests; print('✅ All imports work')"

# Run template server (should start without errors)
python -m src.template_server

# In another terminal, test health
curl http://localhost:8000/health || python health_check.py
```

## 📝 Quick Development Commands

Once setup is working:

```bash
# Run servers
make run-template    # Template server
make run-original    # Original FogLAMP server
python examples/ecommerce_server.py  # E-commerce example

# Development
make test           # Run tests
make lint           # Check code quality  
make format         # Format code
make help           # See all commands
```

---

**The most important thing is to get a working Python environment. The DevContainer is nice-to-have, but the MCP server works perfectly fine in any Python 3.10+ environment!**
