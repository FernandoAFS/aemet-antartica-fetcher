"""
SQL cache logic
"""

from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from datetime import datetime, timedelta
from operator import attrgetter
from aemetAntartica.db.context import db_context_var
from aemetAntartica.util.itertools import sliding_window

import structlog

from aemetAntartica.fetcher.annot import WeatherDataFetcher, WeatherPoint
from aemetAntartica.model.fetch import WeatherDataPoint, WeatherDataPointSeries
from aemetAntartica.util.task_group import parallel_task

logger = structlog.get_logger(__name__)


def find_cache_gaps(
    d0: datetime, df: datetime, dates: Sequence[datetime], gap: timedelta
) -> Iterable[datetime]:
    """
    Returns gaps that are larger than provided.

    Dates must be pre-sorted
    """

    if len(dates) <= 0:
        yield d0
        yield df
        return

    if d0 < dates[0]:
        yield d0
        yield dates[0] - gap

    for d0_, df_ in sliding_window(dates[1:-1], 2):
        if df_ - d0_ <= gap:
            continue
        yield d0_ + gap
        yield df_ - gap

    if df > dates[-1]:
        yield dates[-1] + gap
        yield df


@dataclass(frozen=True, kw_only=True)
class SqliteCacheFetcherProxy:
    """
    Proxy fetcher that captures requests. Answers with sqlite data if possible and delegates on fetcher for true data-source.

    This class expects to have a db context available.
    """

    fetcher: WeatherDataFetcher[WeatherPoint]
    date_offset: timedelta = timedelta(minutes=10)

    async def stations(self) -> Sequence[str]:
        "Call fetcher"
        return await self.fetcher.stations()

    async def time_range(self, station_id: str) -> tuple[datetime, datetime]:
        "Call fetcher"
        return await self.fetcher.time_range(station_id)

    async def timeseries(
        self, date_0: datetime, date_f: datetime, station_id: str
    ) -> Sequence[WeatherDataPoint]:
        """
        Fetch data from sql. Check for gaps. Fetch those gaps in the network
        and finally insert them back to sql.
        """
        db_proxy = db_context_var.get()

        fetched_results = await db_proxy.fetch_between(date_0, date_f, station_id)

        fetched_dates = list(map(attrgetter("fhora"), fetched_results))
        gaps_markerks = find_cache_gaps(date_0, date_f, fetched_dates, self.date_offset)

        tasks = [
            self.fetcher.timeseries(gap0, gapf, station_id)
            for gap0, gapf in sliding_window(gaps_markerks, 2)
        ]

        aemet_results = await parallel_task(*tasks)
        aemet_fetched_points = [point for result in aemet_results for point in result]

        aemet_points = WeatherDataPointSeries.model_validate(
            {"points": aemet_fetched_points}
        ).points

        await db_proxy.insert_points(aemet_points, station_id)

        all_points = [*fetched_results, *aemet_points]
        return sorted(all_points, key=attrgetter("fhora"))
