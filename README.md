# Bluesound Integration for Unfolded Circle Remote 2/3

Control your Bluesound BluOS music streamer directly from your Unfolded Circle Remote 2 or Remote 3 with comprehensive media player control, **multi-room audio support**, and **complete BluOS API-based control**.

![Bluesound](https://img.shields.io/badge/Bluesound-BluOS%20Music%20Streamer-blue)
[![GitHub Release](https://img.shields.io/github/v/release/mase1981/uc-intg-bluesound?style=flat-square)](https://github.com/mase1981/uc-intg-bluesound/releases)
![License](https://img.shields.io/badge/license-MPL--2.0-blue?style=flat-square)
[![GitHub issues](https://img.shields.io/github/issues/mase1981/uc-intg-bluesound?style=flat-square)](https://github.com/mase1981/uc-intg-bluesound/issues)
[![Community Forum](https://img.shields.io/badge/community-forum-blue?style=flat-square)](https://unfolded.community/)
[![Discord](https://badgen.net/discord/online-members/zGVYf58)](https://discord.gg/zGVYf58)
![GitHub Downloads (all assets, all releases)](https://img.shields.io/github/downloads/mase1981/uc-intg-bluesound/total?style=flat-square)
[![Buy Me A Coffee](https://img.shields.io/badge/buy%20me%20a%20coffee-donate-yellow.svg?style=flat-square)](https://buymeacoffee.com/meirmiyara)
[![PayPal](https://img.shields.io/badge/PayPal-donate-blue.svg?style=flat-square)](https://paypal.me/mmiyara)
[![Github Sponsors](https://img.shields.io/badge/GitHub%20Sponsors-30363D?&logo=GitHub-Sponsors&logoColor=EA4AAA&style=flat-square)](https://github.com/sponsors/mase1981)


## Features

This integration provides comprehensive control of Bluesound BluOS music streamers through the native BluOS API, delivering seamless integration with your Unfolded Circle Remote for complete music control across all BluOS-enabled devices from Bluesound, NAD Electronics, and DALI.

---
## ❤️ Support Development ❤️

If you find this integration useful, consider supporting development:

[![GitHub Sponsors](https://img.shields.io/badge/Sponsor-GitHub-pink?style=for-the-badge&logo=github)](https://github.com/sponsors/mase1981)
[![Buy Me A Coffee](https://img.shields.io/badge/Buy%20Me%20A%20Coffee-FFDD00?style=for-the-badge&logo=buy-me-a-coffee&logoColor=black)](https://www.buymeacoffee.com/meirmiyara)
[![PayPal](https://img.shields.io/badge/PayPal-00457C?style=for-the-badge&logo=paypal&logoColor=white)](https://paypal.me/mmiyara)

Your support helps maintain this integration. Thank you! ❤️
---

### 🎵 **Media Player Control**

#### **Playback Control**
- **Play/Pause Toggle** - Control playback state
- **Stop** - Stop playback
- **Next/Previous Track** - Navigate through tracks
- **Seek** - Jump to specific position in track
- **Real-time Position** - Current playback position

#### **Volume Control**
- **Volume Up/Down** - Precise volume adjustment
- **Set Volume** - Direct volume control (0-100 scale)
- **Volume Slider** - Visual volume control
- **Mute Toggle** - Quick mute/unmute
- **Mute/Unmute** - Explicit mute controls
- **Real-time Updates** - Instant volume feedback

#### **Playback Modes**
- **Shuffle** - Toggle shuffle mode on/off
- **Repeat Modes** - Off, All tracks, Single track
- **Mode Feedback** - Real-time mode status

#### **Preset Control**
- **10 Presets** - Quick access to favorite stations/playlists
- **Preset Buttons** - One-touch preset recall
- **Uses Your Presets** - Configured in BluOS app

#### **Media Information**
- **Track Title** - Currently playing song
- **Artist Name** - Artist information
- **Album Name** - Album information
- **Album Artwork** - Cover art display
- **Duration** - Track length
- **Position** - Current playback position
- **Source** - Current streaming service

### 🎛️ **Remote Control Entity**

Dedicated remote entity with intuitive UI pages:

#### **Page 1: Playback & Volume**
- Play, Pause, Stop buttons
- Next/Previous track navigation
- Volume Up/Down controls
- Mute toggle button

#### **Page 2: Modes & Presets**
- Repeat mode selection (Off/All/One)
- Shuffle toggle (On/Off)
- Quick access to presets 1-4

#### **Page 3: Multi-Room Grouping**
- Leave group button
- Group management controls
- Multi-room audio coordination

### 📊 **Sensor Entities**

Real-time monitoring of device state:

- **Connection Sensor** - Device connectivity status (Connected/Disconnected)
- **Group Status Sensor** - Multi-room grouping state (Ungrouped/Leader/Follower)

### 🔊 **Multi-Room Audio**

#### **Group Management**
- **Leave Group** - Remove player from current group
- **Group Status** - Real-time grouping state monitoring
- **Group Creation** - Use BluOS app to create speaker groups
- **Follower Detection** - Automatic detection of grouped players

### **Protocol Requirements**

- **Protocol**: BluOS Custom Integration API
- **HTTP Port**: 11000 (default)
  - CI580 multi-zone: 11000, 11010, 11020, 11030
- **Network Access**: Device must be on same local network
- **Connection**: Periodic polling for state updates (5-second interval)
- **Efficiency**: ETag support for optimized bandwidth usage

### **Network Requirements**

- **Local Network Access** - Integration requires same network as Bluesound device
- **HTTP Protocol** - BluOS API (port 11000)
- **Static IP Recommended** - Device should have static IP or DHCP reservation
- **Firewall** - Must allow HTTP traffic
- **Multi-Zone** - CI580 uses ports 11010, 11020, 11030 for additional zones

## Installation

### Option 1: Remote Web Interface (Recommended)
1. Navigate to the [**Releases**](https://github.com/mase1981/uc-intg-bluesound/releases) page
2. Download the latest `uc-intg-bluesound-<version>-aarch64.tar.gz` file
3. Open your remote's web interface (`http://your-remote-ip`)
4. Go to **Settings** → **Integrations** → **Add Integration**
5. Click **Upload** and select the downloaded `.tar.gz` file

### Option 2: Docker (Advanced Users)

The integration is available as a pre-built Docker image from GitHub Container Registry:

**Image**: `ghcr.io/mase1981/uc-intg-bluesound:latest`

**Docker Compose:**
```yaml
services:
  uc-intg-bluesound:
    image: ghcr.io/mase1981/uc-intg-bluesound:latest
    container_name: uc-intg-bluesound
    network_mode: host
    volumes:
      - </local/path>:/data
    environment:
      - UC_CONFIG_HOME=/data
      - UC_INTEGRATION_HTTP_PORT=9090
      - UC_INTEGRATION_INTERFACE=0.0.0.0
      - PYTHONPATH=/app
    restart: unless-stopped
```

**Docker Run:**
```bash
docker run -d --name uc-bluesound --restart unless-stopped --network host -v bluesound-config:/app/config -e UC_CONFIG_HOME=/app/config -e UC_INTEGRATION_INTERFACE=0.0.0.0 -e UC_INTEGRATION_HTTP_PORT=9090 -e PYTHONPATH=/app ghcr.io/mase1981/uc-intg-bluesound:latest
```

## Configuration

### Step 1: Prepare Your Bluesound Device

**IMPORTANT**: Bluesound device must be powered on and connected to your network before adding the integration.

#### Verify Network Connection:
1. Check that device is connected to network (Ethernet or WiFi)
2. Note the IP address from device's network settings or BluOS app
3. Ensure device firmware is up to date via BluOS app
4. Verify BluOS API is accessible (enabled by default on port 11000)

#### Network Setup:
- **Wired Connection**: Recommended for stability
- **Static IP**: Recommended via DHCP reservation
- **Firewall**: Allow HTTP traffic (port 11000)
- **Network Isolation**: Must be on same subnet as Remote
- **Multi-Zone**: CI580 requires ports 11010, 11020, 11030 for additional zones

#### Supported Devices:
**Bluesound**: Node series, Powernode series, Vault 2i, Pulse series
**NAD Electronics**: M10, M33, C 399, C 658, C 700, CI 580
**DALI**: BluOS enabled speakers

### Step 2: Setup Integration

1. After installation, go to **Settings** → **Integrations**
2. The Bluesound integration should appear in **Available Integrations**
3. Click **"Configure"** to begin setup:

#### **Configuration:**
- **Player Name**: Friendly name (e.g., "Living Room Bluesound")
- **IP Address**: Enter device IP (e.g., 192.168.1.100)
- **Port**: Default is 11000 (change only if needed or for multi-zone)
- Click **Complete Setup**

#### **Connection Test:**
- Integration verifies device connectivity
- HTTP connection established to BluOS API
- Setup fails if device unreachable

4. Integration will create entities:
   - **Media Player**: `media_player.bluesound_[device_name]`
   - **Remote**: `remote.bluesound_[device_name]`
   - **Sensors**: Connection and Group status sensors

## Using the Integration

### Media Player Entity

The media player entity provides complete control:

- **Playback Control**: Play/Pause toggle, Stop, Next, Previous, Seek
- **Volume Control**: Volume slider (0-100), Up/Down buttons
- **Mute Control**: Toggle, Mute, Unmute
- **Shuffle**: Toggle shuffle mode
- **Repeat**: Cycle through Off, All, One
- **Presets**: Select from 10 quick-access presets
- **Media Info**: Current track, artist, album, artwork, duration, position

### Remote Control Entity

The remote control entity provides quick access through UI pages:

- **Playback Page**: Full playback and volume controls with visual buttons
- **Modes Page**: Repeat/Shuffle modes and preset quick access
- **Grouping Page**: Multi-room audio controls

### Sensor Entities

| Sensor | Description |
|--------|-------------|
| Connection Sensor | Device connectivity status (Connected/Disconnected) |
| Group Status Sensor | Multi-room grouping state (Ungrouped/Leader/Follower) |

### Multi-Room Audio

#### Creating Groups:
1. Use the official BluOS app to create speaker groups
2. Integration automatically detects grouping changes
3. Monitor group status via Group Status sensor

#### Leaving Groups:
1. Use Remote entity's grouping page
2. Click "Leave Group" button
3. Player becomes independent

## Credits

- **Developer**: Meir Miyara
- **Bluesound**: Premium wireless multi-room music streaming systems
- **NAD Electronics**: High-performance audio components with BluOS
- **DALI**: Danish audiophile speakers with BluOS integration
- **Unfolded Circle**: Remote 2/3 integration framework (ucapi)
- **Protocol**: BluOS Custom Integration API v1.7
- **Community**: Testing and feedback from UC community

## License

This project is licensed under the Mozilla Public License 2.0 (MPL-2.0) - see LICENSE file for details.

## Support & Community

- **GitHub Issues**: [Report bugs and request features](https://github.com/mase1981/uc-intg-bluesound/issues)
- **UC Community Forum**: [General discussion and support](https://unfolded.community/)
- **Developer**: [Meir Miyara](https://www.linkedin.com/in/meirmiyara)
- **BluOS Support**: [Official BluOS Support](https://support.bluos.net/)

---

**Made with ❤️ for the Unfolded Circle and Bluesound Communities**

**Thank You**: Meir Miyara
