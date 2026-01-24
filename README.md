# Bluesound Integration for Unfolded Circle Remote

[![License](https://img.shields.io/badge/License-MPL%202.0-brightgreen.svg)](https://opensource.org/licenses/MPL-2.0)
[![Python](https://img.shields.io/badge/python-3.11%20%7C%203.12-blue.svg)](https://www.python.org/downloads/)

Integration driver for Bluesound BluOS music streamers and wireless speakers with Unfolded Circle Remote Two/3.

Supports all BluOS-enabled devices from:
- Bluesound
- NAD Electronics
- DALI

## Features

### Media Player
- Full playback control (play, pause, stop, next, previous)
- Volume control (set, up/down, mute/unmute)
- Shuffle and repeat modes
- Media information display (title, artist, album, artwork)
- Playback position and seek support
- Source selection
- Preset recall (10 presets)

### Remote Control
- Dedicated remote entity with UI pages
- Playback controls
- Volume controls
- Repeat and shuffle modes
- Preset quick access (1-10)
- Multi-room grouping controls

### Sensors
- **Connection Status**: Monitor device connectivity
- **Group Status**: Track multi-room grouping state (Leader/Follower/Ungrouped)

### Multi-Room Audio
- Leave group functionality
- Group status monitoring
- Compatible with Bluesound app for group creation

## Requirements

- Unfolded Circle Remote Two or Remote 3
- Bluesound/BluOS-enabled device on the same network
- Device IP address (static IP recommended)

## Installation

### Via GitHub

1. Download the latest release
2. Extract to Remote's integrations directory
3. Restart the integration service

### Manual Installation

```bash
git clone https://github.com/mase1981/uc-intg-bluesound.git
cd uc-intg-bluesound
pip install -r requirements.txt
python -m intg_bluesound
```

## Configuration

### Setup Flow

1. Open Unfolded Circle Remote web interface
2. Navigate to Integrations
3. Select "Add Integration"
4. Choose "Bluesound"
5. Enter configuration:
   - **Player Name**: Friendly name for the device
   - **IP Address**: Device IP address
   - **Port**: BluOS port (default: 11000)

### Port Configuration

Most Bluesound devices use port **11000** (default).

Multi-zone devices (CI580) use different ports per zone:
- Zone 1: 11000
- Zone 2: 11010
- Zone 3: 11020
- Zone 4: 11030

## Entities

After successful setup, the integration creates the following entities:

- **Media Player** (`media_player.bluesound_<ip>`)
  - Control playback, volume, sources, and modes
  - View media information and artwork

- **Remote** (`remote.bluesound_<ip>`)
  - Quick access UI for common controls
  - Preset buttons
  - Grouping controls

- **Connection Sensor** (`sensor.bluesound_<ip>_connection`)
  - Connected/Disconnected status

- **Group Sensor** (`sensor.bluesound_<ip>_group`)
  - Ungrouped/Leader/Follower status
  - Group name if applicable

## Usage

### Playback Control

Use the media player entity to control playback:
- Play/Pause/Stop
- Next/Previous track
- Volume adjustment
- Mute toggle

### Presets

Access your saved BluOS presets (configured in Bluesound app):
- Via Remote entity preset buttons (1-10)
- Via Media Player commands

### Multi-Room Audio

To create speaker groups:
1. Use the official Bluesound app to create groups
2. Monitor group status via Group Sensor
3. Leave groups using Remote entity

Note: Group creation must be done through the Bluesound app. The integration supports group monitoring and leaving groups.

## Supported Devices

All devices running BluOS firmware:

**Bluesound**:
- Node series (Node, Node 2, Node 2i, Node N130, Node X, Node Icon)
- Powernode series (Powernode, Powernode 2, Powernode 2i, Powernode N330, Powernode Edge, Powernode Icon)
- Vault 2, Vault 2i
- Pulse series (Pulse, Pulse 2, Pulse 2i, Pulse Flex, Pulse Flex 2i, Pulse Mini, Pulse Mini 2i, Pulse M, Pulse Sub, Pulse Sub+, Pulse Soundbar, Pulse Soundbar 2i)

**NAD Electronics**:
- M10, M10 V2
- M33
- C 399
- C 658
- C 700
- CI 580 (multi-zone)

**DALI**:
- BluOS enabled speakers

## Troubleshooting

### Device Not Found

1. Verify device is powered on
2. Check network connectivity
3. Confirm IP address is correct
4. Ensure port 11000 is accessible (check firewall)
5. Try pinging the device IP

### Connection Lost

The integration includes automatic reconnection logic:
- Polls device every 5 seconds
- Reconnects automatically on network recovery
- Monitor via Connection Sensor

### Slow Response

- Ensure stable network connection
- Consider using wired Ethernet instead of Wi-Fi
- Check for network congestion
- Verify device firmware is up to date

### Groups Not Working

- Group creation requires Bluesound app
- Integration supports leaving groups only
- Check Group Sensor for current status

## Development

### Project Structure

```
uc-intg-bluesound/
├── intg_bluesound/
│   ├── __init__.py
│   ├── __main__.py
│   ├── config.py
│   ├── device.py
│   ├── driver.py
│   ├── setup_flow.py
│   ├── media_player.py
│   ├── remote.py
│   └── sensor.py
├── driver.json
├── pyproject.toml
├── requirements.txt
└── README.md
```

### Running Tests

```bash
# Install dependencies
pip install -r requirements.txt

# Run integration
python -m intg_bluesound
```

## BluOS API

This integration uses the BluOS Custom Integration API via REST/HTTP:
- Protocol: HTTP GET requests
- Response: XML format
- Port: 11000 (default)
- Polling: 5-second intervals with etag support

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add/update tests
5. Submit a pull request

## License

This project is licensed under the Mozilla Public License 2.0 (MPL-2.0).
See [LICENSE](LICENSE) for details.

## Acknowledgments

- Built using [ucapi-framework](https://github.com/unfoldedcircle/integration-python-library)
- BluOS is a trademark of Lenbrook Industries
- Bluesound is a trademark of Lenbrook Industries
- NAD Electronics is a trademark of Lenbrook Industries

## Support

- [GitHub Issues](https://github.com/mase1981/uc-intg-bluesound/issues)
- [Unfolded Circle Community](https://unfoldedcircle.com/community)

## Changelog

### v1.0.0 (2026-01-24)
- Initial release
- Media Player entity with full playback control
- Remote entity with UI pages
- Connection and Group sensors
- Multi-room audio support (leave group)
- Preset support (1-10)
- Automatic reconnection
- BluOS API polling with etag support
