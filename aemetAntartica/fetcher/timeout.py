from asyncio import TimeoutError, timeout
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime

from .annot import WeatherDataFetcher, WeatherPoint
from .exceptions import AemetRequestError


@dataclass(frozen=True, kw_only=True)
class AemetFastapiErrorsWrapper[T: WeatherPoint]:
    "Wrap every method in a timeout"

    fetcher: WeatherDataFetcher[T]
    seconds: float

    async def stations(self) -> Sequence[str]:
        try:
            async with timeout(self.seconds):
                return await self.fetcher.stations()
        except TimeoutError as e:
            raise AemetRequestError("Timeout on stations request") from e

    async def time_range(self, station_id: str) -> tuple[datetime, datetime]:
        try:
            async with timeout(self.seconds):
                return await self.fetcher.time_range(station_id)
        except TimeoutError as e:
            raise AemetRequestError("Timeout on time_range request") from e

    async def timeseries(
        self, date_0: datetime, date_f: datetime, station_id: str
    ) -> Sequence[T]:
        """
        Request station data to external API.
        """
        try:
            async with timeout(self.seconds):
                return await self.fetcher.timeseries(date_0, date_f, station_id)
        except TimeoutError as e:
            raise AemetRequestError("Timeout on timeseries request") from e
