"""
Models used for data response
"""

from collections.abc import Sequence
from datetime import datetime
from typing import Literal, TypedDict

from aemetAntartica.model.fetch import WeatherDataPoint, WeatherDataPointSeries

from pydantic import BaseModel


class PaginationMixin(BaseModel):
    has_previous: bool
    has_next: bool


class WeatherDataPointSeriesPagination(WeatherDataPointSeries, PaginationMixin):
    "Pagination class of point to prevent bandwith issues."


def weather_data_point_pagination_factory(
    points: Sequence[WeatherDataPoint], skip: int, limit: int
) -> WeatherDataPointSeriesPagination:
    """
    Standard factory for easier pagination.
    """

    ndx_0 = skip
    ndx_f = skip + limit

    paged_data = points[ndx_0:ndx_f]

    has_previous = skip > 0
    has_next = ndx_f < len(points)

    return WeatherDataPointSeriesPagination(
        points=list(paged_data),
        has_previous=has_previous,
        has_next=has_next,
    )


WeatherPointResponseKey = Literal[
    "temp",
    "pres",
    "vel",
]


class WeatherPointResponse(TypedDict, total=False):
    fhora: datetime
    temp: float
    pres: float
    vel: float


class WeatherDataPointSeriesPaginationResult(PaginationMixin):
    "Pagination class of point to prevent bandwith issues."

    points: list[WeatherPointResponse]


def pagination_series_to_response(
    series: WeatherDataPointSeriesPagination, keys: Sequence[WeatherPointResponseKey]
) -> WeatherDataPointSeriesPaginationResult:
    """
    Factory of response series.
    """

    points_d: list[WeatherPointResponse] = series.model_dump()["points"]

    # RETURN ALL TYPES WHEN NO KEYS PROVIDED
    if len(keys) <= 0:
        return WeatherDataPointSeriesPaginationResult(
            points=points_d,
            has_previous=series.has_previous,
            has_next=series.has_next,
        )

    def reduce_d(d: WeatherPointResponse) -> WeatherPointResponse:
        return {k: d[k] for k in ["fhora", *keys]} # type: ignore

    reduced_points_d = list(map(reduce_d, points_d))

    return WeatherDataPointSeriesPaginationResult(
        points=reduced_points_d,
        has_previous=series.has_previous,
        has_next=series.has_next,
    )


