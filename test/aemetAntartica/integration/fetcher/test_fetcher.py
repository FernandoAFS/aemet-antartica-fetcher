"""
Very straigth-forward fetcher integration tests.

Kept to a minimum. Prefer to download offline and keep tests unitary for simplicity.
"""

from datetime import datetime
from os import environ
from httpx import AsyncClient

import pytest

from aemetAntartica.fetcher.raw_fetcher import AemetWeatherDataFetcher
from aemetAntartica.fetcher.context import async_httpx_client_ctx
from aemetAntartica.fetcher.static import named_station_metadata


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
    fetcher = AemetWeatherDataFetcher(
        api_key=api_key,
        stations_metadata=named_station_metadata,
    )

    async with AsyncClient() as client:
        with async_httpx_client_ctx(client):
            await fetcher.timeseries(
                date_0=date_0,
                date_f=date_f,
                station_id=station,
            )
