"""
Functions to create instance
"""

import json
from os import environ
from typing import cast

import structlog

from aemetAntartica.fetcher.request_divider import MonthlyTimeRequestDivider
from aemetAntartica.fetcher.fetch_validation import FetchValidatorProxy
from aemetAntartica.fetcher.raw_fetcher import AemetWeatherDataFetcher
from aemetAntartica.fetcher.sql_cache_proxy import SqliteCacheFetcherProxy
from aemetAntartica.fetcher.timeout import FetcherTimeoutProxy
from aemetAntartica.model.fetch import WeatherDataPoint

from .annot import WeatherDataFetcher, WeatherPoint
from .fastapi import AemetFastapiErrorsWrapper
from .semaphore_control import semaphore_data_fetcher_factory
from .static import named_station_metadata

logger = structlog.get_logger()


async def gen_aemet_fetcher_env_var() -> WeatherDataFetcher[WeatherPoint]:
    """
    Return an AEMET fetcher based on environment_variables. Always wraps
    fetcher with fast-api errors proxy.

    Environment Variables:
    - "AEMET_API_KEY"
    - "AEMET_STATIONS_METADATA_JSON"
    - "AEMET_REQUEST_TIMEOUT"
    - "AEMET_MAX_CONCURRENT_REQUESTS"
    - "AEMET_SQLITE_URL"
    """

    api_key = environ["AEMET_API_KEY"]
    meta_json_path = environ.get("AEMET_STATIONS_METADATA_JSON")
    request_timeout = environ.get("AEMET_REQUEST_TIMEOUT")
    max_concurrent_requests = environ.get("AEMET_MAX_CONCURRENT_REQUESTS")
    sqlite_uri = environ.get("AEMET_SQLITE_URL")

    logger.debug(
        "Creating fetcher with environment configuration",
        meta_json_path=meta_json_path,
        request_timeout=request_timeout,
        max_concurrent_requests=max_concurrent_requests,
        sqlite_uri=sqlite_uri,
    )

    if meta_json_path is not None:
        station_metadata = json.loads(meta_json_path)
    else:
        station_metadata = named_station_metadata

    # RAW FETCHER
    fetcher: WeatherDataFetcher[WeatherPoint]
    fetcher = AemetWeatherDataFetcher(
        stations_metadata=station_metadata,
        api_key=api_key,
    )

    # TIMEOUT WRAPPER
    if request_timeout is not None:
        logger.debug("Including timeout check", request_timeout=request_timeout)
        fetcher = FetcherTimeoutProxy(
            fetcher=fetcher,
            seconds=int(request_timeout),
        )
    else:
        logger.debug("Omitting creation of timeout proxy")

    # MAX CONCURRENT WRAPPER
    if max_concurrent_requests is not None:
        logger.debug(
            "Including max concurrent requests proxy",
            max_concurrent_requests=max_concurrent_requests,
        )
        fetcher = semaphore_data_fetcher_factory(
            fetcher=fetcher,
            n=int(max_concurrent_requests),
        )
    else:
        logger.debug("Ommiting parallelization control")

    # REQUEST SLICER
    fetcher = MonthlyTimeRequestDivider(fetcher=fetcher)

    # VALIDATION WRAPPER
    model_fetcher = cast(
        WeatherDataFetcher[WeatherDataPoint], FetchValidatorProxy(fetcher=fetcher)
    )

    # SQLITE CACHE
    if sqlite_uri is not None:
        logger.debug(
            "Including sql cache",
            sqlite_uri=sqlite_uri,
        )
        model_fetcher = SqliteCacheFetcherProxy(fetcher=model_fetcher)
    else:
        logger.debug("Ommiting sql cache control")

    # ERROR MANAGEMENT
    return AemetFastapiErrorsWrapper(data_fetch=model_fetcher)  # type: ignore


__fetcher = None


async def cached_gen_aemet_fetcher_env_var():
    return await gen_aemet_fetcher_env_var()

    global __fetcher
    if __fetcher is None:
        __fetcher = await gen_aemet_fetcher_env_var()
    return __fetcher
