"""
Bluesound Sensor entities.

:copyright: (c) 2026 by Meir Miyara.
:license: MPL-2.0, see LICENSE for more details.
"""

import logging
from ucapi.sensor import Sensor, DeviceClasses
from intg_bluesound.config import BluesoundConfig
from intg_bluesound.device import BluesoundDevice

_LOG = logging.getLogger(__name__)


class BluesoundConnectionSensor(Sensor):
    """Connection status sensor for Bluesound player."""

    def __init__(self, device_config: BluesoundConfig, device: BluesoundDevice):
        """Initialize with device reference."""
        self._device = device
        self._device_config = device_config

        entity_id = f"sensor.{device_config.identifier}_connection"

        super().__init__(
            identifier=entity_id,
            name=f"{device_config.name} Connection",
            features=[],
            attributes={
                "state": "Disconnected",
                "value": "disconnected",
            },
        )


class BluesoundGroupSensor(Sensor):
    """Group status sensor for Bluesound player."""

    def __init__(self, device_config: BluesoundConfig, device: BluesoundDevice):
        """Initialize with device reference."""
        self._device = device
        self._device_config = device_config

        entity_id = f"sensor.{device_config.identifier}_group"

        super().__init__(
            identifier=entity_id,
            name=f"{device_config.name} Group Status",
            features=[],
            attributes={
                "state": "Ungrouped",
                "value": "ungrouped",
            },
        )
