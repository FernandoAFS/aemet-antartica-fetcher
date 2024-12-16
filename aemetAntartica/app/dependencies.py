"""
Dependencies factories for fastapi
"""

import operator
from typing import Annotated, Callable, TypeAlias, TypeVar

from fastapi import Depends

from aemetAntartica.fetcher.annot import WeatherDataFetcher, WeatherPoint
from aemetAntartica.fetcher.factory import cached_gen_aemet_fetcher_env_var
from aemetAntartica.model.factory import change_series_timezone_os
from aemetAntartica.model.fetch import WeatherDataPoint, WeatherDataPointSeries
from aemetAntartica.util.bisect import find_between

from .enum import AggTimeOpts, AggTypeOpts
from .params import (
    AggregationOptionsParam,
    Date0PathParam,
    DateFPathParam,
    StationIdPathParam,
)
from .response import (
    WeatherDataPointSeriesPaginationResult,
    pagination_series_to_response,
    weather_data_point_pagination_factory,
)


AemetDataFetcher: TypeAlias = Annotated[
    WeatherDataFetcher[WeatherPoint], Depends(cached_gen_aemet_fetcher_env_var)
]

TimezonePointConvert: TypeAlias = Annotated[
    Callable[[WeatherDataPoint], WeatherDataPoint],
    Depends(change_series_timezone_os),
]


async def aggregate_aemet_data(
    date_0: Date0PathParam,
    date_f: DateFPathParam,
    station_id: StationIdPathParam,
    agg_opts: AggregationOptionsParam,
    data_fetch: AemetDataFetcher,
    tz_convert: TimezonePointConvert,
) -> WeatherDataPointSeriesPaginationResult:
    """
    Aggregation top level functions

    It starts the fetching process, filters, sorts, aggregates, changes timezone...
    """
    agg_opt = agg_opts.agg_opt
    time_opt = agg_opts.time_opt

    # TODO: RAISE ERROR.
    # BOTH HAVE TO BE INFORMED TOGETHER. CANNOT AGGREGATE OVER NULL TIME FRAME.
    if (agg_opt == AggTypeOpts.NONE) != (time_opt == AggTimeOpts.NONE):
        ...

    agg_f = agg_opt.to_agg_f()
    agg_td = time_opt.to_period()

    ts = await data_fetch.timeseries(date_0, date_f, station_id)

    # TODO: MOVE TO SERIES...
    models_ts = list(map(WeatherDataPoint.model_validate, ts))
    filtered_models_ts = find_between(
        models_ts, date_0, date_f, key=operator.attrgetter("fhora")
    )

    agg_data = agg_f(filtered_models_ts, agg_td)

    # TODO: CONVERT TIMEZONE.

    adapted_page = list(map(tz_convert, agg_data))

    pagination = weather_data_point_pagination_factory(
        adapted_page, agg_opts.skip, agg_opts.limit
    )

    return pagination_series_to_response(pagination, agg_opts.data_props)


AemetAggDataQuery: TypeAlias = Annotated[
    WeatherDataFetcher[WeatherPoint], Depends(aggregate_aemet_data)
]
