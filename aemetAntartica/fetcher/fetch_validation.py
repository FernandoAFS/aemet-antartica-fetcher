from collections.abc import (
    Sequence,
)
from dataclasses import dataclass
from datetime import UTC, datetime

import structlog

from aemetAntartica.model.fetch import WeatherDataPoint, WeatherDataPointSeries
from aemetAntartica.model.tz_fetch import change_series_timezone


from .annot import WeatherDataFetcher, WeatherPoint

logger = structlog.getLogger(__name__)


@dataclass(frozen=True, kw_only=True)
class FetchValidatorProxy:
    """
    Get requests and convert them to validated pydantic result
    """

    fetcher: WeatherDataFetcher[WeatherPoint]

    async def stations(self) -> Sequence[str]:
        return await self.fetcher.stations()

    async def time_range(self, station_id: str) -> tuple[datetime, datetime]:
        return await self.fetcher.time_range(station_id)

    async def timeseries(
        self, date_0: datetime, date_f: datetime, station_id: str
    ) -> Sequence[WeatherDataPoint]:
        "Validate model and enforce timezone"
        raw_res = await self.fetcher.timeseries(date_0, date_f, station_id)

        logger.debug(
            "Validating model", date_0=date_0, date_f=date_f, station_id=station_id
        )
        points = WeatherDataPointSeries.model_validate({"points": raw_res})
        return change_series_timezone(UTC, points).points
