"""
Bluesound sensor entities.

:copyright: (c) 2026 by Meir Miyara.
:license: MPL-2.0, see LICENSE for more details.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from ucapi import sensor
from ucapi_framework import SensorEntity

if TYPE_CHECKING:
    from uc_intg_bluesound.config import BluesoundConfig
    from uc_intg_bluesound.device import BluesoundDevice

_LOG = logging.getLogger(__name__)


class BluesoundConnectionSensor(SensorEntity):
    """Connection status sensor for Bluesound player."""

    def __init__(self, device_config: BluesoundConfig, device: BluesoundDevice) -> None:
        self._device = device
        entity_id = f"sensor.{device_config.identifier}.connection"
        super().__init__(
            entity_id,
            f"{device_config.name} Connection",
            [],
            {
                sensor.Attributes.STATE: sensor.States.UNKNOWN,
                sensor.Attributes.VALUE: "",
            },
            device_class=sensor.DeviceClasses.CUSTOM,
            options={sensor.Options.CUSTOM_UNIT: ""},
        )
        self.subscribe_to_device(device)

    async def sync_state(self) -> None:
        if self._device.state == "UNAVAILABLE":
            self.update({
                sensor.Attributes.STATE: sensor.States.UNAVAILABLE,
                sensor.Attributes.VALUE: "disconnected",
            })
            return
        self.update({
            sensor.Attributes.STATE: sensor.States.ON,
            sensor.Attributes.VALUE: "connected",
        })


class BluesoundGroupSensor(SensorEntity):
    """Group status sensor for Bluesound player."""

    def __init__(self, device_config: BluesoundConfig, device: BluesoundDevice) -> None:
        self._device = device
        entity_id = f"sensor.{device_config.identifier}.group"
        super().__init__(
            entity_id,
            f"{device_config.name} Group Status",
            [],
            {
                sensor.Attributes.STATE: sensor.States.UNKNOWN,
                sensor.Attributes.VALUE: "",
            },
            device_class=sensor.DeviceClasses.CUSTOM,
            options={sensor.Options.CUSTOM_UNIT: ""},
        )
        self.subscribe_to_device(device)

    async def sync_state(self) -> None:
        if self._device.state == "UNAVAILABLE":
            self.update({
                sensor.Attributes.STATE: sensor.States.UNAVAILABLE,
                sensor.Attributes.VALUE: "unavailable",
            })
            return

        if self._device.is_grouped:
            if self._device.is_leader:
                group_status = "Leader"
            else:
                group_status = "Follower"
        else:
            group_status = "Ungrouped"

        display = self._device.group_name if self._device.group_name else group_status

        self.update({
            sensor.Attributes.STATE: sensor.States.ON,
            sensor.Attributes.VALUE: display,
        })


class BluesoundSourceSensor(SensorEntity):
    """Current source/service sensor for Bluesound player."""

    def __init__(self, device_config: BluesoundConfig, device: BluesoundDevice) -> None:
        self._device = device
        entity_id = f"sensor.{device_config.identifier}.source"
        super().__init__(
            entity_id,
            f"{device_config.name} Source",
            [],
            {
                sensor.Attributes.STATE: sensor.States.UNKNOWN,
                sensor.Attributes.VALUE: "",
            },
            device_class=sensor.DeviceClasses.CUSTOM,
            options={sensor.Options.CUSTOM_UNIT: ""},
        )
        self.subscribe_to_device(device)

    async def sync_state(self) -> None:
        if self._device.state == "UNAVAILABLE":
            self.update({
                sensor.Attributes.STATE: sensor.States.UNAVAILABLE,
                sensor.Attributes.VALUE: "unavailable",
            })
            return
        self.update({
            sensor.Attributes.STATE: sensor.States.ON,
            sensor.Attributes.VALUE: self._device.source or "None",
        })
