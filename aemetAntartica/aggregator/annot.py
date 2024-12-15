"""
Interface and typing definitions
"""

from typing import Protocol, Sequence
from aemetAntartica.model.fetch import WeatherDataPoint
from datetime import timedelta

class Aggregator(Protocol):

    def __call__(self, data_in: Sequence[WeatherDataPoint], period: timedelta) -> Sequence[WeatherDataPoint]:
        """
        Given sequence of data return other sequence with the same type but not the same length.
        """
        ...
