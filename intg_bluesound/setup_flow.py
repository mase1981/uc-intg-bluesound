"""
Bluesound setup flow for Unfolded Circle integration.

:copyright: (c) 2026 by Meir Miyara.
:license: MPL-2.0, see LICENSE for more details.
"""

import asyncio
import logging
from typing import Any
from ucapi import RequestUserInput
from ucapi_framework import BaseSetupFlow
from intg_bluesound.config import BluesoundConfig
from intg_bluesound.device import BluesoundDevice

_LOG = logging.getLogger(__name__)


class BluesoundSetupFlow(BaseSetupFlow[BluesoundConfig]):
    """Setup flow for Bluesound integration."""

    def get_manual_entry_form(self) -> RequestUserInput:
        """Define manual entry fields."""
        return RequestUserInput(
            {"en": "Bluesound Player Setup"},
            [
                {
                    "id": "name",
                    "label": {"en": "Player Name"},
                    "field": {"text": {"value": "Bluesound Player"}},
                },
                {
                    "id": "host",
                    "label": {"en": "IP Address"},
                    "field": {"text": {"value": ""}},
                },
                {
                    "id": "port",
                    "label": {"en": "Port (default: 11000)"},
                    "field": {"number": {"value": 11000, "min": 1, "max": 65535}},
                },
            ],
        )

    async def query_device(
        self, input_values: dict[str, Any]
    ) -> BluesoundConfig | RequestUserInput:
        """
        Validate connection and create config.
        Called after user provides info.
        """
        host = input_values.get("host", "").strip()
        if not host:
            raise ValueError("IP address is required")

        name = input_values.get("name", f"Bluesound Player ({host})").strip()

        # Get port or use default
        port = input_values.get("port", 11000)
        if isinstance(port, str):
            try:
                port = int(port)
            except ValueError:
                port = 11000

        _LOG.info("Setting up Bluesound player at %s:%d", host, port)

        # Test connection
        try:
            test_config = BluesoundConfig(
                identifier=f"bluesound_{host.replace('.', '_')}",
                name=name,
                host=host,
                port=port
            )

            # Quick connection test
            test_device = BluesoundDevice(test_config)
            connected = await asyncio.wait_for(
                test_device.connect(),
                timeout=10.0
            )
            await test_device.disconnect()

            if not connected:
                raise ValueError(f"Failed to connect to {host}:{port}")

            _LOG.info("Successfully connected to Bluesound player at %s:%d", host, port)
            return test_config

        except asyncio.TimeoutError:
            raise ValueError(
                f"Connection timeout to {host}:{port}\n"
                "Please verify the player is powered on and accessible on the network"
            ) from None
        except Exception as err:
            raise ValueError(f"Setup failed: {err}") from err
