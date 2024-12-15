"""
Testing of chunk aggregation functions (not just the calculation per se)
"""

import operator as op
from collections.abc import Callable, Sequence
from datetime import datetime, timedelta

import pytest

from aemetAntartica.aggregator.iteration import (
    calc_agg_factory,
    calc_mean,
    calc_median,
    calc_points_period,
    picker_agg_factory,
)

try:
    import numpy as np
except ImportError:
    np = None

np_exception = ImportError("Numpy optional rependency required for this test")

_now = datetime.fromisoformat("2024-12-15")

def gen_dt(base: datetime, inc: timedelta):
    "Helper incremental monotonic datetime generator."
    i = base
    while True:
        yield i
        i += inc


@pytest.mark.parametrize("vals, period", [
    (list(zip(
        gen_dt(_now, timedelta(hours=1)),
        range(50),
    )),
    timedelta(hours=5),)
])
def test_first_agg_np(vals: Sequence[tuple[datetime, float]], period: timedelta):

    if np is None:
        raise np_exception

    # ADAPTED TO WORK WITH TUPLES INSTEAD OF MODEL PER SE.
    first_agg = picker_agg_factory(
        agg_f=op.itemgetter(0),
        date_getter=op.itemgetter(0),
    )

    firsts_iter = first_agg(vals, period)

    # NUMPY CALC COMPRARE

    dates = list(map(op.itemgetter(0), vals))
    data_freq = calc_points_period(dates)
    n_samples_period = (period // data_freq)
    arr = np.array(list(map(op.itemgetter(1), vals)))
    mat = arr.reshape(len(vals) // n_samples_period, n_samples_period, )

    firsts_np = mat[:, 0]

    assert len(firsts_iter) == len(firsts_np)

    for i, (iter_, np_) in enumerate(zip(firsts_iter, firsts_np)):
        assert iter_[1] == np_ , f"Mismatching value in {i} position."



@pytest.mark.parametrize("vals, period", [
    (list(zip(
        gen_dt(_now, timedelta(hours=1)),
        range(50),
    )),
    timedelta(hours=5),)
])
def test_last_agg_np(vals: Sequence[tuple[datetime, float]], period: timedelta):

    if np is None:
        raise np_exception

    # ADAPTED TO WORK WITH TUPLES INSTEAD OF MODEL PER SE.
    first_agg = picker_agg_factory(
        agg_f=op.itemgetter(-1),
        date_getter=op.itemgetter(0),
    )

    firsts_iter = first_agg(vals, period)

    # NUMPY CALC COMPRARE

    dates = list(map(op.itemgetter(0), vals))
    data_freq = calc_points_period(dates)
    n_samples_period = (period // data_freq)
    arr = np.array(list(map(op.itemgetter(1), vals)))
    mat = arr.reshape(len(vals) // n_samples_period, n_samples_period, )

    firsts_np = mat[:, -1]

    assert len(firsts_iter) == len(firsts_np)

    for i, (iter_, np_) in enumerate(zip(firsts_iter, firsts_np)):
        assert iter_[1] == np_ , f"Mismatching value in {i} position."


def do_tup_agg_factory(
    models: Sequence[tuple[datetime, float]],
    calc_f: Callable[[Sequence[float]], float],
    date_picker: Callable[[Sequence[datetime]], datetime],
):
    return (
        date_picker(list(map(op.itemgetter(0), models))),
        calc_f(list(map(op.itemgetter(1), models))),
    )


@pytest.mark.parametrize("vals, period", [
    (list(zip(
        gen_dt(_now, timedelta(hours=1)),
        range(50),
    )),
    timedelta(hours=5),)
])
def test_agg_mean_np(vals: Sequence[tuple[datetime, float]], period: timedelta):

    if np is None:
        raise np_exception

    # ADAPTED TO WORK WITH TUPLES INSTEAD OF MODEL PER SE.
    mean_agg = calc_agg_factory(
        agg_f=calc_mean,
        date_f=op.itemgetter(0),
        date_picker=op.itemgetter(0),
        model_f=do_tup_agg_factory,
    )

    firsts_iter = mean_agg(vals, period)

    # NUMPY CALC COMPRARE

    dates = list(map(op.itemgetter(0), vals))
    data_freq = calc_points_period(dates)
    n_samples_period = (period // data_freq)
    arr = np.array(list(map(op.itemgetter(1), vals)))
    mat = arr.reshape(len(vals) // n_samples_period, n_samples_period, )
    mat_mean = np.nanmean(mat, axis=1)

    assert len(firsts_iter) == len(mat_mean)

    for i, (iter_, np_) in enumerate(zip(firsts_iter, mat_mean)):
        assert iter_[1] == np_ , f"Mismatching value in {i} position."



@pytest.mark.parametrize("vals, period", [
    (list(zip(
        gen_dt(_now, timedelta(hours=1)),
        range(50),
    )),
    timedelta(hours=5),)
])
def test_agg_median_np(vals: Sequence[tuple[datetime, float]], period: timedelta):

    if np is None:
        raise np_exception

    # ADAPTED TO WORK WITH TUPLES INSTEAD OF MODEL PER SE.
    mean_agg = calc_agg_factory(
        agg_f=calc_median,
        date_f=op.itemgetter(0),
        date_picker=op.itemgetter(0),
        model_f=do_tup_agg_factory,
    )

    firsts_iter = mean_agg(vals, period)

    # NUMPY CALC COMPRARE

    dates = list(map(op.itemgetter(0), vals))
    data_freq = calc_points_period(dates)
    n_samples_period = (period // data_freq)
    arr = np.array(list(map(op.itemgetter(1), vals)))
    mat = arr.reshape(len(vals) // n_samples_period, n_samples_period, )
    mat_mean = np.nanmedian(mat, axis=1)

    assert len(firsts_iter) == len(mat_mean)

    for i, (iter_, np_) in enumerate(zip(firsts_iter, mat_mean)):
        assert iter_[1] == np_ , f"Mismatching value in {i} position."

