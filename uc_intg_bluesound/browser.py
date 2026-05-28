"""
Bluesound media browser.

:copyright: (c) 2026 by Meir Miyara.
:license: MPL-2.0, see LICENSE for more details.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from ucapi import StatusCodes
from ucapi.api_definitions import Pagination
from ucapi.media_player import (
    BrowseMediaItem,
    BrowseOptions,
    BrowseResults,
    MediaClass,
    MediaContentType,
)

if TYPE_CHECKING:
    from uc_intg_bluesound.device import BluesoundDevice

_LOG = logging.getLogger(__name__)


async def browse(device: BluesoundDevice, options: BrowseOptions) -> BrowseResults | StatusCodes:
    media_id = options.media_id if hasattr(options, "media_id") else None

    if not media_id or media_id == "root":
        return await _browse_root(device)

    if media_id == "presets":
        return await _browse_presets(device)

    if media_id == "queue":
        return await _browse_queue(device)

    if media_id.startswith("preset_"):
        return StatusCodes.NOT_FOUND

    return StatusCodes.NOT_FOUND


async def _browse_root(device: BluesoundDevice) -> BrowseResults:
    items = []

    preset_thumbnail = None
    if device.presets:
        first_preset = device.presets[0]
        preset_thumbnail = first_preset.get("image") or None

    items.append(BrowseMediaItem(
        title="Presets",
        media_class=MediaClass.PLAYLIST,
        media_type="directory",
        media_id="presets",
        can_browse=True,
        can_play=False,
        thumbnail=preset_thumbnail,
    ))

    items.append(BrowseMediaItem(
        title="Queue",
        media_class=MediaClass.TRACK,
        media_type="directory",
        media_id="queue",
        can_browse=True,
        can_play=False,
        thumbnail="icon://uc:music",
    ))

    return BrowseResults(
        media=BrowseMediaItem(
            title="Bluesound",
            media_class=MediaClass.DIRECTORY,
            media_type="root",
            media_id="root",
            can_browse=True,
            items=items,
        ),
        pagination=Pagination(page=1, limit=len(items), count=len(items)),
    )


async def _browse_presets(device: BluesoundDevice) -> BrowseResults:
    presets = device.presets
    if not presets:
        presets = await device._fetch_presets()
        device._presets = presets

    items = []
    for preset in presets:
        preset_id = preset.get("id", "")
        preset_name = preset.get("name", "")
        preset_image = preset.get("image", "")

        if not preset_id or not preset_name:
            continue

        items.append(BrowseMediaItem(
            title=preset_name,
            media_class=MediaClass.RADIO,
            media_type=MediaContentType.RADIO,
            media_id=f"preset_{preset_id}",
            can_browse=False,
            can_play=True,
            thumbnail=preset_image if preset_image else "icon://uc:music",
        ))

    return BrowseResults(
        media=BrowseMediaItem(
            title="Presets",
            media_class=MediaClass.PLAYLIST,
            media_type="directory",
            media_id="presets",
            can_browse=True,
            items=items,
        ),
        pagination=Pagination(page=1, limit=len(items), count=len(items)),
    )


async def _browse_queue(device: BluesoundDevice) -> BrowseResults:
    queue_items = await device.fetch_queue()

    items = []
    for idx, song in enumerate(queue_items):
        title = song.get("title", song.get("fn", f"Track {idx + 1}"))
        artist = song.get("art", "")
        album = song.get("alb", "")
        image = song.get("image", "")
        song_id = song.get("songid", song.get("id", str(idx)))

        items.append(BrowseMediaItem(
            title=title,
            media_class=MediaClass.TRACK,
            media_type=MediaContentType.TRACK,
            media_id=f"queue_{song_id}",
            can_browse=False,
            can_play=True,
            thumbnail=image if image else None,
            artist=artist if artist else None,
            album=album if album else None,
        ))

    return BrowseResults(
        media=BrowseMediaItem(
            title="Queue",
            media_class=MediaClass.TRACK,
            media_type="directory",
            media_id="queue",
            can_browse=True,
            items=items,
        ),
        pagination=Pagination(page=1, limit=len(items), count=len(items)),
    )
