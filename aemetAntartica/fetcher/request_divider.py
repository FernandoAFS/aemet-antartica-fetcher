"""
Async synchronization primitive proxy for parallelization control.
"""

from collections.abc import (
    Generator,
    Sequence,
)
from dataclasses import dataclass
from datetime import datetime

import structlog

from aemetAntartica.util.task_group import parallel_task

from .annot import WeatherDataFetcher

logger = structlog.getLogger(__name__)


def monthly_divider(d0: datetime, df: datetime) -> Generator[datetime]:
    "Generate list of dates always first day of the month"
    if df <= d0:
        raise ValueError("Df must be after D0")

    som = d0.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    eom = df.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    if d0 != som:
        yield d0

    d = som
    while d < eom:
        yield d
        if d.month >= 12:
            d = d.replace(year=d.year + 1, month=1)
        else:
            d = d.replace(month=d.month + 1)

    if eom != df:
        yield df


@dataclass(frozen=True, kw_only=True)
class MonthlyTimeRequestDivider[T]:
    """
    Wrap every request method under a semaphore to guarrante a max number of current requests
    """

    fetcher: WeatherDataFetcher[T]

    async def stations(self) -> Sequence[str]:
        return await self.fetcher.stations()

    async def time_range(self, station_id: str) -> tuple[datetime, datetime]:
        return await self.fetcher.time_range(station_id)

    async def timeseries(
        self, date_0: datetime, date_f: datetime, station_id: str
    ) -> Sequence[T]:
        dates = list(monthly_divider(date_0, date_f))

        tasks = [
            self.fetcher.timeseries(d0, df, station_id)
            for d0, df in zip(dates[:-1], dates[1:])
        ]
        results = await parallel_task(*tasks)

        # FLATTENING THE RESULT
        return [point for points in results for point in points]
