#!/usr/bin/env python3
"""
Quick Start Script for MCP Server Template

This script helps you get started quickly without any DevContainer or Docker setup.
It checks your environment, installs missing dependencies, and runs the server.

Usage:
    python quick_start.py [--original|--template|--ecommerce]
"""

import sys
import os
import subprocess
import importlib.util
from typing import List, Tuple

def check_python_version() -> bool:
    """Check if Python version is 3.10 or higher."""
    version = sys.version_info
    if version.major == 3 and version.minor >= 10:
        print(f"✅ Python {version.major}.{version.minor}.{version.micro} is compatible")
        return True
    else:
        print(f"❌ Python {version.major}.{version.minor}.{version.micro} is too old. Need Python 3.10+")
        return False

def check_package(package_name: str) -> bool:
    """Check if a package is installed."""
    spec = importlib.util.find_spec(package_name)
    return spec is not None

def install_packages(packages: List[str]) -> bool:
    """Install missing packages using pip."""
    try:
        cmd = [sys.executable, "-m", "pip", "install", "--upgrade"] + packages
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            print(f"✅ Installed: {', '.join(packages)}")
            return True
        else:
            print(f"❌ Failed to install packages: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ Error installing packages: {e}")
        return False

def check_and_install_dependencies() -> bool:
    """Check for required dependencies and install if missing."""
    
    # Core dependencies for MCP server
    required_packages = [
        ("mcp", "mcp==1.12.3"),
        ("aiohttp", "aiohttp==3.12.15"),
        ("requests", "requests==2.32.3"),
        ("tabulate", "tabulate==0.9.0"),
    ]
    
    # Optional dependencies
    optional_packages = [
        ("psycopg2", "psycopg2-binary==2.9.10"),
        ("bs4", "beautifulsoup4==4.12.3"),
    ]
    
    missing_packages = []
    
    print("🔍 Checking required dependencies...")
    
    # Check required packages
    for package_name, install_name in required_packages:
        if not check_package(package_name):
            print(f"❌ Missing: {package_name}")
            missing_packages.append(install_name)
        else:
            print(f"✅ Found: {package_name}")
    
    # Check optional packages
    print("\n🔍 Checking optional dependencies...")
    for package_name, install_name in optional_packages:
        if not check_package(package_name):
            print(f"⚠️  Optional: {package_name} (will install)")
            missing_packages.append(install_name)
        else:
            print(f"✅ Found: {package_name}")
    
    # Install missing packages
    if missing_packages:
        print(f"\n📦 Installing {len(missing_packages)} missing packages...")
        if install_packages(missing_packages):
            print("✅ All dependencies installed successfully!")
            return True
        else:
            print("❌ Some dependencies failed to install")
            return False
    else:
        print("\n✅ All dependencies are already installed!")
        return True

def setup_python_path():
    """Add src directory to Python path."""
    project_root = os.path.dirname(os.path.abspath(__file__))
    src_path = os.path.join(project_root, "src")
    
    if src_path not in sys.path:
        sys.path.insert(0, src_path)
        print(f"✅ Added to Python path: {src_path}")
    
    # Also set PYTHONPATH environment variable
    current_pythonpath = os.environ.get("PYTHONPATH", "")
    if src_path not in current_pythonpath:
        os.environ["PYTHONPATH"] = f"{src_path}:{current_pythonpath}".rstrip(":")
        print(f"✅ Set PYTHONPATH to include: {src_path}")

def run_server(server_type: str = "template") -> bool:
    """Run the specified server type."""
    
    setup_python_path()
    
    try:
        if server_type == "original":
            print("\n🚀 Starting Original FogLAMP MCP Server...")
            from src.mcp_server import main
            main()
            
        elif server_type == "template":
            print("\n🚀 Starting Template MCP Server...")
            from src.template_server import main
            main()
            
        elif server_type == "ecommerce":
            print("\n🛒 Starting E-commerce Example Server...")
            # Add project root to path for examples
            project_root = os.path.dirname(os.path.abspath(__file__))
            if project_root not in sys.path:
                sys.path.insert(0, project_root)
            
            from examples.ecommerce_server import main
            main()
            
        else:
            print(f"❌ Unknown server type: {server_type}")
            return False
            
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("💡 Try installing missing dependencies or check file paths")
        return False
    except KeyboardInterrupt:
        print(f"\n👋 {server_type.title()} server stopped by user")
        return True
    except Exception as e:
        print(f"❌ Server error: {e}")
        return False
    
    return True

def show_help():
    """Show help information."""
    print("""
🚀 MCP Server Template Quick Start

This script helps you get started quickly with the MCP server template.

Usage:
    python quick_start.py [options]

Options:
    --original, -o    Run the original FogLAMP MCP server
    --template, -t    Run the generic template server (default)
    --ecommerce, -e   Run the e-commerce example server
    --help, -h        Show this help message

Examples:
    python quick_start.py                    # Run template server
    python quick_start.py --template         # Run template server
    python quick_start.py --original         # Run original server  
    python quick_start.py --ecommerce        # Run e-commerce example

Environment Variables:
    MCP_HOST=0.0.0.0     # Server host (default: 0.0.0.0)
    MCP_PORT=8000        # Server port (default: 8000)
    MCP_DEBUG=true       # Enable debug mode
    MCP_LOG_LEVEL=DEBUG  # Set log level

After starting the server:
    - Server will be available at http://localhost:8000
    - Press Ctrl+C to stop the server
    - Check server health: python health_check.py
""")

def main():
    """Main entry point."""
    
    # Parse command line arguments
    server_type = "template"  # default
    
    if len(sys.argv) > 1:
        arg = sys.argv[1].lower()
        if arg in ["--help", "-h", "help"]:
            show_help()
            return
        elif arg in ["--original", "-o", "original"]:
            server_type = "original"
        elif arg in ["--template", "-t", "template"]:
            server_type = "template"
        elif arg in ["--ecommerce", "-e", "ecommerce"]:
            server_type = "ecommerce"
        else:
            print(f"❌ Unknown option: {arg}")
            show_help()
            return
    
    print("🎯 MCP Server Template Quick Start")
    print("=" * 50)
    
    # Check Python version
    if not check_python_version():
        print("\n💡 Please install Python 3.10 or higher:")
        print("   - Download from: https://python.org/downloads/")
        print("   - Or use pyenv: pyenv install 3.10")
        sys.exit(1)
    
    # Check and install dependencies
    print("\n" + "=" * 50)
    if not check_and_install_dependencies():
        print("\n💡 You can also manually install dependencies:")
        print("   pip install mcp aiohttp requests tabulate")
        sys.exit(1)
    
    # Run the server
    print("\n" + "=" * 50)
    run_server(server_type)

if __name__ == "__main__":
    main()
