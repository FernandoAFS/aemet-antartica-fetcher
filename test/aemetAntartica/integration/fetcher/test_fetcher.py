"""
Very straigth-forward fetcher integration tests.

Kept to a minimum. Prefer to download offline and keep tests unitary for simplicity.
"""

from datetime import datetime
from os import environ

import pytest

from aemetAntartica.fetcher.aemet import (
    AemetWeatherDataFetcherConcurrent,
    AemetWeatherDataFetcherNaive,
    AemetWeatherDataFetcherSerial,
)
from aemetAntartica.fetcher.fetch_functions import (
    aemet_2_step_fetch,
    cached_aemet_2_step_fetch,
)
from aemetAntartica.fetcher.static import named_station_metadata
from aemetAntartica.util.datetime import monthly_date_range


@pytest.fixture
def api_key() -> str:
    # TODO: MOVE TO ENVIRONMENT_VARIABLES.

    try:
        return environ["AEMET_API_KEY"]
    except KeyError as e:
        raise KeyError(
            "AEMET_API_KEY environment variable is required to run this test. See README."
        ) from e


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "date_0, date_f, station",
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
async def test_naive_fetcher(
    date_0: datetime, date_f: datetime, station: str, api_key: str
):
    """
    Simple test of naieve aemet adata fetcher
    """
    fetcher = AemetWeatherDataFetcherNaive(
        api_key=api_key,
        stations_metadata=named_station_metadata,
    )

    await fetcher.timeseries(
        date_0=date_0,
        date_f=date_f,
        station_id=station,
    )


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "date_0, date_f, station",
    [
        (
            datetime.fromisoformat("2023-01-01T00:00:00+0000"),
            datetime.fromisoformat("2023-03-01T00:00:00+0000"),
            "Meteo Station Gabriel de Castilla",
        ),
        (
            datetime.fromisoformat("2023-01-01T00:00:00+0000"),
            datetime.fromisoformat("2023-03-01T00:00:00+0000"),
            "Meteo Station Juan Carlos I",
        ),
    ],
)
async def test_serial_fetcher(
    date_0: datetime, date_f: datetime, station: str, api_key: str
):
    """
    Simple test of serial aemet fetcher
    """

    fetcher = AemetWeatherDataFetcherSerial(
        api_key=api_key,
        stations_metadata=named_station_metadata,
        date_generator=monthly_date_range,
        fetch_function=aemet_2_step_fetch,
    )

    await fetcher.timeseries(
        date_0=date_0,
        date_f=date_f,
        station_id=station,
    )


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "date_0, date_f, station",
    [
        (
            datetime.fromisoformat("2023-01-01T00:00:00+0000"),
            datetime.fromisoformat("2023-03-01T00:00:00+0000"),
            "Meteo Station Gabriel de Castilla",
        ),
        (
            datetime.fromisoformat("2023-01-01T00:00:00+0000"),
            datetime.fromisoformat("2023-03-01T00:00:00+0000"),
            "Meteo Station Juan Carlos I",
        ),
    ],
)
async def test_concurrent_fetcher(
    date_0: datetime, date_f: datetime, station: str, api_key: str
):
    """
    Simple test of concurrent aemet fetcher
    """

    fetcher = AemetWeatherDataFetcherConcurrent(
        api_key=api_key,
        stations_metadata=named_station_metadata,
        date_generator=monthly_date_range,
        fetch_function=aemet_2_step_fetch,
    )

    await fetcher.timeseries(
        date_0=date_0,
        date_f=date_f,
        station_id=station,
    )


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "date_0, date_f, station",
    [
        (
            datetime.fromisoformat("2023-01-01T00:00:00+0000"),
            datetime.fromisoformat("2023-03-01T00:00:00+0000"),
            "Meteo Station Gabriel de Castilla",
        ),
        (
            datetime.fromisoformat("2023-01-01T00:00:00+0000"),
            datetime.fromisoformat("2023-03-01T00:00:00+0000"),
            "Meteo Station Juan Carlos I",
        ),
    ],
)
async def test_serial_cached_fetcher(
    date_0: datetime, date_f: datetime, station: str, api_key: str
):
    """
    Simple test of serial cached aemet fetcher
    """

    fetcher = AemetWeatherDataFetcherSerial(
        api_key=api_key,
        stations_metadata=named_station_metadata,
        date_generator=monthly_date_range,
        fetch_function=cached_aemet_2_step_fetch,
    )

    await fetcher.timeseries(
        date_0=date_0,
        date_f=date_f,
        station_id=station,
    )


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "date_0, date_f, station",
    [
        (
            datetime.fromisoformat("2023-01-01T00:00:00+0000"),
            datetime.fromisoformat("2023-03-01T00:00:00+0000"),
            "Meteo Station Gabriel de Castilla",
        ),
        (
            datetime.fromisoformat("2023-01-01T00:00:00+0000"),
            datetime.fromisoformat("2023-03-01T00:00:00+0000"),
            "Meteo Station Juan Carlos I",
        ),
    ],
)
async def test_concurrent_cached_fetcher(
    date_0: datetime, date_f: datetime, station: str, api_key: str
):
    """
    Simple test of serial cached aemet fetcher
    """

    fetcher = AemetWeatherDataFetcherConcurrent(
        api_key=api_key,
        stations_metadata=named_station_metadata,
        date_generator=monthly_date_range,
        fetch_function=cached_aemet_2_step_fetch,
    )

    await fetcher.timeseries(
        date_0=date_0,
        date_f=date_f,
        station_id=station,
    )
