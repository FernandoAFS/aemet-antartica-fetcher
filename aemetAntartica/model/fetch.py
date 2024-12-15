"""
Model used to validate data coming from aemet portal through fetcher.
"""

from pydantic import BaseModel
from datetime import datetime


class WeatherDataPoint(BaseModel):
    fhora: datetime
    temp: float
    pres: float
    vel: float
