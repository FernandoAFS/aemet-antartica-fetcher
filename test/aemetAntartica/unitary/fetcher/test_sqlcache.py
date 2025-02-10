"Test in-memory sql cache"

import contextlib
import random
from collections.abc import AsyncGenerator
from datetime import datetime, timedelta
from unittest.mock import Mock

import aiosqlite
import pytest

from aemetAntartica.db.context import async_db_context_var_ctx
from aemetAntartica.db.db_proxy import FetchPointDbProxy
from aemetAntartica.fetcher.sql_cache_proxy import (
    SqliteCacheFetcherProxy,
    find_cache_gaps,
)
from aemetAntartica.model.fetch import WeatherDataPoint, WeatherDataPointSeries
from aemetAntartica.util.itertools import sliding_window

SQLITE_URI = "sqlite:///"


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "d0, df, informed, gap",
    [
        (
            datetime.fromisoformat("2020-01-15T00:00:00+0000"),
            datetime.fromisoformat("2020-03-01T00:00:00+0000"),
            [
                (
                    datetime.fromisoformat("2020-02-01T00:00:00+0000"),
                    datetime.fromisoformat("2020-02-03T00:00:00+0000"),
                ),
                (
                    datetime.fromisoformat("2020-02-06T00:00:00+0000"),
                    datetime.fromisoformat("2020-02-10T00:00:00+0000"),
                ),
            ],
            timedelta(hours=24),
        ),
    ],
)
async def test_gaps_finding(
    d0: datetime,
    df: datetime,
    informed: list[tuple[datetime, datetime]],
    gap: timedelta,
):
    def gen_dates():
        for d0, df in informed:
            d = d0
            while d <= df:
                yield d
                d += gap

    dates = list(gen_dates())

    gaps_mark = list(find_cache_gaps(d0, df, dates, gap))

    def expected_marks_gen():
        flat_informed = [d for t in informed for d in t]

        if informed[0][0] > d0:
            yield d0
            yield flat_informed[0] - gap

        for d0_, df_ in sliding_window(flat_informed[1:-1], 2):
            yield d0_ + gap
            yield df_ - gap

        if flat_informed[-1] < df:
            yield flat_informed[-1] + gap
            yield df

    expected_marks = list(expected_marks_gen())

    assert len(expected_marks) == len(gaps_mark)

    def print_tups():
        joins = map(
            "\t".join,
            zip(
                map(datetime.isoformat, expected_marks),
                map(datetime.isoformat, gaps_mark),
            ),
        )

        return "\n".join(joins)

    print()
    print(print_tups())

    for d_res, d_mock in zip(gaps_mark, expected_marks):
        assert d_res == d_mock


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "d01, df1, d02, df2",
    [
        (
            datetime.fromisoformat("2020-01-15T00:00:00+0000"),
            datetime.fromisoformat("2020-02-15T00:00:00+0000"),
            datetime.fromisoformat("2020-02-01T00:00:00+0000"),
            datetime.fromisoformat("2020-03-01T00:00:00+0000"),
        ),
    ],
)
async def test_sql_cache_overlap(
    d01: datetime, df1: datetime, d02: datetime, df2: datetime
):
    "Simple test of 2 subsequent overlapping requests"
    station_id = "static_station"
    gap = timedelta(hours=24)

    async def mock_fetcher_side_effect(d0_, df_, station_id_):
        "Make up data as we fetch."
        assert station_id_ == station_id
        if df_ <= d0_:
            return

        def gen_dates():
            d = d0_
            while d <= df_:
                yield d
                d = d + gap

        def gen_resp_items():
            for d in gen_dates():
                yield {
                    "fhora": d.isoformat(),
                    "temp": random.randint(0, 1000),
                    "pres": random.randint(0, 1000),
                    "vel": random.randint(0, 1000),
                }

        return WeatherDataPointSeries.model_validate(
            {"points": list(gen_resp_items())}
        ).points

    mock_fetcher_method = Mock(side_effect=mock_fetcher_side_effect)
    mock_fetcher_object = Mock()
    mock_fetcher_object.timeseries = mock_fetcher_method

    @contextlib.asynccontextmanager
    async def db_context() -> AsyncGenerator[FetchPointDbProxy]:
        async with aiosqlite.connect(":memory:") as conn:
            proxy = FetchPointDbProxy(db_connection=conn)
            mock_proxy = Mock(wraps=proxy)
            async with mock_proxy.table_context():
                with async_db_context_var_ctx(mock_proxy):
                    yield mock_proxy

    async with db_context():
        cached_fetcher = SqliteCacheFetcherProxy(
            fetcher=mock_fetcher_object, date_offset=gap
        )

        response1 = await cached_fetcher.timeseries(d01, df1, station_id)
        response2 = await cached_fetcher.timeseries(d02, df2, station_id)

    def filter_between(point: WeatherDataPoint) -> bool:
        return (point.fhora >= d02) & (point.fhora <= df1)

    response1_overlap = list(filter(filter_between, response1))
    response2_overlap = list(filter(filter_between, response2))

    assert response1[0].fhora == d01
    assert response1[-1].fhora == df1

    assert response2[0].fhora == d02
    assert response2[-1].fhora == df2

    assert len(response1_overlap) > 0
    assert len(response2_overlap) > 0
    assert len(response1_overlap) == len(response2_overlap)

    for r1, r2 in zip(response1_overlap, response2_overlap):
        assert r1.fhora == r2.fhora
        assert r1.temp == r2.temp
        assert r1.pres == r2.pres
        assert r1.vel == r2.vel
