"""
Date operations over model.
"""

from datetime import tzinfo

from .fetch import WeatherDataPoint, WeatherDataPointSeries


def set_point_timzone(tz: tzinfo):
    "Convenient method for changing points timezone"

    def _(model: WeatherDataPoint):
        d = model.model_dump()
        d["fhora"] = model.fhora.astimezone(tz)

        return WeatherDataPoint.model_validate(d)

    return _


def change_series_timezone(
    tz: tzinfo, series: WeatherDataPointSeries
) -> WeatherDataPointSeries:
    "Change points timezone of series series."
    new_points = map(set_point_timzone(tz), series.points)
    return WeatherDataPointSeries(points=list(new_points))
