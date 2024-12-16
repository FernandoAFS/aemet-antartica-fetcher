"""
Model used to validate data coming from aemet portal through fetcher.
"""

from datetime import datetime

from pydantic import BaseModel


class WeatherDataPoint(BaseModel):
    "Model of aemet data and aggregations"

    fhora: datetime
    temp: float
    pres: float
    vel: float


class WeatherDataPointSeries(BaseModel):
    "Wrapper class to assist validation of multiple points"

    points: list[WeatherDataPoint]
