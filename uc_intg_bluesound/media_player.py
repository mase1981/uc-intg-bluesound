"""
Bluesound media player entity.

:copyright: (c) 2026 by Meir Miyara.
:license: MPL-2.0, see LICENSE for more details.
"""

from __future__ import annotations

import logging
from typing import Any, TYPE_CHECKING

from ucapi import media_player, StatusCodes
from ucapi.media_player import BrowseOptions, BrowseResults, SearchOptions, SearchResults
from ucapi_framework import MediaPlayerEntity

from uc_intg_bluesound import browser

if TYPE_CHECKING:
    from uc_intg_bluesound.config import BluesoundConfig
    from uc_intg_bluesound.device import BluesoundDevice

_LOG = logging.getLogger(__name__)

FEATURES = [
    media_player.Features.ON_OFF,
    media_player.Features.PLAY_PAUSE,
    media_player.Features.STOP,
    media_player.Features.NEXT,
    media_player.Features.PREVIOUS,
    media_player.Features.VOLUME,
    media_player.Features.VOLUME_UP_DOWN,
    media_player.Features.MUTE_TOGGLE,
    media_player.Features.MUTE,
    media_player.Features.UNMUTE,
    media_player.Features.SHUFFLE,
    media_player.Features.REPEAT,
    media_player.Features.SEEK,
    media_player.Features.MEDIA_TITLE,
    media_player.Features.MEDIA_ARTIST,
    media_player.Features.MEDIA_ALBUM,
    media_player.Features.MEDIA_IMAGE_URL,
    media_player.Features.MEDIA_POSITION,
    media_player.Features.MEDIA_DURATION,
    media_player.Features.MEDIA_TYPE,
    media_player.Features.PLAY_MEDIA,
    media_player.Features.BROWSE_MEDIA,
    media_player.Features.SELECT_SOURCE,
]


