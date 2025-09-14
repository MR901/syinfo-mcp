
import re
import requests
import subprocess
import platform
from bs4 import BeautifulSoup

import logging
from typing import Union, Dict, List, Any, Optional

try:
    from foglamp.common import logger
    _logger = logger.setup(__name__, level=logging.INFO)
except:
    logging.basicConfig(level=logging.INFO)
    _logger = logging.getLogger(__name__)

__author__ = "Mohit Rajput"
__copyright__ = "Copyright (c) 2025 Dianomic Systems Inc."
__license__ = "Apache 2.0"
__version__ = "${VERSION}"


class FogLAMPPlugin:

    @staticmethod
    def _parse_plugin_filename(filename: str) -> Optional[Dict[str, str]]:
        """Parse plugin filename to extract information."""
        pattern = r"foglamp-([^-]+)-([^_]+)_([^_]+)_([^.]+)\.deb"
        match = re.match(pattern, filename)

        if not match:
            return None

        plugin_type, plugin_name, version, architecture = match.groups()
        return {
            "type": plugin_type,
            "name": plugin_name,
            "full_name": f"foglamp-{plugin_type}-{plugin_name}",
            "version": version,
            "architecture": architecture
        }

    @staticmethod
    def _extract_file_info(link_element) -> Dict[str, Optional[str]]:
        """Extract file size and last modified date from link element."""
        try:
            parent = link_element.parent
            if not parent:
                return {"size": None, "last_modified": None}

            text = parent.get_text()

            # Extract size
            size_match = re.search(r"(\d+(?:\.\d+)?\s*[KMGT]?B)", text, re.IGNORECASE)
            size = size_match.group(1) if size_match else None

            # Extract date
            date_match = re.search(r"(\d{4}-\d{2}-\d{2}|\d{2}-\w{3}-\d{4})", text)
            last_modified = date_match.group(1) if date_match else None

            return {"size": size, "last_modified": last_modified}
        except Exception:
            return {"size": None, "last_modified": None}

    @staticmethod
    def _convert_size_to_bytes(size_str: str) -> int:
        """Convert size string to bytes."""
        if not size_str:
            return 0

        try:
            size_match = re.match(r"(\d+(?:\.\d+)?)\s*([KMGT]?)B?", size_str, re.IGNORECASE)
            if not size_match:
                return 0

            size_value = float(size_match.group(1))
            unit = size_match.group(2).upper()
            multipliers = {"K": 1024, "M": 1024**2, "G": 1024**3, "T": 1024**4}
            return int(size_value * multipliers.get(unit, 1))
        except Exception:
            return 0

    @staticmethod
    def list_foglamp_plugins(
        plugin_type: Optional[str] = None,
        search_term: Optional[str] = None,
        os_type: str = "ubuntu2404",
        architecture: str = "x86_64",
        repository_url: str = "http://archives.dianomic.com/foglamp/latest/",
        include_details: bool = False,
        sort_by: str = "name"
    ) -> Dict[str, Any]:
        """List and search FogLAMP plugins/packages from the Dianomic archives repository.

        Args:
            plugin_type: Filter by plugin type (south, north, filter, notification, rule, service)
            search_term: Search term to filter plugins by name
            os_type: Operating system type (e.g., ubuntu2404, ubuntu2204)
            architecture: System architecture (e.g., x86_64, arm64)
            repository_url: Base repository URL
            include_details: Include file size and last modified date
            sort_by: Sort order (name, version, size, date)

        Returns:
            Dict containing plugin list and summary information
        """
        _err_dict = {"src": "FogLAMPPlugin.list_foglamp_plugins()"}

        # Validation
        valid_plugin_types = ["south", "north", "filter", "notification", "rule", "service"]
        valid_sort_options = ["name", "version", "size", "date"]

        if plugin_type and plugin_type not in valid_plugin_types:
            return {"error": f"Invalid plugin_type. Must be one of: {', '.join(valid_plugin_types)}", "status": "invalid_parameter"}

        if sort_by not in valid_sort_options:
            return {"error": f"Invalid sort_by. Must be one of: {', '.join(valid_sort_options)}", "status": "invalid_parameter"}

        try:
            # Fetch repository page
            full_url = f"{repository_url.rstrip('/')}/{os_type}/{architecture}/"
            response = requests.get(full_url, timeout=30)
            response.raise_for_status()

            # Parse HTML and find plugin links
            soup = BeautifulSoup(response.content, "html.parser")
            plugin_links = soup.find_all("a", href=re.compile(r"\.deb$"))

            # Process plugins
            plugins = []
            categories = {}

            for link in plugin_links:
                href = link.get("href")
                if not href or "foglamp-" not in href:
                    continue

                plugin_info = FogLAMPPlugin._parse_plugin_filename(href)
                if not plugin_info:
                    continue

                # Apply filters
                if plugin_type and plugin_info["type"] != plugin_type:
                    continue

                if search_term:
                    search_lower = search_term.lower()
                    if not (search_lower in plugin_info["name"].lower() or 
                           search_lower in plugin_info["full_name"].lower()):
                        continue

                # Build plugin data
                plugin_data = {
                    "name": plugin_info["name"],
                    "full_name": plugin_info["full_name"],
                    "type": plugin_info["type"],
                    "version": plugin_info["version"],
                    "architecture": plugin_info["architecture"],
                    "filename": href,
                    "download_url": f"{full_url}{href}"
                }

                # Add details if requested
                if include_details:
                    file_info = FogLAMPPlugin._extract_file_info(link)
                    plugin_data.update({
                        "size": file_info["size"],
                        "last_modified": file_info["last_modified"],
                        "file_size_bytes": FogLAMPPlugin._convert_size_to_bytes(file_info["size"])
                    })

                plugins.append(plugin_data)

                # Update category counts
                category = plugin_info["type"]
                categories[category] = categories.get(category, 0) + 1

            # Sort results
            sort_keys = {
                "name": lambda x: x["name"].lower(),
                "version": lambda x: [int(v) for v in x["version"].split(".")],
                "size": lambda x: x.get("file_size_bytes", 0),
                "date": lambda x: x.get("last_modified", "")
            }

            if sort_by in sort_keys:
                plugins.sort(key=sort_keys[sort_by])

            return {
                "repository_info": {
                    "base_url": repository_url,
                    "os_type": os_type,
                    "architecture": architecture,
                    "full_url": full_url
                },
                "filters_applied": {
                    "plugin_type": plugin_type,
                    "search_term": search_term,
                    "include_details": include_details,
                    "sort_by": sort_by
                },
                "plugins": plugins,
                "summary": {
                    "total_plugins": len(plugins),
                    "categories": categories
                }
            }

        except requests.RequestException as e:
            _logger.error(f"Network error: {e}")
            _err_dict["error"] = f"Error fetching plugins: {e}"
            _err_dict["status"] = "network_error"
            return _err_dict
        except Exception as e:
            _logger.error(f"Unexpected error: {e}")
            _err_dict["error"] = f"Error listing plugins: {e}"
            _err_dict["status"] = "failed"
            return _err_dict

    @staticmethod
    def detect_platform() -> Dict[str, Any]:
        """Detect the current platform (Ubuntu/Raspberry Pi).

        Returns:
            Dict[str, Any]: Platform information.
        """
        _err_dict = {"src": "FogLAMPPlugin.detect_platform()"}
        try:
            system_info = {
                "system": platform.system(),
                "release": platform.release(),
                "machine": platform.machine(),
                "processor": platform.processor()
            }

            # Check for Raspberry Pi
            try:
                with open('/proc/cpuinfo', 'r') as f:
                    cpuinfo = f.read()
                    if 'Raspberry Pi' in cpuinfo:
                        system_info["platform"] = "raspberry_pi"
                        system_info["model"] = "Raspberry Pi"

                        # Try to get specific model
                        for line in cpuinfo.split('\n'):
                            if 'Model' in line:
                                system_info["model"] = line.split(':')[1].strip()
                                break
                    else:
                        system_info["platform"] = "ubuntu"
            except:
                system_info["platform"] = "unknown"

            # Check OS version
            try:
                result = subprocess.run(
                    "lsb_release -a",
                    shell=True, capture_output=True, text=True
                )
                if result.returncode == 0:
                    for line in result.stdout.split('\n'):
                        if 'Release:' in line:
                            system_info["os_version"] = line.split(':')[1].strip()
                        elif 'Codename:' in line:
                            system_info["os_codename"] = line.split(':')[1].strip()
            except:
                pass

            # Determine recommended platform string
            if system_info["platform"] == "raspberry_pi":
                system_info["recommended_platform"] = "rpi-bookworm"
            elif system_info["platform"] == "ubuntu":
                if system_info.get("os_version", "").startswith("24"):
                    system_info["recommended_platform"] = "ubuntu2404"
                elif system_info.get("os_version", "").startswith("22"):
                    system_info["recommended_platform"] = "ubuntu2204"
                else:
                    system_info["recommended_platform"] = "ubuntu2404"
            else:
                system_info["recommended_platform"] = "ubuntu2404"

            return {
                "status": "success",
                "platform_info": system_info
            }

        except Exception as e:
            _err_dict["error"] = str(e)
            _err_dict["status"] = "failed"
            return _err_dict

    @staticmethod
    def install_foglamp_package(
        package_name: str,
        version: Optional[str] = None,
        platform: str = "ubuntu2404"
    ) -> Dict[str, Any]:
        """Install a FogLAMP package from the repository.

        Note: First run detect_platform() to check the current system/platform to better decide the platform for the package installation here.

        Args:
            package_name (str): Full package name (e.g., foglamp-south-sinusoid, foglamp-north-omf).
            version (str, optional): Specific version to install.
            platform (str): Platform type (ubuntu2404, ubuntu2204, rpi-bookworm).

        Returns:
            Dict[str, Any]: Installation result.
        """
        _err_dict = {"src": "FogLAMPPlugin.install_foglamp_package()"}
        try:
            # Validate package name
            if not package_name.startswith("foglamp-"):
                _err_dict["error"] = "Package name must start with 'foglamp-'"
                _err_dict["status"] = "invalid_name"
                return _err_dict

            # Determine architecture based on platform
            if platform.startswith("rpi"):
                architecture = "arm64"  # Raspberry Pi 4/5 uses ARM64
            else:
                architecture = "x86_64"  # Ubuntu uses x86_64

            # Check if package is available
            available_packages = FogLAMPPlugin.list_foglamp_plugins(
                search_term=package_name,
                os_type=platform,
                architecture=architecture
            )

            if "error" in available_packages:
                _err_dict["error"] = f"Package not found: {available_packages['error']}"
                _err_dict["status"] = "not_found"
                return _err_dict

            # Find the package
            target_package = None
            for plugin in available_packages.get("plugins", []):
                if plugin["full_name"] == package_name:
                    target_package = plugin
                    break

            if not target_package:
                _err_dict["error"] = f"Package '{package_name}' not available for {platform}/{architecture}"
                _err_dict["status"] = "not_available"
                return _err_dict

            # Check if already installed
            installed = FogLAMPPlugin.check_installed_packages()
            for pkg in installed["packages"]:
                if pkg["package_name"] == package_name:
                    if not version or pkg["version"] == version:
                        _err_dict["message"] = f"Package {package_name} already installed"
                        _err_dict["status"] = "already_installed"
                        return _err_dict

            # Download and install using apt (both Ubuntu and RPi use apt)
            download_url = target_package["download_url"]
            download_cmd = f"wget -O /tmp/{package_name}.deb {download_url}"
            install_cmd = f"sudo apt install -y /tmp/{package_name}.deb"
            cleanup_cmd = f"rm -f /tmp/{package_name}.deb"

            full_cmd = f"{download_cmd} && {install_cmd} && {cleanup_cmd}"

            result = subprocess.run(full_cmd, shell=True, capture_output=True, text=True, timeout=300)

            if result.returncode == 0:
                return {
                    "status": "success",
                    "message": f"Successfully installed {package_name} on {platform}",
                    "version": target_package["version"],
                    "platform": platform,
                    "architecture": architecture
                }
            else:
                return {
                    "status": "failed",
                    "error": f"Installation failed: {result.stderr}",
                    "return_code": result.returncode,
                    "platform": platform
                }

        except Exception as e:
            _err_dict["error"] = str(e)
            _err_dict["status"] = "failed"
            return _err_dict

    @staticmethod
    def check_installed_packages() -> Dict[str, Any]:
        """Check for installed FogLAMP packages on Ubuntu/Raspberry Pi.

        Returns:
            Dict[str, Any]: List of installed FogLAMP packages.
        """
        _err_dict = {"src": "FogLAMPPlugin.check_installed_packages()"}
        try:
            # Check for installed packages using dpkg (Ubuntu/RPi)
            result = subprocess.run(
                "dpkg --list | grep foglamp",
                shell=True, capture_output=True, text=True
            )

            packages = []
            if result.returncode == 0:
                for line in result.stdout.strip().split('\n'):
                    if line.strip():
                        # Parse dpkg output: ii  foglamp-south-sinusoid  1.9.2  amd64  FogLAMP South Sinusoid Plugin
                        match = re.match(r'^ii\s+(\S+)\s+(\S+)\s+(\S+)\s+(.+)$', line.strip())
                        if match:
                            packages.append({
                                "package_name": match.group(1),
                                "version": match.group(2),
                                "architecture": match.group(3),
                                "description": match.group(4).strip()
                            })

            # Also check for Python packages installed via pip
            pip_result = subprocess.run(
                "pip list | grep foglamp",
                shell=True, capture_output=True, text=True
            )

            if pip_result.returncode == 0:
                for line in pip_result.stdout.strip().split('\n'):
                    if line.strip():
                        # Parse pip output: foglamp-south-sinusoid    1.9.2
                        match = re.match(r'^(\S+)\s+(\S+)$', line.strip())
                        if match:
                            packages.append({
                                "package_name": match.group(1),
                                "version": match.group(2),
                                "architecture": "python",
                                "description": f"Python package: {match.group(1)}"
                            })

            return {
                "status": "success",
                "package_manager": "dpkg/pip",
                "packages": packages,
                "total_count": len(packages)
            }

        except Exception as e:
            _err_dict["error"] = str(e)
            _err_dict["status"] = "failed"
            return _err_dict
