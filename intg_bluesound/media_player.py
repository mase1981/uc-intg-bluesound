"""
Bluesound Media Player entity.

:copyright: (c) 2026 by Meir Miyara.
:license: MPL-2.0, see LICENSE for more details.
"""

import logging
from typing import Any
from ucapi import StatusCodes
from ucapi.media_player import (
    Attributes,
    Commands,
    DeviceClasses,
    Features,
    MediaPlayer,
    States,
)
from intg_bluesound.config import BluesoundConfig
from intg_bluesound.device import BluesoundDevice

_LOG = logging.getLogger(__name__)


class BluesoundMediaPlayer(MediaPlayer):
    """Media player entity for Bluesound BluOS players."""

    def __init__(self, device_config: BluesoundConfig, device: BluesoundDevice):
        """Initialize with device reference."""
        self._device = device
        self._device_config = device_config

        entity_id = f"media_player.{device_config.identifier}"

        super().__init__(
            entity_id,
            device_config.name,
            [
                Features.PLAY_PAUSE,
                Features.STOP,
                Features.NEXT,
                Features.PREVIOUS,
                Features.VOLUME,
                Features.VOLUME_UP_DOWN,
                Features.MUTE_TOGGLE,
                Features.MUTE,
                Features.UNMUTE,
                Features.SHUFFLE,
                Features.REPEAT,
                Features.SEEK,
                Features.MEDIA_TITLE,
                Features.MEDIA_ARTIST,
                Features.MEDIA_ALBUM,
                Features.MEDIA_IMAGE_URL,
                Features.MEDIA_POSITION,
                Features.MEDIA_DURATION,
            ],
            {
                Attributes.STATE: States.UNAVAILABLE,
                Attributes.VOLUME: 0,
                Attributes.MUTED: False,
                Attributes.SHUFFLE: False,
                Attributes.REPEAT: "OFF",
            },
            device_class=DeviceClasses.SPEAKER,
            cmd_handler=self.handle_command,
        )

    async def handle_command(
        self, entity: MediaPlayer, cmd_id: str, params: dict[str, Any] | None
    ) -> StatusCodes:
        """Handle commands - direct device reference, no global state!"""
        _LOG.info("[%s] Command: %s %s", self.id, cmd_id, params or "")

        try:
            if cmd_id == Commands.PLAY_PAUSE:
                success = await self._device.play_pause()
                return StatusCodes.OK if success else StatusCodes.SERVER_ERROR

            elif cmd_id == Commands.STOP:
                success = await self._device.stop()
                return StatusCodes.OK if success else StatusCodes.SERVER_ERROR

            elif cmd_id == Commands.NEXT:
                success = await self._device.next_track()
                return StatusCodes.OK if success else StatusCodes.SERVER_ERROR

            elif cmd_id == Commands.PREVIOUS:
                success = await self._device.previous_track()
                return StatusCodes.OK if success else StatusCodes.SERVER_ERROR

            elif cmd_id == Commands.VOLUME:
                if params and "volume" in params:
                    # UC sends volume as 0.0-1.0, BluOS expects 0-100
                    volume_percent = int(float(params["volume"]) * 100)
                    success = await self._device.set_volume(volume_percent)
                    return StatusCodes.OK if success else StatusCodes.SERVER_ERROR
                return StatusCodes.BAD_REQUEST

            elif cmd_id == Commands.VOLUME_UP:
                success = await self._device.volume_up()
                return StatusCodes.OK if success else StatusCodes.SERVER_ERROR

            elif cmd_id == Commands.VOLUME_DOWN:
                success = await self._device.volume_down()
                return StatusCodes.OK if success else StatusCodes.SERVER_ERROR

            elif cmd_id == Commands.MUTE_TOGGLE:
                success = await self._device.mute_toggle()
                return StatusCodes.OK if success else StatusCodes.SERVER_ERROR

            elif cmd_id == Commands.MUTE:
                success = await self._device.mute(True)
                return StatusCodes.OK if success else StatusCodes.SERVER_ERROR

            elif cmd_id == Commands.UNMUTE:
                success = await self._device.mute(False)
                return StatusCodes.OK if success else StatusCodes.SERVER_ERROR

            elif cmd_id == Commands.SHUFFLE:
                if params and "shuffle" in params:
                    success = await self._device.set_shuffle(bool(params["shuffle"]))
                    return StatusCodes.OK if success else StatusCodes.SERVER_ERROR
                return StatusCodes.BAD_REQUEST

            elif cmd_id == Commands.REPEAT:
                if params and "repeat" in params:
                    success = await self._device.set_repeat(params["repeat"])
                    return StatusCodes.OK if success else StatusCodes.SERVER_ERROR
                return StatusCodes.BAD_REQUEST

            elif cmd_id == Commands.SEEK:
                if params and "media_position" in params:
                    position = int(params["media_position"])
                    success = await self._device.seek(position)
                    return StatusCodes.OK if success else StatusCodes.SERVER_ERROR
                return StatusCodes.BAD_REQUEST

            return StatusCodes.NOT_IMPLEMENTED

        except Exception as err:
            _LOG.error("[%s] Command error: %s", self.id, err)
            return StatusCodes.SERVER_ERROR
