"""
SQL cache logic
"""

import operator
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from math import isinf, isnan
from string import Template

import aiosqlite
import asyncstdlib
import structlog

from aemetAntartica.fetcher.annot import WeatherDataFetcher, WeatherPoint
from aemetAntartica.model.fetch import WeatherDataPoint, WeatherDataPointSeries
from aemetAntartica.model.tz_fetch import change_series_timezone
from aemetAntartica.util.bisect import remove_gap

logger = structlog.get_logger(__name__)

# SQL STATEMENTS FUNCTIONS AND DECLARATIONS

_SQL_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

_CREATE_TABLE_STATEMENT = """
CREATE TABLE IF NOT EXISTS datapoints(
    fhora DATETIME ,
    station VARCHAR,
    vel FLOAT,
    temp FLOAT,
    pres FLOAT,
    PRIMARY KEY(fhora, station)
);
""".strip()


_FETCH_COLUMNS = ["fhora", "vel", "temp", "pres"]
_FETCH_INTERVAL_TEMPLATE = Template(
    """
SELECT
    fhora,
    vel,
    temp,
    pres
FROM datapoints
WHERE
    station == "$station_id"
    and fhora between "$date_0" and "$date_f"
ORDER BY fhora;
""".strip()
)


def insert_statement_gen(d_in: Sequence[WeatherDataPoint], station: str) -> str:
    """
    Insert statement function generator.
    """

    def float_format(d: float) -> str:
        if isnan(d):
            return '"NaN"'
        if isinf(d):
            return '"NaN"'
        return f"{d}"

    def data_upd_gen():
        for d in d_in:
            date = d.fhora.strftime(_SQL_DATE_FORMAT)
            yield f'("{date}", "{station}", {float_format(d.vel)}, {float_format(d.temp)}, {float_format(d.pres)})'

    values = ",\n".join(data_upd_gen())

    return f"""
INSERT INTO datapoints (fhora, station, vel, temp, pres )
values {values};
    """.strip()


# PROXY CLASS:


@dataclass
class SqliteCacheFetcherProxy:
    """
    Proxy fetcher that captures requests. Answers with sqlite data if possible and delegates on fetcher for true data-source.

    Don't istanciate directly. Use sqlite_cache_fetcher_proxy_factory.
    """

    fetcher: WeatherDataFetcher[WeatherPoint]
    sqlite_uri: str
    date_offset: timedelta = timedelta(minutes=10)

    async def stations(self) -> Sequence[str]:
        "Call fetcher"
        return await self.fetcher.stations()

    async def time_range(self, station_id: str) -> tuple[datetime, datetime]:
        "Call fetcher"
        return await self.fetcher.time_range(station_id)

    async def timeseries(
        self, date_0: datetime, date_f: datetime, station_id: str
    ) -> Sequence[WeatherDataPoint]:
        """
        Fetch data from sql. Check for gaps. Fetch those gaps in the network and finally insert them back to sql.
        """
        sel_stmt = _FETCH_INTERVAL_TEMPLATE.substitute(
            {
                "date_0": date_0.strftime(_SQL_DATE_FORMAT),
                "date_f": (date_f - self.date_offset).strftime(_SQL_DATE_FORMAT),
                "station_id": station_id,
            }
        )

        async def fetch_rows():
            async with (
                aiosqlite.connect(self.sqlite_uri) as db,
                db.execute(sel_stmt) as cursor,
            ):
                async for row in cursor:
                    yield row

        rows = await asyncstdlib.list(fetch_rows())

        logger.debug(
            "Fetched points from sql",
            n_points=len(rows),
        )

        def row_to_dict(row: tuple) -> dict:
            return dict(zip(_FETCH_COLUMNS, row))

        sql_res_series = WeatherDataPointSeries.model_validate(
            {"points": list(map(row_to_dict, rows))}  # type: ignore
        )
        sql_res_series_tz = change_series_timezone(UTC, sql_res_series)

        async def complete_fetching():
            """
            Fetch all the data not in sql database
            """

            if len(sql_res_series_tz.points) <= 0:
                logger.debug(
                    "No points fetchd. Taking all information from net provider"
                )
                return await self.fetcher.timeseries(date_0, date_f, station_id)

            sql_d0 = sql_res_series_tz.points[0].fhora
            sql_df = sql_res_series_tz.points[-1].fhora

            async def fetch_gap(d0: datetime, df: datetime):
                df_ = df
                if df_ <= d0:
                    return []
                logger.debug("Fetching gap", d0=d0, df=df_)
                return await self.fetcher.timeseries(d0, df, station_id)

            logger.debug(
                "Searching for gaps",
                req_d0=date_0,
                sql_d0=sql_d0,
                sql_df=sql_df,
                req_df=date_f,
            )

            pre_extra = await fetch_gap(date_0, sql_d0)
            # THIS DATE OFFSET MAY HELP HELP THE DATE GENERATOR LATER...
            pos_extra = await fetch_gap(sql_df + self.date_offset, date_f)
            return [
                *pre_extra,
                *pos_extra,
            ]

        extra_fetching = await complete_fetching()
        fetch_res_series = WeatherDataPointSeries.model_validate(
            {"points": extra_fetching}
        )

        async def insert_missing_data():
            """
            If there is data to insert include it in the database
            """

            if len(sql_res_series_tz.points) > 0:
                sql_d0 = sql_res_series_tz.points[0].fhora
                sql_df = sql_res_series_tz.points[-1].fhora

                insert_points = remove_gap(
                    fetch_res_series.points,
                    sql_d0,
                    sql_df,
                    key=operator.attrgetter("fhora"),
                )
            else:
                insert_points = fetch_res_series.points

            insert_stmt = insert_statement_gen(insert_points, station_id)

            # LOG
            async with aiosqlite.connect(self.sqlite_uri) as db:
                await db.execute(insert_stmt)
                await db.commit()
            logger.debug(
                "Point insert complete",
                n_points=len(fetch_res_series.points),
            )

        if len(fetch_res_series.points) > 0:
            await insert_missing_data()

        logger.info(
            "Sql cache return",
            sql_points=len(sql_res_series_tz.points),
            fetch_points=len(fetch_res_series.points),
        )

        return [
            *sql_res_series_tz.points,
            *fetch_res_series.points,
        ]


async def sqlite_cache_fetcher_proxy_factory(
    fetcher: WeatherDataFetcher[WeatherPoint], sqlite_uri: str
) -> SqliteCacheFetcherProxy:
    """
    Creates table if it doesn't exist already.
    """
    logger.info("Creating sql proxy for fetcher")
    async with aiosqlite.connect(sqlite_uri) as db:
        await db.executescript(_CREATE_TABLE_STATEMENT)
    return SqliteCacheFetcherProxy(fetcher=fetcher, sqlite_uri=sqlite_uri)
