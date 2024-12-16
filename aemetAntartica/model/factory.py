"""
Environment variables transformer factories
"""

from collections.abc import Callable
from os import environ
from zoneinfo import ZoneInfo

import structlog

from .tz_fetch import set_point_timzone
from .fetch import WeatherDataPoint

logger = structlog.get_logger()


def change_series_timezone_os() -> Callable[[WeatherDataPoint], WeatherDataPoint]:
    """
    Generate datetime switcher factory from environment variables:

    - AEMET_TIMEZONE_RESULT: any timezone from. See zoneinfo.available_timzone(). (default: Europe/Madrid)
    """
    zone_key = environ.get("AEMET_TIMEZONE_RESULT", "Europe/Madrid")

    zi = ZoneInfo(zone_key)
    logger.debug("Creating results timezone converter", timezone_key=zone_key)
    return set_point_timzone(zi)
