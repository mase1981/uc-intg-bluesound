"""
Bluesound device implementation for Unfolded Circle integration.

:copyright: (c) 2026 by Meir Miyara.
:license: MPL-2.0, see LICENSE for more details.
"""

import asyncio
import logging
from typing import Any
from xml.etree import ElementTree as ET
from time import time

import aiohttp
from ucapi_framework import PollingDevice, DeviceEvents

from uc_intg_bluesound.config import BluesoundConfig

_LOG = logging.getLogger(__name__)


class BluesoundDevice(PollingDevice):
    """Bluesound BluOS player implementation using PollingDevice."""

    def __init__(self, device_config: BluesoundConfig, **kwargs: Any) -> None:
        super().__init__(device_config, poll_interval=5, **kwargs)
        self._device_config = device_config
        self._session: aiohttp.ClientSession | None = None
        self._raw_state: dict[str, Any] = {}
        self._sync_status: dict[str, Any] = {}
        self._etag: str | None = None
        self._base_url = f"http://{device_config.host}:{device_config.port}"

        self._state: str = "UNAVAILABLE"
        self._volume: int = 0
        self._muted: bool = False
        self._shuffle: bool = False
        self._repeat: str = "OFF"
        self._title: str = ""
        self._artist: str = ""
        self._album: str = ""
        self._image_url: str = ""
        self._source: str = ""
        self._position: int | None = None
        self._duration: int | None = None

        self._is_leader: bool = False
        self._is_grouped: bool = False
        self._group_name: str | None = None
        self._presets: list[dict[str, Any]] = []

        self._volume_queue: asyncio.Queue = asyncio.Queue()
        self._mute_queue: asyncio.Queue = asyncio.Queue()
        self._volume_worker_task: asyncio.Task | None = None
        self._mute_worker_task: asyncio.Task | None = None
        self._target_volume: int | None = None
        self._target_mute: bool | None = None
        self._last_volume_update: tuple[int, float] | None = None
        self._volume_debounce_ms = 100
        self._volume_before_mute: int | None = None

    @property
    def identifier(self) -> str:
        return self._device_config.identifier

    @property
    def name(self) -> str:
        return self._device_config.name

    @property
    def address(self) -> str:
        return self._device_config.host

    @property
    def log_id(self) -> str:
        return f"{self.name} ({self.address})"

    @property
    def state(self) -> str:
        return self._state

    @property
    def volume(self) -> int:
        return self._volume

    @property
    def muted(self) -> bool:
        return self._muted

    @property
    def shuffle(self) -> bool:
        return self._shuffle

    @property
    def repeat(self) -> str:
        return self._repeat

    @property
    def title(self) -> str:
        return self._title

    @property
    def artist(self) -> str:
        return self._artist

    @property
    def album(self) -> str:
        return self._album

    @property
    def image_url(self) -> str:
        return self._image_url

    @property
    def source(self) -> str:
        return self._source

    @property
    def position(self) -> int | None:
        return self._position

    @property
    def duration(self) -> int | None:
        return self._duration

    @property
    def is_grouped(self) -> bool:
        return self._is_grouped

    @property
    def is_leader(self) -> bool:
        return self._is_leader

    @property
    def group_name(self) -> str | None:
        return self._group_name

    @property
    def presets(self) -> list[dict[str, Any]]:
        return self._presets

    async def establish_connection(self) -> aiohttp.ClientSession:
        _LOG.info("[%s] Establishing connection", self.log_id)
        timeout = aiohttp.ClientTimeout(total=10)
        self._session = aiohttp.ClientSession(timeout=timeout)

        if not await self._test_connection():
            await self._session.close()
            self._session = None
            raise ConnectionError(f"Cannot reach {self._device_config.host}:{self._device_config.port}")

        try:
            await self._update_state()
        except ConnectionError:
            _LOG.warning("[%s] Initial state query failed, using defaults", self.log_id)

        self._presets = await self._fetch_presets()
        self._volume_worker_task = asyncio.create_task(self._volume_worker())
        self._mute_worker_task = asyncio.create_task(self._mute_worker())
        self._state = "ON"
        _LOG.info("[%s] Connection established", self.log_id)
        return self._session

    async def _test_connection(self) -> bool:
        try:
            async with self._session.get(f"{self._base_url}/Status", timeout=aiohttp.ClientTimeout(total=5)) as resp:
                return resp.status == 200
        except Exception:
            return False

    async def poll_device(self) -> None:
        if not self._session:
            return
        try:
            await self._update_state()
            self.push_update()
        except Exception as err:
            _LOG.debug("[%s] Poll error: %s", self.log_id, err)
            if self._state != "UNAVAILABLE":
                self._state = "UNAVAILABLE"
                self.events.emit(DeviceEvents.DISCONNECTED, self.identifier)

    async def _update_state(self) -> None:
        status_changed = await self._fetch_status()
        sync_changed = await self._fetch_sync_status()

        if not self._raw_state:
            raise ConnectionError("Failed to get device status")

        if status_changed:
            current_volume = int(self._raw_state.get("volume", "0"))
            current_mute = self._raw_state.get("mute", "0") == "1"

            if self._target_volume is not None and current_volume == self._target_volume:
                self._target_volume = None
            if self._target_mute is not None and current_mute == self._target_mute:
                self._target_mute = None

        self._parse_state()

    def _parse_state(self) -> None:
        state_str = self._raw_state.get("state", "").lower()
        if state_str in ("play", "stream"):
            self._state = "PLAYING"
        elif state_str == "pause":
            self._state = "PAUSED"
        elif state_str == "stop":
            self._state = "ON"
        else:
            self._state = "ON"

        raw_volume = int(self._raw_state.get("volume", "0"))
        raw_mute = self._raw_state.get("mute", "0") == "1"

        current_time = time()
        if self._last_volume_update is not None:
            last_vol, last_time = self._last_volume_update
            time_diff_ms = (current_time - last_time) * 1000
            if last_vol == raw_volume and time_diff_ms < self._volume_debounce_ms:
                return
        self._last_volume_update = (raw_volume, current_time)

        self._volume = raw_volume
        self._muted = raw_mute
        self._shuffle = self._raw_state.get("shuffle", "0") == "1"

        repeat_val = self._raw_state.get("repeat", "0")
        if repeat_val == "2":
            self._repeat = "ONE"
        elif repeat_val == "1":
            self._repeat = "ALL"
        else:
            self._repeat = "OFF"

        self._title = self._raw_state.get("title1", self._raw_state.get("name", ""))
        self._artist = self._raw_state.get("artist", self._raw_state.get("title2", ""))
        self._album = self._raw_state.get("album", self._raw_state.get("title3", ""))
        self._image_url = self._raw_state.get("image", "")
        self._source = self._raw_state.get("service", "")

        try:
            secs = self._raw_state.get("secs")
            self._position = int(secs) if secs is not None else None
        except (ValueError, TypeError):
            self._position = None

        try:
            totlen = self._raw_state.get("totlen")
            self._duration = int(totlen) if totlen is not None else None
        except (ValueError, TypeError):
            self._duration = None

        self._is_leader = False
        self._is_grouped = False
        self._group_name = None

        if self._sync_status:
            if "follower" in str(self._sync_status).lower():
                self._is_leader = True
                self._is_grouped = True
            if "leader" in str(self._sync_status).lower():
                self._is_grouped = True
            self._group_name = self._sync_status.get("group", self._sync_status.get("name"))

    async def _fetch_status(self) -> bool:
        try:
            params = {"etag": self._etag, "timeout": "5"} if self._etag else {}
            async with self._session.get(f"{self._base_url}/Status", params=params) as resp:
                if resp.status == 200:
                    text = await resp.text()
                    new_state = self._parse_xml(text)
                    if "etag" in new_state:
                        self._etag = new_state["etag"]
                    if new_state != self._raw_state:
                        self._raw_state = new_state
                        return True
                    return False
                return False
        except asyncio.TimeoutError:
            return False
        except Exception as err:
            _LOG.error("[%s] Status fetch error: %s", self.log_id, err)
            raise ConnectionError(f"Status fetch failed: {err}") from err

    async def _fetch_sync_status(self) -> bool:
        try:
            async with self._session.get(f"{self._base_url}/SyncStatus") as resp:
                if resp.status == 200:
                    text = await resp.text()
                    new_sync = self._parse_xml(text)
                    if new_sync != self._sync_status:
                        self._sync_status = new_sync
                        return True
                    return False
                return False
        except Exception as err:
            _LOG.debug("[%s] SyncStatus fetch error: %s", self.log_id, err)
            return False

    def _parse_xml(self, xml_text: str) -> dict[str, Any]:
        try:
            root = ET.fromstring(xml_text)
            state: dict[str, Any] = {}
            for elem in root.iter():
                tag = elem.tag.split('}')[-1] if '}' in elem.tag else elem.tag
                if elem.text and elem.text.strip():
                    state[tag] = elem.text.strip()
                for attr_name, attr_value in elem.attrib.items():
                    state[f"{tag}_{attr_name}"] = attr_value
            return state
        except Exception as err:
            _LOG.error("[%s] XML parse error: %s", self.log_id, err)
            return {}

    async def _fetch_presets(self) -> list[dict[str, Any]]:
        if not self._session:
            return []
        try:
            async with self._session.get(f"{self._base_url}/Presets") as resp:
                if resp.status == 200:
                    text = await resp.text()
                    return self._parse_presets_xml(text)
                return []
        except Exception as err:
            _LOG.error("[%s] Presets fetch error: %s", self.log_id, err)
            return []

    def _parse_presets_xml(self, xml_text: str) -> list[dict[str, Any]]:
        try:
            root = ET.fromstring(xml_text)
            presets = []
            for preset in root.findall(".//preset"):
                preset_data = {
                    "id": preset.get("id"),
                    "name": preset.get("name"),
                    "url": preset.get("url"),
                    "image": preset.get("image", ""),
                }
                if preset_data["id"] and preset_data["name"]:
                    presets.append(preset_data)
            return presets
        except Exception as err:
            _LOG.error("[%s] Presets XML parse error: %s", self.log_id, err)
            return []

    async def disconnect(self) -> None:
        if self._volume_worker_task:
            await self._volume_queue.put(None)
            self._volume_worker_task.cancel()
            try:
                await self._volume_worker_task
            except asyncio.CancelledError:
                pass
            self._volume_worker_task = None

        if self._mute_worker_task:
            await self._mute_queue.put(None)
            self._mute_worker_task.cancel()
            try:
                await self._mute_worker_task
            except asyncio.CancelledError:
                pass
            self._mute_worker_task = None

        if self._session:
            await self._session.close()
            self._session = None
        self._raw_state = {}
        self._state = "UNAVAILABLE"
        await super().disconnect()

    async def _volume_worker(self) -> None:
        while True:
            try:
                volume = await self._volume_queue.get()
                if volume is None:
                    break
                await self._send_command("Volume", {"level": str(volume)})
                await asyncio.sleep(0.1)
                self._volume_queue.task_done()
            except asyncio.CancelledError:
                break
            except Exception as err:
                _LOG.error("[%s] Volume worker error: %s", self.log_id, err)
                self._volume_queue.task_done()

    async def _mute_worker(self) -> None:
        while True:
            try:
                mute_value = await self._mute_queue.get()
                if mute_value is None:
                    break
                await self._send_command("Volume", {"mute": "1" if mute_value else "0"})
                await asyncio.sleep(0.1)
                self._mute_queue.task_done()
            except asyncio.CancelledError:
                break
            except Exception as err:
                _LOG.error("[%s] Mute worker error: %s", self.log_id, err)
                self._mute_queue.task_done()

    async def _send_command(self, endpoint: str, params: dict[str, Any] | None = None) -> bool:
        if not self._session:
            return False
        try:
            url = f"{self._base_url}/{endpoint}"
            async with self._session.get(url, params=params or {}) as resp:
                return resp.status == 200
        except Exception as err:
            _LOG.error("[%s] Command error %s: %s", self.log_id, endpoint, err)
            return False

    async def play(self) -> bool:
        return await self._send_command("Play")

    async def pause(self) -> bool:
        return await self._send_command("Pause")

    async def stop(self) -> bool:
        return await self._send_command("Pause")

    async def play_pause(self) -> bool:
        return await self._send_command("Pause", {"toggle": "1"})

    async def next_track(self) -> bool:
        return await self._send_command("Skip")

    async def previous_track(self) -> bool:
        return await self._send_command("Back")

    async def set_volume(self, volume: int) -> bool:
        volume = max(0, min(100, volume))
        try:
            await self._volume_queue.put(volume)
            return True
        except Exception:
            return False

    async def volume_up(self) -> bool:
        current_mute = self._raw_state.get("mute", "0") == "1"
        if current_mute or self._target_mute is True:
            await self.set_mute(False)

        if self._target_volume is not None:
            current = self._target_volume
        else:
            current_vol = int(self._raw_state.get("volume", "50"))
            if current_vol == 0 and self._volume_before_mute is not None:
                current = self._volume_before_mute
            else:
                current = current_vol

        new_volume = min(100, current + 1)
        self._target_volume = new_volume
        return await self.set_volume(new_volume)

    async def volume_down(self) -> bool:
        current_mute = self._raw_state.get("mute", "0") == "1"
        if current_mute or self._target_mute is True:
            await self.set_mute(False)

        if self._target_volume is not None:
            current = self._target_volume
        else:
            current_vol = int(self._raw_state.get("volume", "50"))
            if current_vol == 0 and self._volume_before_mute is not None:
                current = self._volume_before_mute
            else:
                current = current_vol

        new_volume = max(0, current - 1)
        self._target_volume = new_volume
        return await self.set_volume(new_volume)

    async def set_mute(self, muted: bool) -> bool:
        if muted and self._volume_before_mute is None:
            current_vol = int(self._raw_state.get("volume", "50"))
            if current_vol > 0:
                self._volume_before_mute = current_vol

        if not muted:
            self._volume_before_mute = None

        try:
            await self._mute_queue.put(muted)
            return True
        except Exception:
            return False

    async def mute_toggle(self) -> bool:
        if self._target_mute is not None:
            current_mute = self._target_mute
        else:
            current_mute = self._raw_state.get("mute", "0") == "1"

        new_mute = not current_mute
        self._target_mute = new_mute
        return await self.set_mute(new_mute)

    async def set_shuffle(self, shuffle: bool) -> bool:
        return await self._send_command("Shuffle", {"state": "1" if shuffle else "0"})

    async def set_repeat(self, repeat: str) -> bool:
        repeat_map = {"OFF": "0", "ALL": "1", "ONE": "2"}
        value = repeat_map.get(repeat.upper(), "0")
        return await self._send_command("Repeat", {"state": value})

    async def seek(self, position: int) -> bool:
        return await self._send_command("Play", {"seek": str(position)})

    async def select_preset(self, preset_id: int) -> bool:
        return await self._send_command("Preset", {"id": str(preset_id)})

    async def clear_queue(self) -> bool:
        return await self._send_command("Clear")

    async def play_url(self, url: str) -> bool:
        return await self._send_command("Play", {"url": url})

    async def add_slave(self, slave_ip: str, slave_port: int = 11000) -> bool:
        return await self._send_command("AddSlave", {"slave": f"{slave_ip}:{slave_port}"})

    async def remove_slave(self, slave_ip: str, slave_port: int = 11000) -> bool:
        return await self._send_command("RemoveSlave", {"slave": f"{slave_ip}:{slave_port}"})

    async def leave_group(self) -> bool:
        return await self._send_command("Leave")

    async def fetch_queue(self) -> list[dict[str, Any]]:
        if not self._session:
            return []
        try:
            async with self._session.get(f"{self._base_url}/Playlist") as resp:
                if resp.status == 200:
                    text = await resp.text()
                    return self._parse_queue_xml(text)
                return []
        except Exception as err:
            _LOG.error("[%s] Queue fetch error: %s", self.log_id, err)
            return []

    def _parse_queue_xml(self, xml_text: str) -> list[dict[str, Any]]:
        try:
            root = ET.fromstring(xml_text)
            items = []
            for song in root.findall(".//song"):
                song_data: dict[str, Any] = {}
                for elem in song:
                    tag = elem.tag
                    if elem.text and elem.text.strip():
                        song_data[tag] = elem.text.strip()
                song_data.update(song.attrib)
                if song_data.get("title") or song_data.get("fn"):
                    items.append(song_data)
            return items
        except Exception as err:
            _LOG.error("[%s] Queue XML parse error: %s", self.log_id, err)
            return []
