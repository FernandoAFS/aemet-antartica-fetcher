"""
Higher level validation operations
"""

import operator
from datetime import datetime

from aemetAntartica.util.bisect import find_between

from .fetch import WeatherDataPointSeries


def validate_filter_fetch_input(
    series: WeatherDataPointSeries,
    date_0: datetime,
    date_f: datetime,
) -> WeatherDataPointSeries:
    """
    Filter Weather Series
    """
    filter_points = find_between(
        series.points, date_0, date_f, key=operator.attrgetter("fhora")
    )
    return WeatherDataPointSeries.model_validate({"points": filter_points})
