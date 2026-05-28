"""
Bluesound select entities.

:copyright: (c) 2026 by Meir Miyara.
:license: MPL-2.0, see LICENSE for more details.
"""

from __future__ import annotations

import logging
from typing import Any, TYPE_CHECKING

from ucapi import select, StatusCodes
from ucapi_framework import SelectEntity

if TYPE_CHECKING:
    from uc_intg_bluesound.config import BluesoundConfig
    from uc_intg_bluesound.device import BluesoundDevice

_LOG = logging.getLogger(__name__)

REPEAT_OPTIONS = ["Off", "All", "One"]


class BluesoundRepeatSelect(SelectEntity):
    """Repeat mode select for Bluesound player."""

    def __init__(self, device_config: BluesoundConfig, device: BluesoundDevice) -> None:
        self._device = device
        entity_id = f"select.{device_config.identifier}.repeat"
        super().__init__(
            entity_id,
            f"{device_config.name} Repeat",
            {
                select.Attributes.STATE: select.States.UNKNOWN,
                select.Attributes.OPTIONS: [],
                select.Attributes.CURRENT_OPTION: "",
            },
            cmd_handler=self._handle_command,
        )
        self.subscribe_to_device(device)

    async def sync_state(self) -> None:
        if self._device.state == "UNAVAILABLE":
            self.update({select.Attributes.STATE: select.States.UNAVAILABLE})
            return

        current = self._device.repeat.capitalize()
        self.update({
            select.Attributes.STATE: select.States.ON,
            select.Attributes.OPTIONS: REPEAT_OPTIONS,
            select.Attributes.CURRENT_OPTION: current,
        })

    async def _handle_command(
        self, entity: select.Select, cmd_id: str, params: dict[str, Any] | None
    ) -> StatusCodes:
        if cmd_id == select.Commands.SELECT_OPTION:
            option = params.get("option", "") if params else ""
            repeat_map = {"Off": "OFF", "All": "ALL", "One": "ONE"}
            repeat_val = repeat_map.get(option)
            if repeat_val is None:
                return StatusCodes.BAD_REQUEST
            ok = await self._device.set_repeat(repeat_val)
            return StatusCodes.OK if ok else StatusCodes.SERVER_ERROR
        return StatusCodes.NOT_IMPLEMENTED


class BluesoundPresetSelect(SelectEntity):
    """Preset select for Bluesound player."""

    def __init__(self, device_config: BluesoundConfig, device: BluesoundDevice) -> None:
        self._device = device
        entity_id = f"select.{device_config.identifier}.preset"
        super().__init__(
            entity_id,
            f"{device_config.name} Preset",
            {
                select.Attributes.STATE: select.States.UNKNOWN,
                select.Attributes.OPTIONS: [],
                select.Attributes.CURRENT_OPTION: "",
            },
            cmd_handler=self._handle_command,
        )
        self.subscribe_to_device(device)

    async def sync_state(self) -> None:
        if self._device.state == "UNAVAILABLE":
            self.update({select.Attributes.STATE: select.States.UNAVAILABLE})
            return

        presets = self._device.presets
        options = [p.get("name", f"Preset {p.get('id')}") for p in presets]

        self.update({
            select.Attributes.STATE: select.States.ON,
            select.Attributes.OPTIONS: options if options else ["No presets"],
            select.Attributes.CURRENT_OPTION: options[0] if options else "No presets",
        })

    async def _handle_command(
        self, entity: select.Select, cmd_id: str, params: dict[str, Any] | None
    ) -> StatusCodes:
        if cmd_id == select.Commands.SELECT_OPTION:
            option = params.get("option", "") if params else ""
            for preset in self._device.presets:
                preset_name = preset.get("name", "")
                if preset_name == option:
                    preset_id = int(preset.get("id", 0))
                    ok = await self._device.select_preset(preset_id)
                    return StatusCodes.OK if ok else StatusCodes.SERVER_ERROR
            return StatusCodes.BAD_REQUEST
        return StatusCodes.NOT_IMPLEMENTED
