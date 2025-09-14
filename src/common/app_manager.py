# -*- coding: utf-8 -*-

# FOGLAMP_BEGIN
# See: https://foglamp.dianomic.com
# FOGLAMP_END

import asyncio
import logging
from aiohttp import web

from foglamp.common import logger

__author__ = "Mohit Rajput"
__copyright__ = "Copyright (c) 2025 Dianomic Systems Inc."
__license__ = "Apache 2.0"
__version__ = "${VERSION}"

_logger = logger.setup(__name__, level=logging.INFO)


class AppManager:
    """Manages aiohttp application servers."""

    def __init__(self):
        self.loop = None
        self.svc_app = None
        self.svc_app_server = None
        self.svc_app_server_handler = None
        self.mgt_app = None
        self.mgt_app_server = None
        self.mgt_app_server_handler = None

    def start_app(self, app, host, port, ssl_ctx=None):
        """
        Start an aiohttp application server.

        Args:
            app (aiohttp.web.Application): Application instance.
            host (str): Host IP.
            port (int): Port number.
            ssl_ctx (ssl.SSLContext or None): SSL context if TLS is used.

        Returns:
            tuple: server and handler
        """
        if self.loop is None:
            self.loop = asyncio.get_event_loop()
        handler = app.make_handler()
        coro = self.loop.create_server(handler, host, port, ssl=ssl_ctx)
        server = self.loop.run_until_complete(coro)
        return server, handler

    async def stop_app(self):
        """Gracefully stops both management and service aiohttp servers."""
        if self.svc_app_server:
            self.svc_app_server.close()
            await self.svc_app_server.wait_closed()
            await self.svc_app.cleanup()

        if self.mgt_app_server:
            self.mgt_app_server.close()
            await self.mgt_app_server.wait_closed()
            await self.mgt_app.cleanup()

        if self.loop:
            self.loop.stop()
