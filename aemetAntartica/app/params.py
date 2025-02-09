"""
Types used for http open-api communications
"""

from datetime import UTC, datetime
from typing import Annotated, TypeAlias

from fastapi import Depends, Path, Query
from pydantic import BaseModel, Field
from structlog import get_logger

from .enum import AggTimeOpts, AggTypeOpts
from .response import WeatherPointResponseKey

logger = get_logger(__name__)

# Not possible to use 'type' keyword: https://github.com/fastapi/fastapi/issues/10719
Date0PathParam: TypeAlias = Annotated[
    datetime,
    Path(title="Start of range", description="Inclusive beginning of timeseries"),
]

DateFPathParam: TypeAlias = Annotated[
    datetime, Path(title="End of range", description="Inclusive end of timeseries")
]

StationIdPathParam: TypeAlias = Annotated[
    str, Path(title="Station Id", description="Name of the station to be fetched")
]

AggTimeQueryParam: TypeAlias = Annotated[
    AggTimeOpts,
    Query(
        title="Aggregation time",
        description="Aggregate timeseries on period. Uniformed for raw information",
    ),
]

AggTypeQueryParam: TypeAlias = Annotated[
    AggTypeOpts,
    Query(
        title="Aggregation type",
        description="Kind of agregation to be performed. Uninformed for raw result.",
    ),
]


class AggregationOptions(BaseModel):
    """
    This model includes aggregation time options, aggregation type and pagination options.
    """

    time_opt: AggTimeQueryParam = AggTimeOpts.NONE
    agg_opt: AggTypeQueryParam = AggTypeOpts.NONE
    skip: int = 0
    limit: int = 10  # TODO: ADD VALIDATION, 100 MAX
    data_props: list[WeatherPointResponseKey] = Field(default_factory=list)


AggregationOptionsParam: TypeAlias = Annotated[AggregationOptions, Query()]


def d0_utc(date_0: Date0PathParam) -> datetime:
    "Enforcing timezone in case it's not already informed"
    if date_0.tzinfo is None:
        date_0 = date_0.replace(tzinfo=UTC)
        logger.info("Assuming UTC timezone for input date", d0=date_0)
    return date_0


Date0PathParamUTC: TypeAlias = Annotated[datetime, Depends(d0_utc)]


def df_utc(date_f: DateFPathParam) -> datetime:
    "Enforcing timezone in case it's not already informed"
    if date_f.tzinfo is None:
        date_f = date_f.replace(tzinfo=UTC)
        logger.info("Assuming UTC timezone for input date", df=date_f)
    return date_f


DateFPathParamUTC: TypeAlias = Annotated[datetime, Depends(df_utc)]
