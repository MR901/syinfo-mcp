# -*- coding: utf-8 -*-

# FOGLAMP_BEGIN
# See: https://foglamp.dianomic.com
# FOGLAMP_END

import json
import logging

from foglamp.common import logger

__author__ = "Mohit Rajput"
__copyright__ = "Copyright (c) 2025 Dianomic Systems Inc."
__license__ = "Apache 2.0"
__version__ = "${VERSION}"

_logger = logger.setup(__name__, level=logging.INFO)


class ServiceRegistry:
    """Handles service registration and management with FogLAMP core."""

    def __init__(self, http_client, service_name):
        self._http_client = http_client
        self._ms_svc_name = service_name
        self._ms_svc_uuid = None
        self._schedule_uuid_for_task = None

    @property
    def service_uuid(self):
        return self._ms_svc_uuid

    def register_service(self, service_registration_payload, registration_token):
        """Register the service with FogLAMP core.

        Args:
            service_registration_payload (dict): Data needed to register service.
            registration_token (str): Registration token.

        Returns:
            dict: Registration response from core.
        """
        if registration_token:
            service_registration_payload["token"] = registration_token
        else:
            _logger.error("Single use registration token is missing")
            return

        _, response = self._http_client.make_request(
            action="POST",
            uri="/foglamp/service",
            payload=service_registration_payload
        )
        try:
            self._ms_svc_uuid = response["id"]
        except Exception as ex:
            _logger.error(
                "Could not register the microservice, From request: {}, Reason: {}".format(
                    json.dumps(service_registration_payload), str(ex)
                )
            )
            raise
        else:
            return response

    def create_category(self, config):
        """
        Create a configuration category for the service in FogLAMP.

        Args:
            config (dict): Configuration to create.

        Returns:
            dict: Category creation response.
        """
        payload = {
            "key": self._ms_svc_name,
            "description": "FogLAMP MCP service",
            "value": config
        }
        status, response = self._http_client.make_request(
            action="POST",
            uri="/foglamp/service/category",
            payload=payload
        )
        if status:
            return response
        else:
            _err_msg = "Could not create a category, From request: {}, Reason: {}".format(
                json.dumps(payload), str(response)
            )
            _logger.error(_err_msg)
            raise Exception(_err_msg)

    def register_interest(self):
        """Register interest for configuration category updates.

        Returns:
            dict: Interest registration response.
        """
        payload = {
            "category": self._ms_svc_name,
            "service": self._ms_svc_uuid
        }
        _, response = self._http_client.make_request(
            action="POST",
            uri="/foglamp/interest",
            payload=payload
        )
        try:
            response["id"]
        except Exception as ex:
            _logger.error("Could not create a interest register record, From request: {}, Reason: {}".format(
                json.dumps(payload), str(ex)))
            raise
        else:
            return response

    def unregister_service(self):
        """Unregister the service from FogLAMP core."""
        if self._ms_svc_uuid:
            _, response = self._http_client.make_request(
                action="DELETE",
                uri=f"/foglamp/service/{self._ms_svc_uuid}",
                payload=None
            )
            try:
                response["id"]
            except Exception as ex:
                _logger.error("Could not unregister the microservice, Reason: {}".format(str(ex)))
                raise
