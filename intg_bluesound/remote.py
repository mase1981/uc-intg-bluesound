"""
Bluesound Remote entity.

:copyright: (c) 2026 by Meir Miyara.
:license: MPL-2.0, see LICENSE for more details.
"""

import logging
from typing import Any
from ucapi import StatusCodes
from ucapi.remote import Remote
from ucapi.ui import UiPage, Size, create_ui_icon, create_ui_text
from intg_bluesound.config import BluesoundConfig
from intg_bluesound.device import BluesoundDevice

_LOG = logging.getLogger(__name__)


class BluesoundRemote(Remote):
    """Remote entity for Bluesound BluOS players."""

    def __init__(self, device_config: BluesoundConfig, device: BluesoundDevice):
        """Initialize with device reference."""
        self._device = device
        self._device_config = device_config

        entity_id = f"remote.{device_config.identifier}"

        # Build simple commands list
        simple_commands = self._build_commands()

        # Build UI pages
        ui_pages = self._build_ui_pages(device_config.name)

        super().__init__(
            identifier=entity_id,
            name=f"{device_config.name} Remote",
            features=["send_cmd"],
            attributes={
                "state": "available",
                "last_command": "",
                "last_result": "",
            },
            simple_commands=simple_commands,
            ui_pages=ui_pages,
            cmd_handler=self.handle_command,
        )

    def _build_commands(self) -> list[str]:
        """Build list of simple commands."""
        commands = []

        # Playback commands
        commands.extend([
            "PLAY",
            "PAUSE",
            "STOP",
            "PLAY_PAUSE",
            "NEXT",
            "PREVIOUS",
        ])

        # Volume commands
        commands.extend([
            "VOLUME_UP",
            "VOLUME_DOWN",
            "MUTE_TOGGLE",
        ])

        # Repeat/Shuffle commands
        commands.extend([
            "REPEAT_OFF",
            "REPEAT_ALL",
            "REPEAT_ONE",
            "SHUFFLE_ON",
            "SHUFFLE_OFF",
        ])

        # Preset commands (1-10)
        for i in range(1, 11):
            commands.append(f"PRESET_{i}")

        # Grouping commands
        commands.extend([
            "LEAVE_GROUP",
        ])

        return commands

    def _build_ui_pages(self, device_name: str) -> list[UiPage]:
        """Build UI pages for the remote."""
        pages = []

        # Page 1: Playback and Volume
        page1 = UiPage("page1", f"{device_name} Controls")
        page1.add(create_ui_text("Playback", 0, 0, Size(4, 1)))
        page1.add(create_ui_icon("uc:play", 0, 1, cmd="PLAY"))
        page1.add(create_ui_icon("uc:pause", 1, 1, cmd="PAUSE"))
        page1.add(create_ui_icon("uc:stop", 2, 1, cmd="STOP"))
        page1.add(create_ui_icon("uc:prev", 3, 1, cmd="PREVIOUS"))
        page1.add(create_ui_icon("uc:next", 0, 2, cmd="NEXT"))
        page1.add(create_ui_text("Volume", 0, 3, Size(4, 1)))
        page1.add(create_ui_icon("uc:up-arrow-bold", 0, 4, cmd="VOLUME_UP"))
        page1.add(create_ui_icon("uc:down-arrow-bold", 1, 4, cmd="VOLUME_DOWN"))
        page1.add(create_ui_icon("uc:mute", 2, 4, cmd="MUTE_TOGGLE"))
        pages.append(page1)

        # Page 2: Modes and Presets
        page2 = UiPage("page2", f"{device_name} Modes")
        page2.add(create_ui_text("Repeat", 0, 0, Size(4, 1)))
        page2.add(create_ui_text("Off", 0, 1, Size(1, 1), cmd="REPEAT_OFF"))
        page2.add(create_ui_text("All", 1, 1, Size(1, 1), cmd="REPEAT_ALL"))
        page2.add(create_ui_text("One", 2, 1, Size(1, 1), cmd="REPEAT_ONE"))
        page2.add(create_ui_text("Shuffle", 0, 2, Size(4, 1)))
        page2.add(create_ui_text("On", 0, 3, Size(2, 1), cmd="SHUFFLE_ON"))
        page2.add(create_ui_text("Off", 2, 3, Size(2, 1), cmd="SHUFFLE_OFF"))
        page2.add(create_ui_text("Presets", 0, 4, Size(4, 1)))
        page2.add(create_ui_text("1", 0, 5, Size(1, 1), cmd="PRESET_1"))
        page2.add(create_ui_text("2", 1, 5, Size(1, 1), cmd="PRESET_2"))
        page2.add(create_ui_text("3", 2, 5, Size(1, 1), cmd="PRESET_3"))
        page2.add(create_ui_text("4", 3, 5, Size(1, 1), cmd="PRESET_4"))
        pages.append(page2)

        # Page 3: Grouping
        page3 = UiPage("page3", f"{device_name} Grouping")
        page3.add(create_ui_text("Multi-Room", 0, 0, Size(4, 1)))
        page3.add(create_ui_text("Leave Group", 0, 1, Size(4, 1), cmd="LEAVE_GROUP"))
        page3.add(create_ui_text("", 0, 2, Size(4, 1)))
        page3.add(create_ui_text("Note: Use Bluesound", 0, 3, Size(4, 1)))
        page3.add(create_ui_text("app to create groups", 0, 4, Size(4, 1)))
        pages.append(page3)

        return pages

    async def handle_command(
        self, entity: Remote, cmd_id: str, params: dict[str, Any] | None
    ) -> StatusCodes:
        """Handle commands."""
        _LOG.info("[%s] Remote command: %s %s", self.id, cmd_id, params or "")

        try:
            actual_command = params.get("command", cmd_id) if params else cmd_id
            self.attributes["last_command"] = actual_command

            # Playback commands
            if actual_command == "PLAY":
                success = await self._device.play()
                self.attributes["last_result"] = "Playing" if success else "Failed"

            elif actual_command == "PAUSE":
                success = await self._device.pause()
                self.attributes["last_result"] = "Paused" if success else "Failed"

            elif actual_command == "STOP":
                success = await self._device.stop()
                self.attributes["last_result"] = "Stopped" if success else "Failed"

            elif actual_command == "PLAY_PAUSE":
                success = await self._device.play_pause()
                self.attributes["last_result"] = "Toggled" if success else "Failed"

            elif actual_command == "NEXT":
                success = await self._device.next_track()
                self.attributes["last_result"] = "Next track" if success else "Failed"

            elif actual_command == "PREVIOUS":
                success = await self._device.previous_track()
                self.attributes["last_result"] = "Previous track" if success else "Failed"

            # Volume commands
            elif actual_command == "VOLUME_UP":
                success = await self._device.volume_up()
                self.attributes["last_result"] = "Volume up" if success else "Failed"

            elif actual_command == "VOLUME_DOWN":
                success = await self._device.volume_down()
                self.attributes["last_result"] = "Volume down" if success else "Failed"

            elif actual_command == "MUTE_TOGGLE":
                success = await self._device.mute_toggle()
                self.attributes["last_result"] = "Mute toggled" if success else "Failed"

            # Repeat commands
            elif actual_command == "REPEAT_OFF":
                success = await self._device.set_repeat("OFF")
                self.attributes["last_result"] = "Repeat: Off" if success else "Failed"

            elif actual_command == "REPEAT_ALL":
                success = await self._device.set_repeat("ALL")
                self.attributes["last_result"] = "Repeat: All" if success else "Failed"

            elif actual_command == "REPEAT_ONE":
                success = await self._device.set_repeat("ONE")
                self.attributes["last_result"] = "Repeat: One" if success else "Failed"

            # Shuffle commands
            elif actual_command == "SHUFFLE_ON":
                success = await self._device.set_shuffle(True)
                self.attributes["last_result"] = "Shuffle: On" if success else "Failed"

            elif actual_command == "SHUFFLE_OFF":
                success = await self._device.set_shuffle(False)
                self.attributes["last_result"] = "Shuffle: Off" if success else "Failed"

            # Preset commands
            elif actual_command.startswith("PRESET_"):
                try:
                    preset_num = int(actual_command.split("_")[1])
                    success = await self._device.select_preset(preset_num)
                    self.attributes["last_result"] = f"Preset {preset_num}" if success else "Failed"
                except (ValueError, IndexError):
                    self.attributes["last_result"] = "Invalid preset"
                    return StatusCodes.BAD_REQUEST

            # Grouping commands
            elif actual_command == "LEAVE_GROUP":
                success = await self._device.leave_group()
                self.attributes["last_result"] = "Left group" if success else "Failed"

            else:
                _LOG.warning("[%s] Unsupported remote command: %s", self.id, actual_command)
                self.attributes["last_result"] = f"Unknown command: {actual_command}"
                return StatusCodes.NOT_IMPLEMENTED

            return StatusCodes.OK if success else StatusCodes.SERVER_ERROR

        except Exception as err:
            _LOG.error("[%s] Remote command error: %s", self.id, err)
            self.attributes["last_result"] = f"Error: {err}"
            return StatusCodes.SERVER_ERROR
