"""
Dependencies factories for fastapi
"""

from typing import Annotated, Callable, TypeAlias

from fastapi import Depends, HTTPException
from structlog import get_logger

from aemetAntartica.fetcher.annot import WeatherDataFetcher, WeatherPoint
from aemetAntartica.fetcher.factory import cached_gen_aemet_fetcher_env_var
from aemetAntartica.model.factory import change_series_timezone_os
from aemetAntartica.model.fetch import WeatherDataPoint

from .enum import AggTimeOpts, AggTypeOpts
from .params import (
    AggregationOptionsParam,
    Date0PathParamUTC,
    DateFPathParamUTC,
    StationIdPathParam,
)
from .response import (
    WeatherDataPointSeriesPaginationResult,
    pagination_series_to_response,
    weather_data_point_pagination_factory,
)

AemetDataFetcher: TypeAlias = Annotated[
    WeatherDataFetcher[WeatherDataPoint], Depends(cached_gen_aemet_fetcher_env_var)
]

TimezonePointConvert: TypeAlias = Annotated[
    Callable[[WeatherDataPoint], WeatherDataPoint],
    Depends(change_series_timezone_os),
]

logger = get_logger(__name__)


async def aggregate_aemet_data(
    date_0: Date0PathParamUTC,
    date_f: DateFPathParamUTC,
    station_id: StationIdPathParam,
    agg_opts: AggregationOptionsParam,
    data_fetch: AemetDataFetcher,
    tz_convert: TimezonePointConvert,
) -> WeatherDataPointSeriesPaginationResult:
    """
    Aggregation top level functions

    It starts the fetching process, filters, sorts, aggregates, changes timezone...
    """
    logger.debug(
        "Solved parameters and dependencies",
        date_0=date_0,
        date_f=date_f,
        station_id=station_id,
        agg_opts=agg_opts,
    )

    agg_opt = agg_opts.agg_opt
    time_opt = agg_opts.time_opt

    if (agg_opt == AggTypeOpts.NONE) & (time_opt != AggTimeOpts.NONE):
        raise HTTPException(
            status_code=400,
            detail="Informed aggregation type requires informed agregation time frame",
        )
    if (agg_opt != AggTypeOpts.NONE) & (time_opt == AggTimeOpts.NONE):
        raise HTTPException(
            status_code=400,
            detail="Informed aggregation time frame requires informed aggregation type",
        )

    logger.debug("Successfully cross-validated parameters")

    agg_f = agg_opt.to_agg_f()
    agg_td = time_opt.to_period()

    ts = await data_fetch.timeseries(date_0, date_f, station_id)

    try:
        agg_data = agg_f(ts, agg_td)
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail="Unexpected error on aggregation",
        ) from e

    try:
        adapted_page = list(map(tz_convert, agg_data))
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail="Unexpected error on time conversion",
        ) from e

    try:
        pagination = weather_data_point_pagination_factory(
            adapted_page, agg_opts.skip, agg_opts.limit
        )
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail="Error on pagination",
        ) from e

    try:
        return pagination_series_to_response(pagination, agg_opts.data_props)
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail="Error on response creation",
        ) from e


AemetAggDataQuery: TypeAlias = Annotated[
    WeatherDataFetcher[WeatherPoint], Depends(aggregate_aemet_data)
]
