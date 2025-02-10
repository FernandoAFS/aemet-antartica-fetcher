"Teset monthly divider"

from datetime import datetime
import pytest
from asyncio import sleep

from aemetAntartica.fetcher.request_divider import (
    MonthlyTimeRequestDivider,
    monthly_divider,
)
from unittest.mock import Mock


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "d0, df",
    [
        (
            datetime.fromisoformat("2020-01-15T00:00:00+0000"),
            datetime.fromisoformat("2020-03-21T00:00:00+0000"),
        ),
    ],
)
async def test_monthly_divider(d0: datetime, df: datetime):
    "Test dates generation function"
    dates = list(monthly_divider(d0, df))
    assert dates[0] == d0
    assert dates[-1] == df

    for d in dates[1:-1]:
        assert d.day == 1
        assert d.hour == 0
        assert d.minute == 0

    year_diff = df.year - d0.year
    if year_diff > 0:
        month_offset = (d0.month - 12) + df.month
    else:
        month_offset = df.month - d0.month

    n_dates = month_offset + year_diff * 12
    if d0.day != 1:
        n_dates += 1
    if df.day != 1:
        n_dates += 1
    assert len(dates) == n_dates


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "d0, df, station_id",
    [
        (
            datetime.fromisoformat("2020-01-15T00:00:00+0000"),
            datetime.fromisoformat("2020-03-21T00:00:00+0000"),
            "station_1",
        ),
    ],
)
async def test_divider_fetcher(d0: datetime, df: datetime, station_id: str):
    "Test divider proxy"
    response_symbol = [object()]

    async def mock_fetcher_side_effect(d0_, df_, station_id_):
        assert station_id_ == station_id, "Unexpected station"
        await sleep(0.1)
        return response_symbol

    mock_fetcher_method = Mock(side_effect=mock_fetcher_side_effect)
    mock_fetcher_object = Mock()
    mock_fetcher_object.timeseries = mock_fetcher_method

    semaphore_fetcher = MonthlyTimeRequestDivider(fetcher=mock_fetcher_object)

    response = await semaphore_fetcher.timeseries(d0, df, station_id)
    assert response[0] is response_symbol[0]

    year_diff = df.year - d0.year
    if year_diff > 0:
        month_offset = (d0.month - 12) + df.month
    else:
        month_offset = df.month - d0.month

    n_dates = month_offset + year_diff * 12
    if d0.day != 1:
        n_dates += 1
    if df.day != 1:
        n_dates += 1

    assert len(mock_fetcher_method.mock_calls) == n_dates - 1
