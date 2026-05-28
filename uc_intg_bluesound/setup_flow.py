"""
Bluesound setup flow for Unfolded Circle integration.

:copyright: (c) 2026 by Meir Miyara.
:license: MPL-2.0, see LICENSE for more details.
"""

import asyncio
import logging
from typing import Any

import aiohttp
from ucapi import RequestUserInput
from ucapi_framework import BaseSetupFlow

from uc_intg_bluesound.config import BluesoundConfig

_LOG = logging.getLogger(__name__)


class BluesoundSetupFlow(BaseSetupFlow[BluesoundConfig]):
    """Setup flow for Bluesound integration."""

    def get_manual_entry_form(self) -> RequestUserInput:
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
        host = input_values.get("host", "").strip()
        if not host:
            raise ValueError("IP address is required")

        name = input_values.get("name", f"Bluesound Player ({host})").strip()

        port = input_values.get("port", 11000)
        if isinstance(port, str):
            try:
                port = int(port)
            except ValueError:
                port = 11000

        _LOG.info("Setting up Bluesound player at %s:%d", host, port)

        try:
            timeout = aiohttp.ClientTimeout(total=5)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                url = f"http://{host}:{port}/Status"
                async with session.get(url) as resp:
                    if resp.status != 200:
                        raise ValueError(f"Player returned status {resp.status}")

            return BluesoundConfig(
                identifier=f"bluesound_{host.replace('.', '_')}",
                name=name,
                host=host,
                port=port,
            )

        except asyncio.TimeoutError:
            raise ValueError(
                f"Connection timeout to {host}:{port}\n"
                "Please verify the player is powered on and accessible"
            ) from None
        except aiohttp.ClientError as err:
            raise ValueError(f"Connection failed: {err}") from err
