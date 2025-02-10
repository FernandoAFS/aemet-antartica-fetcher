"""
Test DB operations
"""

import random
from datetime import datetime, timedelta

import aiosqlite
import pytest

from aemetAntartica.db.db_proxy import FetchPointDbProxy
from aemetAntartica.model.fetch import WeatherDataPointSeries


@pytest.fixture
@pytest.mark.asyncio
async def db_conn():
    async with aiosqlite.connect(":memory:") as conn:
        yield conn


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "d0, df, station_id",
    [
        (
            datetime.fromisoformat("2023-01-01T00:00:00+0000"),
            datetime.fromisoformat("2023-02-01T00:00:00+0000"),
            "Meteo Station Gabriel de Castilla",
        ),
        (
            datetime.fromisoformat("2023-01-01T00:00:00+0000"),
            datetime.fromisoformat("2023-02-01T00:00:00+0000"),
            "Meteo Station Juan Carlos I",
        ),
    ],
)
async def test_insert_fetch(d0: datetime, df: datetime, station_id: str):
    def gen_data_points():
        d = d0
        while d <= df:
            yield {
                "fhora": d,
                "temp": random.randint(0, 1000),
                "pres": random.randint(0, 1000),
                "vel": random.randint(0, 1000),
            }
            d = d + timedelta(minutes=10)

    series = WeatherDataPointSeries.model_validate({"points": list(gen_data_points())})

    async with aiosqlite.connect(":memory:") as db_conn:
        db_proxy = FetchPointDbProxy(db_connection=db_conn)
        await db_proxy.create_table()
        await db_proxy.insert_points(series.points, station_id)
        result = await db_proxy.fetch_between(d0, df, station_id)

        assert len(result) == len(series.points)

        for res, mock in zip(result, series.points):
            assert res.fhora == mock.fhora
            assert res.temp == mock.temp
            assert res.pres == mock.pres
            assert res.vel == mock.vel
