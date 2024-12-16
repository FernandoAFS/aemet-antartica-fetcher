"""
All aggregation functions that are based on iteration.
"""

import operator as op
from datetime import datetime, timedelta
from itertools import filterfalse, repeat
from math import isnan
from typing import Callable, Sequence


from .annot import AggregatorCb

from aemetAntartica.model.fetch import WeatherDataPoint
from aemetAntartica.util.itertools import grouper

type DateAgg = Callable[[Sequence[datetime]], datetime]
type FloatAgg = Callable[[Sequence[float]], float]


def calc_mean(vals: Sequence[float]) -> float:
    """
    Calc the mean ignoring nan values.
    """

    non_nan_vals = list(filterfalse(isnan, vals))

    if len(non_nan_vals) <= 0:
        return 0

    return sum(non_nan_vals) / len(non_nan_vals)


def calc_median(vals: Sequence[float]) -> float:
    """
    Calc the median of a given series.

    Takes the middle point if the series is odd and the average of the two center if it's even.
    """
    non_nan_vals = list(filterfalse(isnan, vals))

    if len(non_nan_vals) <= 0:
        return 0

    nn_sorted = sorted(non_nan_vals)
    len_ = len(nn_sorted)
    if len_ % 2 == 0:
        n = (len_ - 1) // 2
        return (nn_sorted[n] + nn_sorted[n + 1]) / 2
    else:
        return nn_sorted[(len_ - 1) // 2]


def do_model_calculation(
    models: Sequence[WeatherDataPoint],
    calc_f: FloatAgg,
    date_picker: DateAgg,
) -> WeatherDataPoint:
    """
    Apply function over every numeric property of the model.
    """

    def do_prop_agg(prop: str) -> float:
        vals = map(op.attrgetter(prop), models)
        return calc_f(list(vals))

    def pick_date() -> datetime:
        vals = map(op.attrgetter("fhora"), models)
        return date_picker(list(vals))

    temp_agg = do_prop_agg("temp")
    pres_agg = do_prop_agg("pres")
    vel_agg = do_prop_agg("vel")
    date = pick_date()

    return WeatherDataPoint(
        fhora=date,
        temp=temp_agg,
        pres=pres_agg,
        vel=vel_agg,
    )


def calc_points_period(dates: Sequence[datetime]) -> timedelta:
    "Given a list of points get the time between them."

    periods = list(
        map(
            op.sub,
            dates[1::],  # NEXT DATE...
            dates,
        )
    )

    # CHECK THAT THE FRECUENCY IS MORE OR LESS CONSTANT. RAISE WARNING IF NOT CONSTANT.

    # TODO: ANALYZE THIS... MAKE SURE THAT ALL ARE MORE OR LESS EQUAL...
    return periods[0]


# AGGREGATOR FUNCTIONS.


def picker_agg_factory[T](
    agg_f: Callable[[Sequence[T]], T],
    date_getter: Callable[[T], datetime],
):
    """
    Applies the function to a list of points directly.

    This is convenient for selectors such as first or last in group.
    """

    def agg_res(data_in: Sequence[T], period: timedelta) -> Sequence[T]:
        dates = list(map(date_getter, data_in))
        data_freq = calc_points_period(dates)

        n = period // data_freq

        chunks = grouper(data_in, n)
        return list(map(agg_f, chunks))

    return agg_res


"Take the first measurement of the group"
first_agg: AggregatorCb[WeatherDataPoint] = picker_agg_factory(
    agg_f=op.itemgetter(0),
    date_getter=op.attrgetter("fhora"),
)

"Take the last measurement of the group"
last_agg: AggregatorCb[WeatherDataPoint] = picker_agg_factory(
    agg_f=op.itemgetter(-1),
    date_getter=op.attrgetter("fhora"),
)


def calc_agg_factory[T](
    agg_f: FloatAgg,
    date_f: DateAgg,
    date_picker: Callable[[T], datetime],
    model_f: Callable[[Sequence[T], FloatAgg, DateAgg], T],
):
    """
    Generator of numeric aggregation functions.

    This is convenient for numeric type transformations.
    """

    def calc_agg(data_in: Sequence[T], period: timedelta) -> Sequence[T]:
        dates = list(map(date_picker, data_in))
        data_freq = calc_points_period(dates)

        n = period // data_freq
        chunks = grouper(data_in, n)

        agg_iter = map(model_f, chunks, repeat(agg_f), repeat(date_f))
        return list(agg_iter)

    return calc_agg


"Calculate the mean of every numeric property"
mean_agg: AggregatorCb[WeatherDataPoint] = calc_agg_factory(
    agg_f=calc_mean,
    date_f=op.itemgetter(0),
    date_picker=op.attrgetter("fhora"),
    model_f=do_model_calculation,
)

"Calculate the median of every numeric property"
median_agg: AggregatorCb[WeatherDataPoint] = calc_agg_factory(
    agg_f=calc_median,
    date_f=op.itemgetter(0),
    date_picker=op.attrgetter("fhora"),
    model_f=do_model_calculation,
)

def identity_agg[T](data_in: Sequence[T], period: timedelta) -> Sequence[T]:
    """
    Used exclusively to represent raw data. Helps polimorphism.
    """
    return data_in
