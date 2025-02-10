"""
Async synchronization primitive proxy for parallelization control.
"""

from asyncio import BoundedSemaphore
from collections.abc import (
    Sequence,
)
from dataclasses import dataclass
from datetime import datetime

import structlog


from .annot import WeatherDataFetcher

logger = structlog.getLogger(__name__)


@dataclass(frozen=True, kw_only=True)
class SemaphoreDataFetcher[T]:
    """
    Wrap every request method under a semaphore to guarrante a max number of current requests
    """

    fetcher: WeatherDataFetcher[T]
    semaphore: BoundedSemaphore

    async def stations(self) -> Sequence[str]:
        async with self.semaphore:
            return await self.fetcher.stations()

    async def time_range(self, station_id: str) -> tuple[datetime, datetime]:
        async with self.semaphore:
            return await self.fetcher.time_range(station_id)

    async def timeseries(
        self, date_0: datetime, date_f: datetime, station_id: str
    ) -> Sequence[T]:

        if self.semaphore.locked():
            logger.debug("Locked semaphore. Request must wait")


        async with self.semaphore:
            return await self.timeseries(date_0, date_f, station_id)


def semaphore_data_fetcher_factory(
    fetcher: WeatherDataFetcher, n: int
) -> SemaphoreDataFetcher:
    semaphore = BoundedSemaphore(n)
    return SemaphoreDataFetcher(semaphore=semaphore, fetcher=fetcher)
