#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# FOGLAMP_BEGIN
# See: https://foglamp.dianomic.com
# FOGLAMP_END

"""FogLAMP MCP Service starter"""
import argparse
import sys
from foglamp.services.mcp.server import Server

__author__ = "Mohit Rajput"
__copyright__ = "Copyright (c) 2025 Dianomic Systems Inc."
__license__ = "Apache 2.0"
__version__ = "${VERSION}"


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--name", default="FogLAMP MCP")
    parser.add_argument("--address", required=True)
    parser.add_argument("--port", required=True, type=int)
    parser.add_argument("--token", required=True)

    namespace, args = parser.parse_known_args()
    svc_name = getattr(namespace, "name")
    core_management_host = getattr(namespace, "address")
    core_management_port = getattr(namespace, "port")
    token = getattr(namespace, "token")
    # if --dryrun option exists in args then instead of exit, create the config
    if "--dryrun" in args:
        sys.exit()
        # Server().create_config(svc_name, core_management_host, core_management_port, token)
    else:
        Server.run(svc_name, core_management_host, core_management_port, token)
