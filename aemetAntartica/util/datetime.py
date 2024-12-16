"""
datetime based utilities
"""

from collections.abc import Iterable, Callable
from datetime import datetime, timedelta
from functools import partial


def date_range(td: timedelta, d0: datetime, df: datetime) -> Iterable[datetime]:
    """
    Incremtal generator from d0 to df, both included.
    Naieve implementation. Not recommended for production since it doesn't help caching
    """
    d = d0
    while d < df:
        yield d
        d += td
    yield df


date_range_30: Callable[[datetime, datetime], Iterable[datetime]] = partial(
    date_range, timedelta(days=30)
)


def monthly_date_range(d0: datetime, df: datetime):
    "Incremtal generator from d0 to df, both included."

    if df <= d0:
        raise ValueError(f"End date must be later than init date: df={df}, d0={d0}")

    if d0.month == df.month:
        yield d0.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        yield df.replace(
            month=df.month + 1, day=1, hour=0, minute=0, second=0, microsecond=0
        )
        return

    d0_ = d0.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    df_ = df.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    while d0_ <= df_:
        yield d0_
        if d0_.month < 12:
            d0_ = d0_.replace(month=d0_.month + 1)
        else:
            d0_ = d0_.replace(year=d0_.year + 1, month=1)
