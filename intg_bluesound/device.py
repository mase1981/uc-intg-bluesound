"""
Bluesound device implementation for Unfolded Circle integration.

:copyright: (c) 2026 by Meir Miyara.
:license: MPL-2.0, see LICENSE for more details.
"""

import asyncio
import logging
from typing import Any
from xml.etree import ElementTree as ET
import aiohttp
from ucapi_framework import PollingDevice, DeviceEvents
from ucapi.media_player import Attributes as MediaAttributes, States as MediaStates
from ucapi.sensor import Attributes as SensorAttributes
from ucapi.remote import Attributes as RemoteAttributes
from intg_bluesound.config import BluesoundConfig

_LOG = logging.getLogger(__name__)


class BluesoundDevice(PollingDevice):
    """Bluesound BluOS player implementation using PollingDevice."""

    def __init__(self, device_config: BluesoundConfig, **kwargs):
        # Poll every 5 seconds for responsive updates
        super().__init__(device_config, poll_interval=5, **kwargs)
        self._device_config = device_config
        self._session: aiohttp.ClientSession | None = None
        self._state: dict[str, Any] = {}
        self._sync_status: dict[str, Any] = {}
        self._presets: list[dict[str, Any]] = []
        self._etag: str | None = None
        self._base_url = f"http://{device_config.host}:{device_config.port}"
        self._is_leader = False
        self._is_grouped = False
        self._group_name: str | None = None

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

    async def establish_connection(self) -> None:
        """Establish initial connection to device."""
        _LOG.info("[%s] Establishing connection", self.log_id)

        # Create aiohttp session with timeout
        timeout = aiohttp.ClientTimeout(total=10)
        self._session = aiohttp.ClientSession(timeout=timeout)

        # Perform initial status query to verify connectivity
        try:
            await self._fetch_status()
            await self._fetch_sync_status()
            _LOG.info("[%s] Connection established successfully", self.log_id)
        except Exception as err:
            _LOG.error("[%s] Failed to establish connection: %s", self.log_id, err)
            if self._session:
                await self._session.close()
                self._session = None
            raise

    async def poll_device(self) -> None:
        """Poll the device for status updates."""
        if not self._session:
            _LOG.warning("[%s] Session not initialized, skipping poll", self.log_id)
            return

        try:
            # Fetch both status and sync status
            status_changed = await self._fetch_status()
            sync_changed = await self._fetch_sync_status()

            # Emit update event if any state changed
            if status_changed or sync_changed:
                self._emit_update()

        except Exception as err:  # pylint: disable=broad-exception-caught
            _LOG.error("[%s] Poll error: %s", self.log_id, err)

    async def disconnect(self) -> None:
        """Disconnect and cleanup."""
        await super().disconnect()
        if self._session:
            await self._session.close()
            self._session = None
        self._state = {}
        self._sync_status = {}
        self._emit_update()

    async def _fetch_status(self) -> bool:
        """
        Fetch player status from /Status endpoint.
        Returns True if state changed.
        """
        try:
            # Use etag for efficient polling if available
            params = {"etag": self._etag, "timeout": "5"} if self._etag else {}

            async with self._session.get(f"{self._base_url}/Status", params=params) as resp:
                if resp.status == 200:
                    text = await resp.text()
                    new_state = self._parse_status_xml(text)

                    # Extract etag from response for next poll
                    if "etag" in new_state:
                        self._etag = new_state["etag"]

                    # Check if state actually changed
                    if new_state != self._state:
                        self._state = new_state
                        _LOG.debug("[%s] Status updated", self.log_id)
                        return True
                    return False
                else:
                    _LOG.warning("[%s] Status fetch failed: %s", self.log_id, resp.status)
                    return False

        except asyncio.TimeoutError:
            # Timeout is normal when using long polling
            return False
        except Exception as err:  # pylint: disable=broad-exception-caught
            _LOG.error("[%s] Status fetch error: %s", self.log_id, err)
            return False

    async def _fetch_sync_status(self) -> bool:
        """
        Fetch sync/grouping status from /SyncStatus endpoint.
        Returns True if state changed.
        """
        try:
            async with self._session.get(f"{self._base_url}/SyncStatus") as resp:
                if resp.status == 200:
                    text = await resp.text()
                    new_sync = self._parse_sync_status_xml(text)

                    if new_sync != self._sync_status:
                        self._sync_status = new_sync
                        _LOG.debug("[%s] Sync status updated", self.log_id)
                        return True
                    return False
                else:
                    _LOG.warning("[%s] SyncStatus fetch failed: %s", self.log_id, resp.status)
                    return False

        except Exception as err:  # pylint: disable=broad-exception-caught
            _LOG.error("[%s] SyncStatus fetch error: %s", self.log_id, err)
            return False

    def _parse_status_xml(self, xml_text: str) -> dict[str, Any]:
        """Parse XML status response into dict."""
        try:
            root = ET.fromstring(xml_text)
            state = {}

            # Extract all attributes and text values
            for elem in root.iter():
                # Get element tag (remove namespace if present)
                tag = elem.tag.split('}')[-1] if '}' in elem.tag else elem.tag

                # Get text value
                if elem.text and elem.text.strip():
                    state[tag] = elem.text.strip()

                # Get attributes
                for attr_name, attr_value in elem.attrib.items():
                    state[f"{tag}_{attr_name}"] = attr_value

            return state

        except Exception as err:  # pylint: disable=broad-exception-caught
            _LOG.error("[%s] XML parse error: %s", self.log_id, err)
            return {}

    def _parse_sync_status_xml(self, xml_text: str) -> dict[str, Any]:
        """Parse XML sync status response into dict."""
        try:
            root = ET.fromstring(xml_text)
            sync = {}

            # Extract sync info
            for elem in root.iter():
                tag = elem.tag.split('}')[-1] if '}' in elem.tag else elem.tag
                if elem.text and elem.text.strip():
                    sync[tag] = elem.text.strip()
                for attr_name, attr_value in elem.attrib.items():
                    sync[f"{tag}_{attr_name}"] = attr_value

            return sync

        except Exception as err:  # pylint: disable=broad-exception-caught
            _LOG.error("[%s] SyncStatus XML parse error: %s", self.log_id, err)
            return {}

    def _emit_update(self) -> None:
        """Emit entity update events for media player, remote, and sensors."""
        media_player_id = f"media_player.{self.identifier}"
        remote_id = f"remote.{self.identifier}"
        connection_sensor_id = f"sensor.{self.identifier}_connection"
        group_sensor_id = f"sensor.{self.identifier}_group"

        if not self._state or not self.is_connected:
            # Device unavailable - update all entities
            self.events.emit(
                DeviceEvents.UPDATE,
                media_player_id,
                {MediaAttributes.STATE: MediaStates.UNAVAILABLE}
            )
            self.events.emit(
                DeviceEvents.UPDATE,
                remote_id,
                {RemoteAttributes.STATE: "UNAVAILABLE"}
            )
            self.events.emit(
                DeviceEvents.UPDATE,
                connection_sensor_id,
                {
                    SensorAttributes.STATE: "Disconnected",
                    SensorAttributes.VALUE: "disconnected",
                }
            )
            return

        # Parse state information from BluOS status
        state_str = self._state.get("state", "").lower()

        # Map BluOS states to UC media player states
        if state_str in ("play", "stream"):
            state = MediaStates.PLAYING
        elif state_str == "pause":
            state = MediaStates.PAUSED
        elif state_str == "stop":
            state = MediaStates.IDLE
        else:
            state = MediaStates.IDLE

        # Extract playback info
        volume = int(self._state.get("volume", "0"))
        mute = self._state.get("mute", "0") == "1"
        shuffle = self._state.get("shuffle", "0") == "1"
        repeat = self._state.get("repeat", "0")

        # Map repeat: 0=off, 1=all, 2=one
        repeat_mode = "OFF"
        if repeat == "2":
            repeat_mode = "ONE"
        elif repeat == "1":
            repeat_mode = "ALL"

        # Extract media info
        title = self._state.get("title1", self._state.get("name", ""))
        artist = self._state.get("artist", self._state.get("title2", ""))
        album = self._state.get("album", self._state.get("title3", ""))
        image_url = self._state.get("image", "")

        # Get service/source name
        service = self._state.get("service", "")

        # Build media position info
        media_position = None
        media_duration = None
        try:
            secs = self._state.get("secs")
            totlen = self._state.get("totlen")
            if secs is not None:
                media_position = int(secs)
            if totlen is not None:
                media_duration = int(totlen)
        except (ValueError, TypeError):
            pass

        # Build attributes dict
        attrs = {
            MediaAttributes.STATE: state,
            MediaAttributes.VOLUME: volume,
            MediaAttributes.MUTED: mute,
            MediaAttributes.SHUFFLE: shuffle,
            MediaAttributes.REPEAT: repeat_mode,
        }

        if title:
            attrs[MediaAttributes.MEDIA_TITLE] = title
        if artist:
            attrs[MediaAttributes.MEDIA_ARTIST] = artist
        if album:
            attrs[MediaAttributes.MEDIA_ALBUM] = album
        if image_url:
            attrs[MediaAttributes.MEDIA_IMAGE_URL] = image_url
        if service:
            attrs[MediaAttributes.SOURCE] = service
        if media_position is not None:
            attrs[MediaAttributes.MEDIA_POSITION] = media_position
        if media_duration is not None:
            attrs[MediaAttributes.MEDIA_DURATION] = media_duration

        # Check grouping status from SyncStatus
        self._is_leader = False
        self._is_grouped = False
        self._group_name = None

        if self._sync_status:
            # If player has followers, it's a leader
            if "follower" in str(self._sync_status).lower():
                self._is_leader = True
                self._is_grouped = True
            # If player has a leader, it's grouped
            if "leader" in str(self._sync_status).lower():
                self._is_grouped = True

            # Try to extract group name
            self._group_name = self._sync_status.get("group", self._sync_status.get("name"))

        _LOG.debug("[%s] Emitting update: %s", self.log_id, state)
        self.events.emit(DeviceEvents.UPDATE, media_player_id, attrs)

        # Update Remote
        remote_state = "ON" if state != MediaStates.UNAVAILABLE else "OFF"
        self.events.emit(
            DeviceEvents.UPDATE,
            remote_id,
            {RemoteAttributes.STATE: remote_state}
        )

        # Update Connection Sensor
        self.events.emit(
            DeviceEvents.UPDATE,
            connection_sensor_id,
            {
                SensorAttributes.STATE: "Connected",
                SensorAttributes.VALUE: "connected",
            }
        )

        # Update Group Sensor
        group_status = "Ungrouped"
        if self._is_grouped:
            if self._is_leader:
                group_status = "Leader"
            else:
                group_status = "Follower"

        group_info = self._group_name if self._group_name else group_status

        self.events.emit(
            DeviceEvents.UPDATE,
            group_sensor_id,
            {
                SensorAttributes.STATE: group_info,
                SensorAttributes.VALUE: group_status.lower(),
            }
        )

    async def _send_command(self, endpoint: str, params: dict[str, Any] | None = None) -> bool:
        """Send a command to the BluOS player."""
        if not self._session:
            _LOG.error("[%s] Cannot send command - session not initialized", self.log_id)
            return False

        try:
            url = f"{self._base_url}/{endpoint}"
            _LOG.debug("[%s] Sending command: %s %s", self.log_id, endpoint, params or "")

            async with self._session.get(url, params=params or {}) as resp:
                if resp.status == 200:
                    # Force immediate poll to update state
                    asyncio.create_task(self.poll_device())
                    return True
                else:
                    _LOG.warning("[%s] Command failed: %s %s", self.log_id, endpoint, resp.status)
                    return False

        except Exception as err:  # pylint: disable=broad-exception-caught
            _LOG.error("[%s] Command error %s: %s", self.log_id, endpoint, err)
            return False

    async def play(self) -> bool:
        """Start playback."""
        _LOG.info("[%s] Play", self.log_id)
        return await self._send_command("Play")

    async def pause(self) -> bool:
        """Pause playback."""
        _LOG.info("[%s] Pause", self.log_id)
        return await self._send_command("Pause")

    async def stop(self) -> bool:
        """Stop playback."""
        _LOG.info("[%s] Stop", self.log_id)
        return await self._send_command("Pause")  # BluOS uses Pause for stop

    async def play_pause(self) -> bool:
        """Toggle play/pause."""
        _LOG.info("[%s] Play/Pause toggle", self.log_id)
        return await self._send_command("Pause", {"toggle": "1"})

    async def next_track(self) -> bool:
        """Skip to next track."""
        _LOG.info("[%s] Next track", self.log_id)
        return await self._send_command("Skip")

    async def previous_track(self) -> bool:
        """Skip to previous track."""
        _LOG.info("[%s] Previous track", self.log_id)
        return await self._send_command("Back")

    async def set_volume(self, volume: int) -> bool:
        """Set volume level (0-100)."""
        volume = max(0, min(100, volume))
        _LOG.info("[%s] Setting volume to %d", self.log_id, volume)
        return await self._send_command("Volume", {"level": str(volume)})

    async def volume_up(self) -> bool:
        """Increase volume."""
        _LOG.info("[%s] Volume up", self.log_id)
        current = int(self._state.get("volume", "50"))
        return await self.set_volume(current + 1)

    async def volume_down(self) -> bool:
        """Decrease volume."""
        _LOG.info("[%s] Volume down", self.log_id)
        current = int(self._state.get("volume", "50"))
        return await self.set_volume(current - 1)

    async def mute(self, muted: bool) -> bool:
        """Set mute state."""
        _LOG.info("[%s] Setting mute to %s", self.log_id, muted)
        return await self._send_command("Volume", {"mute": "1" if muted else "0"})

    async def mute_toggle(self) -> bool:
        """Toggle mute."""
        _LOG.info("[%s] Mute toggle", self.log_id)
        current_mute = self._state.get("mute", "0") == "1"
        return await self.mute(not current_mute)

    async def set_shuffle(self, shuffle: bool) -> bool:
        """Set shuffle mode."""
        _LOG.info("[%s] Setting shuffle to %s", self.log_id, shuffle)
        return await self._send_command("Shuffle", {"state": "1" if shuffle else "0"})

    async def set_repeat(self, repeat: str) -> bool:
        """Set repeat mode (OFF, ALL, ONE)."""
        _LOG.info("[%s] Setting repeat to %s", self.log_id, repeat)

        # Map UC repeat modes to BluOS values
        repeat_map = {
            "OFF": "0",
            "ALL": "1",
            "ONE": "2",
        }

        value = repeat_map.get(repeat.upper(), "0")
        return await self._send_command("Repeat", {"state": value})

    async def seek(self, position: int) -> bool:
        """Seek to position in seconds."""
        _LOG.info("[%s] Seeking to %d", self.log_id, position)
        return await self._send_command("Play", {"seek": str(position)})

    async def select_preset(self, preset_id: int) -> bool:
        """Select a preset."""
        _LOG.info("[%s] Selecting preset %d", self.log_id, preset_id)
        return await self._send_command("Preset", {"id": str(preset_id)})

    async def clear_queue(self) -> bool:
        """Clear the playback queue."""
        _LOG.info("[%s] Clearing queue", self.log_id)
        return await self._send_command("Clear")

    async def fetch_presets(self) -> list[dict[str, Any]]:
        """Fetch available presets from the player."""
        if not self._session:
            return []

        try:
            async with self._session.get(f"{self._base_url}/Presets") as resp:
                if resp.status == 200:
                    text = await resp.text()
                    return self._parse_presets_xml(text)
                return []
        except Exception as err:  # pylint: disable=broad-exception-caught
            _LOG.error("[%s] Presets fetch error: %s", self.log_id, err)
            return []

    def _parse_presets_xml(self, xml_text: str) -> list[dict[str, Any]]:
        """Parse XML presets response into list."""
        try:
            root = ET.fromstring(xml_text)
            presets = []
            for preset in root.findall(".//preset"):
                preset_data = {
                    "id": preset.get("id"),
                    "name": preset.get("name"),
                    "url": preset.get("url"),
                }
                if preset_data["id"] and preset_data["name"]:
                    presets.append(preset_data)
            return presets
        except Exception as err:  # pylint: disable=broad-exception-caught
            _LOG.error("[%s] Presets XML parse error: %s", self.log_id, err)
            return []

    async def add_slave(self, slave_ip: str, slave_port: int = 11000) -> bool:
        """Add a slave player to this player's group (make this player leader)."""
        _LOG.info("[%s] Adding slave %s:%d", self.log_id, slave_ip, slave_port)
        return await self._send_command("AddSlave", {"slave": f"{slave_ip}:{slave_port}"})

    async def remove_slave(self, slave_ip: str, slave_port: int = 11000) -> bool:
        """Remove a slave player from this player's group."""
        _LOG.info("[%s] Removing slave %s:%d", self.log_id, slave_ip, slave_port)
        return await self._send_command("RemoveSlave", {"slave": f"{slave_ip}:{slave_port}"})

    async def leave_group(self) -> bool:
        """Leave the current group (if part of one)."""
        _LOG.info("[%s] Leaving group", self.log_id)
        # To leave a group, send Leave command
        return await self._send_command("Leave")
