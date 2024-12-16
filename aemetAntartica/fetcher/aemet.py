"""
Fetcher service for aemet open data
"""
import logging
import operator as op
from asyncio import TaskGroup
from collections.abc import (
    Awaitable,
    Callable,
    Coroutine,
    Iterable,
    Mapping,
    Sequence,
)
from dataclasses import dataclass
from datetime import datetime, timedelta
from itertools import chain, repeat
from string import Template

import asyncstdlib
import httpx

from aemetAntartica.fetcher.fetch_functions import aemet_2_step_fetch
from aemetAntartica.util.itertools import grouper

from .annot import AemetWeatherPoint, StationMetaData
from .context import api_key_ctx, async_httpx_client_ctx
from .exceptions import (
    DateRangeValueError,
    EndDateValueError,
    IniDateValueError,
    StationIdValueError,
)

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

@dataclass(frozen=True)
class AemetWeatherDataFetcherMixin:
    """
    Fetch data from aemet open portal. https://opendata.aemet.es/...

    Stations metadata in memory and requests timesereis from aemet opendata portal.

    Timeseries method stub only. Implement in subclass.

    Naieve implementation. This will only work for requests with a max range of 1 month.
    """

    "Simple station metadata dict"
    stations_metadata: Mapping[str, StationMetaData]

    "Must have a requested key. See: https://opendata.aemet.es/centrodedescargas/inicio"
    api_key: str

    """Standard python template to generate ticket fetch uri.
    see https://docs.python.org/3/library/string.html#template-strings. The template will have the following parameters:
    - date0
    - dateF
    - station_id
    """
    uri_template: str = "https://opendata.aemet.es/opendata/api/antartida/datos/fechaini/$date0/fechafin/$dateF/estacion/$station_id"

    "Strftime date format use to interpolate date in uri string"
    uri_date_format: str = "%Y-%m-%dT%H:%M:%SUTC"

    def _get_station_metadata(self, station_name: str) -> StationMetaData:
        try:
            return self.stations_metadata[station_name]
        except KeyError as e:
            raise StationIdValueError(f"Station name {station_name} not found") from e

    async def stations(self) -> list[str]:
        return list(self.stations_metadata.keys())

    async def time_range(self, station_id: str) -> tuple[datetime, datetime]:
        station_metadata = self._get_station_metadata(station_id)
        return (
            station_metadata["date0"],
            station_metadata["datef"],
        )

    def _params_to_uri(self, date0: datetime, dateF: datetime, station_id: str) -> str:
        return Template(self.uri_template).substitute(
            {
                "date0": date0.strftime(self.uri_date_format),
                "dateF": dateF.strftime(self.uri_date_format),
                "station_id": station_id,
            }
        )

    def _common_timeseries_param_validation(
        self, date_0: datetime, date_f: datetime, station_id: str
    ):
        """
        Raise exception on commmon parameter errors.
        """
        station_metadata = self._get_station_metadata(station_id)

        d_min = station_metadata["date0"]
        d_max = station_metadata["datef"]

        if date_f < date_0:
            DateRangeValueError(
                f"end date must be later than init date: date_f={date_f}, date_0={date_0}"
            )

        if date_0 < d_min:
            raise IniDateValueError(
                f"Requested date is below minimum: min_date={d_min}, requested_d0={date_0}"
            )

        if date_f > d_max:
            raise EndDateValueError(
                f"Requested date is above max: max_date={d_max}, requested_dF={date_f}"
            )


@dataclass(frozen=True)
class AemetWeatherDataFetcherNaive(AemetWeatherDataFetcherMixin):
    """
    Straight forward implementation. Adequate for requests of up to a month.

    Not recommended in production. Adequate for very small requests only.
    """

    async def timeseries(
        self, date_0: datetime, date_f: datetime, station_id: str
    ) -> Sequence[AemetWeatherPoint]:
        """
        Directly fetch as much as possible in one request.
        """
        self._common_timeseries_param_validation(date_0, date_f, station_id)
        months_diff = date_f.month - date_0.month
        days_diff = date_f.day - date_0.day
        if (months_diff >= 1) & (days_diff > 0):
            raise DateRangeValueError(
                "This fetch implementation does not support requests of more than 1 month"
            )

        # REQUESTS PER SE
        station_metadata = self._get_station_metadata(station_id)
        ticket_uri = self._params_to_uri(
            date_0,
            date_f,
            station_metadata["station_id"],
        )

        async with (
            httpx.AsyncClient() as client,
        ):
            with (
                async_httpx_client_ctx(client),
                api_key_ctx(self.api_key),
            ):
                return await aemet_2_step_fetch(ticket_uri)


