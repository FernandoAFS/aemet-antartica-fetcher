"""
Mock fetcher for testing and simulations.
"""

from typing import Mapping
from datetime import datetime
from .annot import StationMetaData, WeatherPoint
from .exceptions import StationIdValueError, IniDateValueError, EndDateValueError
from dataclasses import dataclass
import operator as op
from itertools import repeat, compress


class InMemoryStationData(StationMetaData):
    """
    Inclusion of timeseries information in station data to avoid double dictionary.
    """

    timeseries: list[WeatherPoint]


@dataclass(frozen=True)
class MockWeatherDataFetcher:
    """
    Returns information from a given in-memory source.
    """

    "Combination of both metadata and in-memory timeseries data"
    station_data: Mapping[str, InMemoryStationData]

    def _get_station_data(self, station_name: str) -> InMemoryStationData:
        "Wrapper around dict get for error handling"
        try:
            return self.station_data[station_name]
        except KeyError as e:
            raise StationIdValueError(f"Station name {station_name} not found") from e

    async def stations(self) -> list[str]:
        return list(self.station_data.keys())

    async def time_range(self, station_id: str) -> tuple[datetime, datetime]:
        station_metadata = self._get_station_data(station_id)
        return (
            station_metadata["date0"],
            station_metadata["datef"],
        )

    async def timeseries(
        self, date0: datetime, dateF: datetime, station_id: str
    ) -> list[WeatherPoint]:
        station_metadata = self._get_station_data(station_id)

        dMin = station_metadata["date0"]
        dMax = station_metadata["datef"]

        if date0 < dMin:
            raise IniDateValueError(
                f"Requested date is below minimum: min_date={dMin}, requested_d0={date0}"
            )

        if dateF > dMax:
            raise EndDateValueError(
                f"Requested date is above max: max_date={dMax}, requested_dF={dateF}"
            )

        # THINK OVER THIS. THERE MAY BE A BETTER WAY TO DO THE TIME CONVERSION...
        timeseries_data = station_metadata["timeseries"]
        fhoras: map[str] = map(op.itemgetter("fhora"), timeseries_data)
        timeseries_dates: list[datetime] = list(map(datetime.fromisoformat, fhoras))

        gt_d0_mask: map[bool] = map(op.gt, timeseries_dates, repeat(date0))
        lt_df_mask: map[bool] = map(op.lt, timeseries_dates, repeat(dateF))

        dates_mask: map[bool] = map(op.and_, gt_d0_mask, lt_df_mask)

        return list(compress(timeseries_data, dates_mask))
