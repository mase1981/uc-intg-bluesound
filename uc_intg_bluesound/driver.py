"""
Bluesound driver for Unfolded Circle Remote.

:copyright: (c) 2026 by Meir Miyara.
:license: MPL-2.0, see LICENSE for more details.
"""

import logging

from ucapi_framework import BaseIntegrationDriver

from uc_intg_bluesound.config import BluesoundConfig
from uc_intg_bluesound.device import BluesoundDevice
from uc_intg_bluesound.media_player import BluesoundMediaPlayer
from uc_intg_bluesound.remote import BluesoundRemote
from uc_intg_bluesound.sensor import (
    BluesoundConnectionSensor,
    BluesoundGroupSensor,
    BluesoundSourceSensor,
)
from uc_intg_bluesound.select import BluesoundRepeatSelect, BluesoundPresetSelect

_LOG = logging.getLogger(__name__)


class BluesoundDriver(BaseIntegrationDriver[BluesoundDevice, BluesoundConfig]):
    """Bluesound integration driver."""

    def __init__(self):
        super().__init__(
            device_class=BluesoundDevice,
            entity_classes=[
                BluesoundMediaPlayer,
                BluesoundRemote,
                BluesoundConnectionSensor,
                BluesoundGroupSensor,
                BluesoundSourceSensor,
                BluesoundRepeatSelect,
                lambda cfg, dev: [BluesoundPresetSelect(cfg, dev)] if dev.presets else [],
            ],
            driver_id="bluesound",
            require_connection_before_registry=True,
        )