@dataclass(frozen=True, kw_only=True)
class AemetWeatherDataFetcherSerial(AemetWeatherDataFetcherMixin):
    """
    Request cascade for multi-month requests.

    Not recommended in production. Good for debugging or for resource-constrained environments.
    """

    "Used to generate monthly dates. Very relevant for caching."
    date_generator: Callable[[datetime, datetime], Iterable[datetime]]

    "Used to simply fetch the data from (presumably) aemet services"
    fetch_function: Callable[[str], Awaitable[list[AemetWeatherPoint]]]

    "Move the end of the day request few minutes before the start of the next one to avoid overlapping intervals"
    last_date_offset: timedelta = timedelta(minutes=10)

    async def timeseries(
        self, date_0: datetime, date_f: datetime, station_id: str
    ) -> Sequence[AemetWeatherPoint]:
        # PARAMETER VALIDATION
        self._common_timeseries_param_validation(date_0, date_f, station_id)


        dates_0 = list(self.date_generator(date_0, date_f))
        dates_f = map(op.sub, dates_0[1:], repeat(self.last_date_offset))

        station_metadata = self._get_station_metadata(station_id)

        uris = map(
            self._params_to_uri,
            dates_0,
            dates_f,
            repeat(station_metadata["station_id"]),
        )
        uris_l = list(uris)

        logger.debug("Making the following requests: ")
        for uri in uris_l:
            logger.debug(uri)

        async def req_iterable():
            async with httpx.AsyncClient() as client:
                with (
                    async_httpx_client_ctx(client),
                    api_key_ctx(self.api_key),
                ):
                    for ticket_uri in uris_l:
                        logger.debug("Requesting uri: %s", ticket_uri)
                        yield await self.fetch_function(ticket_uri)
                        logger.debug("Request competed sucessfully")

        # MUST DO THIS IN MEMORY SINCE ASYNC ITERABLE DON'T ALLOW FOR YIELD_FROM.
        res_matrix = await asyncstdlib.list(req_iterable())
        res_l = list(chain.from_iterable(res_matrix))
        return res_l


@dataclass(frozen=True, kw_only=True)
class AemetWeatherDataFetcherConcurrent(AemetWeatherDataFetcherMixin):
    """
    Parallel requests for multiple-months.

    This implementation may include overfetching. Filter in data validation step
    """

    "Used to generate monthly dates. Very relevant for caching."
    date_generator: Callable[[datetime, datetime], Iterable[datetime]]

    "Used to simply fetch the data from (presumably) aemet services"
    fetch_function: Callable[[str], Coroutine[None, None, Sequence[AemetWeatherPoint]]]

    "Max number of concurrent requests"
    max_concurrent_requests: int = 10

    "Move the end of the day request few minutes before the start of the next one to avoid overlapping intervals"
    last_date_offset: timedelta = timedelta(minutes=10)

    async def timeseries(
        self, date_0: datetime, date_f: datetime, station_id: str
    ) -> Sequence[AemetWeatherPoint]:
        # PARAMETER VALIDATION
        self._common_timeseries_param_validation(date_0, date_f, station_id)

        dates_0 = list(self.date_generator(date_0, date_f))
        dates_f = map(op.sub, dates_0[1:], repeat(self.last_date_offset))

        station_metadata = self._get_station_metadata(station_id)

        uris = map(
            self._params_to_uri,
            dates_0,
            dates_f,
            repeat(station_metadata["station_id"]),
        )

        coros = map(self.fetch_function, uris)
        concurrency_rate = min(self.max_concurrent_requests, len(dates_0) - 1)
        coros_chunks = grouper(coros, concurrency_rate)

        # DIVIDED IN 2 FUNCTIONS FOR EASIER READIBILITY.
        async def parallel_req():
            async with (
                httpx.AsyncClient() as client,
            ):
                with (
                    async_httpx_client_ctx(client),
                    api_key_ctx(self.api_key),
                ):
                    for coros_chunk in coros_chunks:
                        async with TaskGroup() as tg:
                            tasks = list(map(tg.create_task, coros_chunk))
                        for t in tasks:
                            yield t.result()

        # MUST DO THIS IN MEMORY SINCE ASYNC ITERABLE DON'T ALLOW FOR YIELD_FROM.
        res_matrix = await asyncstdlib.list(parallel_req())
        res_l = list(chain.from_iterable(res_matrix))

        return res_l
