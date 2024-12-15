"""
Test of puerly numeric aggregation functions.
"""

from typing import Sequence

import pytest

from aemetAntartica.aggregator.iteration import calc_mean, calc_median

try:
    import numpy as np
except ImportError:
    np = None

np_exception = ImportError("Numpy optional dependency is required for this test.")


# TODO: IMPROVE THIS TEST INJECTING PARAMETERS WITH HYPOTHESIS
@pytest.mark.parametrize("values", [list(range(50))])
def test_calc_mean_np(values: Sequence[float]):
    """
    Compare results of iterable calculations and numpy calculations for mean
    """

    if np is None:
        raise np_exception

    np_mean = np.nanmean(values)
    iter_mean = calc_mean(values)

    assert np_mean == iter_mean, "Different result from numpy and iterable"


# TODO: IMPROVE THIS TEST INJECTING PARAMETERS WITH HYPOTHESIS
@pytest.mark.parametrize("values", [list(range(50))])
def test_calc_median_np(values: Sequence[float]):
    """
    Compare results of iterable calculations and numpy calculations for median
    """

    if np is None:
        raise np_exception

    np_mean = np.nanmedian(values)
    iter_mean = calc_median(values)

    assert np_mean == iter_mean, "Different result from numpy and iterable"
