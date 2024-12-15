"""
Types used for http open-api communications
"""

from enum import Enum
from typing import Annotated, TypeAlias

from fastapi import Path, Query


class AggTimeOpts(str, Enum):
    """
    Time options for aggregations
    """

    HOURLY = "hourly"
    DAILY = "daily"
    MONTHLY = "monthly"


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
