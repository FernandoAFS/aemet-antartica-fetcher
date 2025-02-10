from dataclasses import dataclass
from datetime import datetime, UTC
from typing import Sequence

import aiosqlite
import contextlib

from aemetAntartica.model.fetch import WeatherDataPoint, WeatherDataPointSeries
from aemetAntartica.model.tz_fetch import change_series_timezone

from .statements import (
    FETCH_INTERVAL_TEMPLATE,
    SQL_DATE_FORMAT,
    insert_statement_gen,
    FETCH_COLUMNS,
    CREATE_TABLE_STATEMENT,
    DROP_TABLE_STATEMENT,
)


@dataclass(frozen=True, kw_only=True)
class FetchPointDbProxy:
    "Wrapper class around db connection"

    db_connection: aiosqlite.Connection

    # TODO: FIX THE return type
    async def fetch_between(
        self, date_0: datetime, date_f, station_id: str
    ) -> list[WeatherDataPoint]:
        "Fetch interval of points"

        sel_stmt = FETCH_INTERVAL_TEMPLATE.substitute(
            {
                "date_0": date_0.strftime(SQL_DATE_FORMAT),
                "date_f": date_f.strftime(SQL_DATE_FORMAT),
                "station_id": station_id,
            }
        )

        async with self.db_connection.execute(sel_stmt) as cursor:
            rows = list(await cursor.fetchall())

        def row_to_dict(row: aiosqlite.Row) -> dict:
            return dict(zip(FETCH_COLUMNS, row))

        row_dicts = list(map(row_to_dict, rows))

        sql_res_series = WeatherDataPointSeries.model_validate({"points": row_dicts})
        sql_res_series_tz = change_series_timezone(UTC, sql_res_series)

        return sql_res_series_tz.points

    async def insert_points(self, points: Sequence[WeatherDataPoint], station: str):
        "Insert sequence of points"

        if len(points) <= 0:
            return

        series = WeatherDataPointSeries.model_validate({"points": points})
        sql_res_series_tz = change_series_timezone(UTC, series)
        stmt = insert_statement_gen(sql_res_series_tz.points, station)
        await self.db_connection.execute(stmt)
        await self.db_connection.commit()

    async def create_table(self):
        "Create a table from scratch if none available."
        await self.db_connection.executescript(CREATE_TABLE_STATEMENT)

    async def drop_table(self):
        "Drop table if any available"
        await self.db_connection.executescript(DROP_TABLE_STATEMENT)

    @contextlib.asynccontextmanager
    async def table_context(self):
        await self.create_table()
        yield
        await self.drop_table()
