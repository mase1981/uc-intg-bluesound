"""
Bluesound remote entity.

:copyright: (c) 2026 by Meir Miyara.
:license: MPL-2.0, see LICENSE for more details.
"""

from __future__ import annotations

import logging
from typing import Any, TYPE_CHECKING

from ucapi import remote, StatusCodes
from ucapi.ui import Buttons, create_btn_mapping, create_ui_text, create_ui_icon, UiPage, Size
from ucapi_framework import RemoteEntity

if TYPE_CHECKING:
    from uc_intg_bluesound.config import BluesoundConfig
    from uc_intg_bluesound.device import BluesoundDevice

_LOG = logging.getLogger(__name__)

COMMANDS = [
    "PLAY", "PAUSE", "STOP", "PLAY_PAUSE", "NEXT", "PREVIOUS",
    "VOLUME_UP", "VOLUME_DOWN", "MUTE_TOGGLE",
    "REPEAT_OFF", "REPEAT_ALL", "REPEAT_ONE",
    "SHUFFLE_ON", "SHUFFLE_OFF",
    "PRESET_1", "PRESET_2", "PRESET_3", "PRESET_4", "PRESET_5",
    "PRESET_6", "PRESET_7", "PRESET_8", "PRESET_9", "PRESET_10",
    "LEAVE_GROUP",
]


class BluesoundRemote(RemoteEntity):
    """Remote entity for Bluesound BluOS players."""

    def __init__(self, device_config: BluesoundConfig, device: BluesoundDevice) -> None:
        self._device = device
        entity_id = f"remote.{device_config.identifier}"

        super().__init__(
            entity_id,
            f"{device_config.name} Remote",
            features=[remote.Features.ON_OFF, remote.Features.SEND_CMD],
            attributes={remote.Attributes.STATE: remote.States.UNKNOWN},
            simple_commands=COMMANDS,
            button_mapping=[
                create_btn_mapping(Buttons.PLAY, short="PLAY_PAUSE"),
                create_btn_mapping(Buttons.STOP, short="STOP"),
                create_btn_mapping(Buttons.PREV, short="PREVIOUS"),
                create_btn_mapping(Buttons.NEXT, short="NEXT"),
                create_btn_mapping(Buttons.VOLUME_UP, short="VOLUME_UP"),
                create_btn_mapping(Buttons.VOLUME_DOWN, short="VOLUME_DOWN"),
                create_btn_mapping(Buttons.MUTE, short="MUTE_TOGGLE"),
            ],
            ui_pages=[
                UiPage("playback", "Playback", grid=Size(4, 6), items=[
                    create_ui_text("Playback", 0, 0, Size(4, 1)),
                    create_ui_icon("uc:play", 0, 1, cmd="PLAY"),
                    create_ui_icon("uc:pause", 1, 1, cmd="PAUSE"),
                    create_ui_icon("uc:stop", 2, 1, cmd="STOP"),
                    create_ui_icon("uc:prev", 0, 2, cmd="PREVIOUS"),
                    create_ui_icon("uc:next", 1, 2, cmd="NEXT"),
                    create_ui_text("Volume", 0, 3, Size(4, 1)),
                    create_ui_icon("uc:up-arrow-bold", 0, 4, cmd="VOLUME_UP"),
                    create_ui_icon("uc:down-arrow-bold", 1, 4, cmd="VOLUME_DOWN"),
                    create_ui_icon("uc:mute", 2, 4, cmd="MUTE_TOGGLE"),
                ]),
                UiPage("modes", "Modes & Presets", grid=Size(4, 6), items=[
                    create_ui_text("Repeat", 0, 0, Size(4, 1)),
                    create_ui_text("Off", 0, 1, Size(1, 1), cmd="REPEAT_OFF"),
                    create_ui_text("All", 1, 1, Size(1, 1), cmd="REPEAT_ALL"),
                    create_ui_text("One", 2, 1, Size(1, 1), cmd="REPEAT_ONE"),
                    create_ui_text("Shuffle", 0, 2, Size(4, 1)),
                    create_ui_text("On", 0, 3, Size(2, 1), cmd="SHUFFLE_ON"),
                    create_ui_text("Off", 2, 3, Size(2, 1), cmd="SHUFFLE_OFF"),
                    create_ui_text("Presets", 0, 4, Size(4, 1)),
                    create_ui_text("1", 0, 5, Size(1, 1), cmd="PRESET_1"),
                    create_ui_text("2", 1, 5, Size(1, 1), cmd="PRESET_2"),
                    create_ui_text("3", 2, 5, Size(1, 1), cmd="PRESET_3"),
                    create_ui_text("4", 3, 5, Size(1, 1), cmd="PRESET_4"),
                ]),
            ],
            cmd_handler=self._handle_command,
        )
        self.subscribe_to_device(device)

    async def sync_state(self) -> None:
        if self._device.state == "UNAVAILABLE":
            self.update({remote.Attributes.STATE: remote.States.UNAVAILABLE})
            return
        self.update({remote.Attributes.STATE: remote.States.ON})

    async def _handle_command(
        self, entity: remote.Remote, cmd_id: str, params: dict[str, Any] | None
    ) -> StatusCodes:
        if cmd_id == remote.Commands.ON:
            return StatusCodes.OK
        if cmd_id == remote.Commands.OFF:
            await self._device.stop()
            return StatusCodes.OK

        if cmd_id != remote.Commands.SEND_CMD:
            return StatusCodes.NOT_IMPLEMENTED

        command = params.get("command", "") if params else ""
        if not command:
            return StatusCodes.BAD_REQUEST

        try:
            return await self._dispatch(command)
        except Exception as err:
            _LOG.error("[%s] Remote command error: %s", self.id, err)
            return StatusCodes.SERVER_ERROR

    async def _dispatch(self, command: str) -> StatusCodes:
        d = self._device

        dispatch_map = {
            "PLAY": d.play,
            "PAUSE": d.pause,
            "STOP": d.stop,
            "PLAY_PAUSE": d.play_pause,
            "NEXT": d.next_track,
            "PREVIOUS": d.previous_track,
            "VOLUME_UP": d.volume_up,
            "VOLUME_DOWN": d.volume_down,
            "MUTE_TOGGLE": d.mute_toggle,
            "LEAVE_GROUP": d.leave_group,
        }

        if command in dispatch_map:
            ok = await dispatch_map[command]()
            return StatusCodes.OK if ok else StatusCodes.SERVER_ERROR

        if command == "REPEAT_OFF":
            ok = await d.set_repeat("OFF")
            return StatusCodes.OK if ok else StatusCodes.SERVER_ERROR
        if command == "REPEAT_ALL":
            ok = await d.set_repeat("ALL")
            return StatusCodes.OK if ok else StatusCodes.SERVER_ERROR
        if command == "REPEAT_ONE":
            ok = await d.set_repeat("ONE")
            return StatusCodes.OK if ok else StatusCodes.SERVER_ERROR
        if command == "SHUFFLE_ON":
            ok = await d.set_shuffle(True)
            return StatusCodes.OK if ok else StatusCodes.SERVER_ERROR
        if command == "SHUFFLE_OFF":
            ok = await d.set_shuffle(False)
            return StatusCodes.OK if ok else StatusCodes.SERVER_ERROR

        if command.startswith("PRESET_"):
            try:
                preset_num = int(command.split("_")[1])
                ok = await d.select_preset(preset_num)
                return StatusCodes.OK if ok else StatusCodes.SERVER_ERROR
            except (ValueError, IndexError):
                return StatusCodes.BAD_REQUEST

        return StatusCodes.NOT_IMPLEMENTED
