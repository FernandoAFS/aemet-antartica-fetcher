from typing import Annotated, TypeAlias
from fastapi import Path, Query
from enum import Enum


class AggTimeOpts(str, Enum):
    hourly = "hourly"
    daily = "daily"
    monthly = "monthly"


# Not possible to use 'type' keyword: https://github.com/fastapi/fastapi/issues/10719
Date0PathParam: TypeAlias = Annotated[
    str, Path(title="Start of range", description="Inclusive beginning of timeseries")
]
DateFPathParam: TypeAlias = Annotated[
    str, Path(title="End of range", description="Inclusive end of timeseries")
]
StationIdPathParam: TypeAlias = Annotated[
    str, Path(title="Station Id", description="Name of the station to be fetched")
]
AggTypeQueryParam: TypeAlias = Annotated[
    AggTimeOpts | None,
    Query(
        title="Aggregation time",
        description="Aggregate timeseries on period. Uniformed for raw information",
    ),
]