class BluesoundMediaPlayer(MediaPlayerEntity):
    """Media player entity for Bluesound BluOS players."""

    def __init__(self, device_config: BluesoundConfig, device: BluesoundDevice) -> None:
        self._device = device
        entity_id = f"media_player.{device_config.identifier}"
        super().__init__(
            entity_id,
            device_config.name,
            features=FEATURES,
            attributes={
                media_player.Attributes.STATE: media_player.States.UNKNOWN,
                media_player.Attributes.VOLUME: 0,
                media_player.Attributes.MUTED: False,
                media_player.Attributes.SHUFFLE: False,
                media_player.Attributes.REPEAT: media_player.RepeatMode.OFF,
                media_player.Attributes.MEDIA_TYPE: "music",
            },
            device_class=media_player.DeviceClasses.SPEAKER,
            cmd_handler=self._handle_command,
        )
        self.subscribe_to_device(device)

    async def sync_state(self) -> None:
        d = self._device
        if d.state == "UNAVAILABLE":
            self.update({media_player.Attributes.STATE: media_player.States.UNAVAILABLE})
            return

        state = self.map_entity_states(d.state)
        attrs: dict[str, Any] = {
            media_player.Attributes.STATE: state,
            media_player.Attributes.VOLUME: d.volume,
            media_player.Attributes.MUTED: d.muted,
            media_player.Attributes.SHUFFLE: d.shuffle,
            media_player.Attributes.REPEAT: _repeat_to_uc(d.repeat),
            media_player.Attributes.MEDIA_TYPE: "music",
        }

        if d.title:
            attrs[media_player.Attributes.MEDIA_TITLE] = d.title
        if d.artist:
            attrs[media_player.Attributes.MEDIA_ARTIST] = d.artist
        if d.album:
            attrs[media_player.Attributes.MEDIA_ALBUM] = d.album
        if d.image_url:
            attrs[media_player.Attributes.MEDIA_IMAGE_URL] = d.image_url
        if d.source:
            attrs[media_player.Attributes.SOURCE] = d.source
        if d.position is not None:
            attrs[media_player.Attributes.MEDIA_POSITION] = d.position
        if d.duration is not None:
            attrs[media_player.Attributes.MEDIA_DURATION] = d.duration

        self.update(attrs)

    async def browse(self, options: BrowseOptions) -> BrowseResults | StatusCodes:
        if not self._device._session:
            return StatusCodes.SERVICE_UNAVAILABLE
        return await browser.browse(self._device, options)

    async def search(self, options: SearchOptions) -> SearchResults | StatusCodes:
        return StatusCodes.NOT_IMPLEMENTED

    async def _handle_command(
        self, entity: media_player.MediaPlayer, cmd_id: str, params: dict[str, Any] | None
    ) -> StatusCodes:
        try:
            return await self._dispatch_command(cmd_id, params)
        except Exception as err:
            _LOG.error("[%s] Command error: %s", self.id, err)
            return StatusCodes.SERVER_ERROR

    async def _dispatch_command(self, cmd_id: str, params: dict[str, Any] | None) -> StatusCodes:
        d = self._device

        if cmd_id == media_player.Commands.ON:
            return StatusCodes.OK

        if cmd_id == media_player.Commands.OFF:
            ok = await d.stop()
            return StatusCodes.OK if ok else StatusCodes.SERVER_ERROR

        if cmd_id == media_player.Commands.PLAY_PAUSE:
            ok = await d.play_pause()
            return StatusCodes.OK if ok else StatusCodes.SERVER_ERROR

        if cmd_id == media_player.Commands.STOP:
            ok = await d.stop()
            return StatusCodes.OK if ok else StatusCodes.SERVER_ERROR

        if cmd_id == media_player.Commands.NEXT:
            ok = await d.next_track()
            return StatusCodes.OK if ok else StatusCodes.SERVER_ERROR

        if cmd_id == media_player.Commands.PREVIOUS:
            ok = await d.previous_track()
            return StatusCodes.OK if ok else StatusCodes.SERVER_ERROR

        if cmd_id == media_player.Commands.VOLUME:
            if params and "volume" in params:
                ok = await d.set_volume(int(params["volume"]))
                return StatusCodes.OK if ok else StatusCodes.SERVER_ERROR
            return StatusCodes.BAD_REQUEST

        if cmd_id == media_player.Commands.VOLUME_UP:
            ok = await d.volume_up()
            return StatusCodes.OK if ok else StatusCodes.SERVER_ERROR

        if cmd_id == media_player.Commands.VOLUME_DOWN:
            ok = await d.volume_down()
            return StatusCodes.OK if ok else StatusCodes.SERVER_ERROR

        if cmd_id == media_player.Commands.MUTE_TOGGLE:
            ok = await d.mute_toggle()
            return StatusCodes.OK if ok else StatusCodes.SERVER_ERROR

        if cmd_id == media_player.Commands.MUTE:
            ok = await d.set_mute(True)
            return StatusCodes.OK if ok else StatusCodes.SERVER_ERROR

        if cmd_id == media_player.Commands.UNMUTE:
            ok = await d.set_mute(False)
            return StatusCodes.OK if ok else StatusCodes.SERVER_ERROR

        if cmd_id == media_player.Commands.SHUFFLE:
            ok = await d.set_shuffle(not d.shuffle)
            return StatusCodes.OK if ok else StatusCodes.SERVER_ERROR

        if cmd_id == media_player.Commands.REPEAT:
            cycle = {"OFF": "ALL", "ALL": "ONE", "ONE": "OFF"}
            new_mode = cycle.get(d.repeat, "OFF")
            ok = await d.set_repeat(new_mode)
            return StatusCodes.OK if ok else StatusCodes.SERVER_ERROR

        if cmd_id == media_player.Commands.SEEK:
            if params and "media_position" in params:
                ok = await d.seek(int(params["media_position"]))
                return StatusCodes.OK if ok else StatusCodes.SERVER_ERROR
            return StatusCodes.BAD_REQUEST

        if cmd_id == media_player.Commands.SELECT_SOURCE:
            return StatusCodes.NOT_IMPLEMENTED

        if cmd_id == media_player.Commands.PLAY_MEDIA:
            return await self._handle_play_media(params)

        return StatusCodes.NOT_IMPLEMENTED

    async def _handle_play_media(self, params: dict[str, Any] | None) -> StatusCodes:
        if not params:
            return StatusCodes.BAD_REQUEST

        media_id = params.get("media_id", "")
        if not media_id:
            return StatusCodes.BAD_REQUEST

        if media_id.startswith("preset_"):
            try:
                preset_id = int(media_id[7:])
                ok = await self._device.select_preset(preset_id)
                return StatusCodes.OK if ok else StatusCodes.SERVER_ERROR
            except ValueError:
                return StatusCodes.BAD_REQUEST

        if media_id.startswith("queue_"):
            ok = await self._device.play()
            return StatusCodes.OK if ok else StatusCodes.SERVER_ERROR

        ok = await self._device.play_url(media_id)
        return StatusCodes.OK if ok else StatusCodes.SERVER_ERROR


def _repeat_to_uc(repeat: str) -> media_player.RepeatMode:
    mapping = {
        "OFF": media_player.RepeatMode.OFF,
        "ALL": media_player.RepeatMode.ALL,
        "ONE": media_player.RepeatMode.ONE,
    }
    return mapping.get(repeat, media_player.RepeatMode.OFF)
