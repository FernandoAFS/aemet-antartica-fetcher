"Test semaphore fetcher for max concurrent calls"

import pytest
from asyncio import sleep

from aemetAntartica.fetcher.semaphore_control import semaphore_data_fetcher_factory
from aemetAntartica.util.task_group import parallel_task
from unittest.mock import Mock


@pytest.mark.asyncio
@pytest.mark.parametrize("max_concurrent, n_requests", ([5, 7], [12, 30]))
async def test_semaphore_proxy(max_concurrent: int, n_requests: int):
    n = 0

    async def mock_fetcher_side_effect():
        nonlocal n
        n = n + 1
        assert n <= max_concurrent, "Overpassed max concurrent"
        await sleep(0.1)  # SIMULATE MINIMAL WORK TO ALLOW FOR CONCURRENT...
        n = n - 1

    mock_fetcher_method = Mock(side_effect=mock_fetcher_side_effect)
    mock_fetcher_object = Mock()
    mock_fetcher_object.timeseries = mock_fetcher_method
    mock_fetcher_object.stations = mock_fetcher_method
    mock_fetcher_object.time_range = mock_fetcher_method

    semaphore_fetcher = semaphore_data_fetcher_factory(
        mock_fetcher_object, max_concurrent
    )

    tasks = [semaphore_fetcher.stations() for _ in range(n_requests)]
    await parallel_task(*tasks)
    print(mock_fetcher_object.stations.calls())
