"""
Bluesound integration entry point.

:copyright: (c) 2026 by Meir Miyara.
:license: MPL-2.0, see LICENSE for more details.
"""

import logging
from ucapi_framework import run_integration
from intg_bluesound.driver import BluesoundDriver
from intg_bluesound.setup_flow import BluesoundSetupFlow
from intg_bluesound.config import BluesoundConfigManager

_LOG = logging.getLogger(__name__)


def main():
    """Run the integration."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    )

    config_manager = BluesoundConfigManager("bluesound")

    run_integration(
        driver=BluesoundDriver(),
        setup_flow=BluesoundSetupFlow(config_manager),
        config_manager=config_manager,
    )


if __name__ == "__main__":
    main()
