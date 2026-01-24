"""
Bluesound driver for Unfolded Circle Remote.

:copyright: (c) 2026 by Meir Miyara.
:license: MPL-2.0, see LICENSE for more details.
"""

import logging
from ucapi import Entity
from ucapi_framework import BaseIntegrationDriver
from intg_bluesound.config import BluesoundConfig
from intg_bluesound.device import BluesoundDevice
from intg_bluesound.media_player import BluesoundMediaPlayer
from intg_bluesound.remote import BluesoundRemote
from intg_bluesound.sensor import BluesoundConnectionSensor, BluesoundGroupSensor

_LOG = logging.getLogger(__name__)


class BluesoundDriver(BaseIntegrationDriver[BluesoundDevice, BluesoundConfig]):
    """Bluesound integration driver."""

    def __init__(self):
        super().__init__(
            device_class=BluesoundDevice,
            entity_classes=[
                BluesoundMediaPlayer,
                BluesoundRemote,
                BluesoundConnectionSensor,
                BluesoundGroupSensor,
            ],
            driver_id="bluesound",
        )

    def create_entities(
        self, device_config: BluesoundConfig, device: BluesoundDevice
    ) -> list[Entity]:
        """Create entity instances."""
        _LOG.info("Creating entities for %s", device_config.name)
        return [
            BluesoundMediaPlayer(device_config, device),
            BluesoundRemote(device_config, device),
            BluesoundConnectionSensor(device_config, device),
            BluesoundGroupSensor(device_config, device),
        ]
