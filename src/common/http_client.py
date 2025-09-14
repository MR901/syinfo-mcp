# -*- coding: utf-8 -*-

# FOGLAMP_BEGIN
# See: https://foglamp.dianomic.com
# FOGLAMP_END

import ssl
import json
import logging
from urllib.parse import urlencode
from http.client import HTTPConnection, HTTPSConnection

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


class HTTPClient:
    """Handles HTTP/HTTPS communication with FogLAMP core."""

    def __init__(
        self, core_mgt_host, core_mgt_port, auth_token=None, is_tls_enabled=False
    ):
        self._core_mgt_host = core_mgt_host
        self._core_mgt_port = core_mgt_port
        self._auth_token = auth_token
        self._is_tls_enabled = is_tls_enabled

    def make_request(
        self, action, uri, payload=None, port=None, headers=None,
        params=None, timeout=None, verify=True
    ):
        """Make an HTTP or HTTPS request to the FogLAMP core service.

        Args:
            action (str): HTTP method ("GET", "POST", etc.).
            uri (str): Request URI.
            payload (dict or None): JSON payload to send.
            port (int or None): Port to connect to (defaults to _core_mgt_port).
            headers (dict or None): Additional request headers (merged).
            params (dict or None): Query string parameters.
            timeout (float or None): Timeout in seconds.
            verify (bool): Whether to verify TLS certificate (only if TLS enabled).

        Returns:
            dict or str: Parsed JSON response or raw string if not JSON.
        """
        success = False
        port = self._core_mgt_port if port is None else port

        # Build final URI with query params
        if params:
            query_str = urlencode(params)
            uri = f"{uri}?{query_str}"

        # Prepare payload
        data = None
        if payload is not None:
            data = json.dumps(payload)
            if not headers:
                headers = {}
            headers.setdefault("Content-Type", "application/json")

        # Merge headers and auth
        final_headers = {}
        if headers:
            final_headers.update(headers)
        if self._auth_token:
            final_headers["Authorization"] = self._auth_token

        # Choose connection type
        if self._is_tls_enabled:
            context = ssl.create_default_context()
            if not verify:
                context.check_hostname = False
                context.verify_mode = ssl.CERT_NONE
            conn = HTTPSConnection(self._core_mgt_host, port, context=context, timeout=timeout)
        else:
            conn = HTTPConnection(self._core_mgt_host, port, timeout=timeout)

        try:
            conn.request(action, uri, body=data, headers=final_headers)
            r = conn.getresponse()
            if r.status == 412:
                _err_msg = f"Precondition Failed on {uri}"
                _logger.warning(_err_msg)
                success = True
            elif r.status in range(400, 500):
                _err_msg = f"Client error {r.status} on {uri}: {r.reason}"
                _logger.warning(_err_msg)
            elif r.status in range(500, 600):
                _err_msg = f"Server error {r.status} on {uri}: {r.reason}"
                _logger.error(_err_msg)
            else:
                success = True

            if not success:
                return success, {"error": _err_msg}

            res = r.read().decode()
            try:
                return success, json.loads(res)
            except json.JSONDecodeError:
                return success, res
        except Exception as ex:
            _err_msg = f"Error making request to {uri}: {ex}"
            _logger.error(_err_msg)
            return success, {"error": _err_msg}
        finally:
            conn.close()
