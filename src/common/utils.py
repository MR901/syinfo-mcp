# -*- coding: utf-8 -*-

# FOGLAMP_BEGIN
# See: https://foglamp.dianomic.com
# FOGLAMP_END

import logging
import subprocess
from typing import Tuple

from foglamp.common import logger

__author__ = "Mohit Rajput"
__copyright__ = "Copyright (c) 2025 Dianomic Systems Inc."
__license__ = "Apache 2.0"
__version__ = "${VERSION}"

_logger = logger.setup(__name__, level=logging.INFO)


def enable_cors(app):
    """Implement Cross Origin Resource Sharing (CORS) support."""
    import aiohttp_cors

    # Configure default CORS settings.
    cors = aiohttp_cors.setup(app, defaults={
        "*": aiohttp_cors.ResourceOptions(
            allow_methods=["GET", "POST", "PUT", "DELETE"],
            allow_credentials=True,
            expose_headers="*",
            allow_headers="*",
        )
    })

    # Configure CORS on all routes.
    for route in list(app.router.routes()):
        cors.add(route)

def get_host_info() -> Tuple[str, str]:
    ip_address = (
        subprocess.run(["hostname", "-I"], stdout=subprocess.PIPE)
        .stdout.decode("utf-8").replace("\n", "").strip().split(" ")
    )
    host_id = (
        subprocess.run("hostid", stdout=subprocess.PIPE)
        .stdout.decode("utf-8").replace("\n", "").strip().split(" ")
    )
    return ip_address[0], host_id[0]
