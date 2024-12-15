from collections.abc import Iterable
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


date_range_30 = partial(date_range, timedelta(days=30))


def monthly_date_range(d0: datetime, df: datetime):
    "Incremtal generator from d0 to df, both included."
    d0_ = d0.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    df_ = df.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    while d0_ <= df_:
        yield d0_
        d0_ = d0_.replace(month=d0_.month + 1)
