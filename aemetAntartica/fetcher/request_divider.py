"""
Proxy to divide a large request into sub-montly requests.
"""

from collections.abc import (
    Generator,
    Sequence,
)
from dataclasses import dataclass
from datetime import datetime, timedelta

import structlog

from itertools import batched
from aemetAntartica.util.task_group import parallel_task

from .annot import WeatherDataFetcher

logger = structlog.getLogger(__name__)


def add_month(d: datetime) -> datetime:
    "Add one month to date"
    if d.month >= 12:
        return d.replace(year=d.year + 1, month=1)
    return d.replace(month=d.month + 1)


def diff_months(d0: datetime, df: datetime) -> int:
    "Add one month to date"
    return (df.year - d0.year) * 12 + df.month - d0.month


def monthly_divider(d0: datetime, df: datetime, gap: timedelta) -> Generator[datetime]:
    "Generate list of dates always first day of the month"

    yield d0

    d = d0.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    diff_months(d0, df)
    for _ in range(diff_months(d0, df)):
        d = add_month(d)
        yield d - gap
        yield d

    if d < df:
        yield df


@dataclass(frozen=True, kw_only=True)
class MonthlyTimeRequestDivider[T]:
    """
    Wrap every request method under a semaphore to guarrante a max number of current requests
    """

    fetcher: WeatherDataFetcher[T]
    gap: timedelta = timedelta(minutes=10)

    async def stations(self) -> Sequence[str]:
        return await self.fetcher.stations()

    async def time_range(self, station_id: str) -> tuple[datetime, datetime]:
        return await self.fetcher.time_range(station_id)

    async def timeseries(
        self, date_0: datetime, date_f: datetime, station_id: str
    ) -> Sequence[T]:
        logger.debug(
            "Request on request divider",
            date_0=date_0,
            date_f=date_f,
            station_id=station_id,
        )

        dates_markers = monthly_divider(date_0, date_f, self.gap)
        dates_limits = list(batched(dates_markers, 2))

        logger.debug("Creating montly requests", dates_limits=dates_limits)

        async def fetch(d0: datetime, df: datetime) -> Sequence[T]:
            logger.debug(
                "Starting sub-monthly request",
                date_0=date_0,
                date_f=date_f,
            )
            ts = await self.fetcher.timeseries(d0, df, station_id)
            logger.debug(
                "Finished sub-monthly request",
                date_0=date_0,
                date_f=date_f,
            )
            return ts

        tasks = [fetch(d0, df) for d0, df in dates_limits]
        results = await parallel_task(*tasks)

        # FLATTENING THE RESULT
        return [point for points in results for point in points]
