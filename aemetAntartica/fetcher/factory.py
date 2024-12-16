"""
Functions to create instance
"""

import json
from functools import cache
from os import environ

from aemetAntartica.util.datetime import date_range_30, monthly_date_range

from .aemet import (
    AemetWeatherDataFetcherConcurrent,
    AemetWeatherDataFetcherNaive,
    AemetWeatherDataFetcherSerial,
)
from .annot import WeatherDataFetcher, WeatherPoint
from .fetch_functions import aemet_2_step_fetch, cached_aemet_2_step_fetch
from .static import named_station_metadata


def gen_aemet_fetcher_env_var() -> WeatherDataFetcher[WeatherPoint]:
    """
    Return an AEMET fetcher based on environment_variables

    Environment Variables:
    - AEMET_API_KEY: aemet open data api key. (required)
    - AEMET_FETCHER_TYPE: serial, concurrent or naive (default: serial)
    - AEMET_CACHED: none or memory (default: memory)
    - AEMET_DATE_GEN: month or naive (default: month)
    - AEMET_STATIONS_METADATA_JSON: path to the stations metadata file (default data if none)
    """

    # TODO: EXPAND THE ENVIRONMENT VARIABLES FOR ALL OPTIONAL ARGUMENTS.
    # TODO: INCLUDE MOCK TYPE

    api_key = environ["AEMET_API_KEY"]
    fetcher_type = environ.get("AEMET_FETCHER_TYPE", "SERIAL").upper()
    cached_env = environ.get("AEMET_CACHED", "MEMORY").upper()
    date_gen_env = environ.get("AEMET_DATE_GEN", "MONTH").upper()
    meta_json_path = environ.get("AEMET_STATIONS_METADATA_JSON")

    if meta_json_path is not None:
        station_metadata = json.loads(meta_json_path)
    else:
        station_metadata = named_station_metadata

    if cached_env == "MEMORY":
        fetch_f = cached_aemet_2_step_fetch
    elif cached_env == "NONE":
        fetch_f = aemet_2_step_fetch
    else:
        raise ValueError(f"value fop AEMET_CACHED {cached_env} not supported")

    if date_gen_env == "MONTH":
        date_gen = monthly_date_range
    elif date_gen_env == "NAIVE":
        date_gen = date_range_30
    else:
        raise ValueError(f"value fop AEMET_DATE_GEN {date_gen_env} not supported")

    if fetcher_type == "SERIAL":
        return AemetWeatherDataFetcherSerial(
            stations_metadata=station_metadata,
            date_generator=date_gen,
            fetch_function=fetch_f,
            api_key=api_key,
        )
    elif fetcher_type == "CONCURRENT":
        return AemetWeatherDataFetcherConcurrent(
            stations_metadata=station_metadata,
            date_generator=date_gen,
            fetch_function=fetch_f,
            api_key=api_key,
        )
    elif fetcher_type == "NAIVE":
        return AemetWeatherDataFetcherNaive(
            stations_metadata=station_metadata,
            api_key=api_key,
        )

    raise ValueError(f"Value {fetcher_type} of FETCHER_TYPE not supported.")


cached_gen_aemet_fetcher_env_var = cache(gen_aemet_fetcher_env_var)
