"""
Raw enum types.
"""

from datetime import timedelta
from enum import Enum

from aemetAntartica.model.fetch import WeatherDataPoint
from aemetAntartica.aggregator.annot import AggregatorCb
from aemetAntartica.aggregator.iteration import first_agg, last_agg, mean_agg, median_agg, identity_agg

class AggTimeOpts(str, Enum):
    """
    Time options for aggregations
    """

    NONE = "none"
    HOURLY = "hourly"
    DAILY = "daily"
    MONTHLY = "monthly"

    def to_period(self) -> timedelta:
        """
        Return period given
        """
        if self == AggTimeOpts.NONE:
            # INVALID TD. SHOULDN'T BE USE.
            return timedelta(hours=0)
        if self == AggTimeOpts.HOURLY:
            return timedelta(hours=1)
        if self == AggTimeOpts.DAILY:
            return timedelta(days=1)
        if self == AggTimeOpts.MONTHLY:
            return timedelta(days=30)
        raise ValueError(f"Unfeasible enum value {self}")


class AggTypeOpts(str, Enum):
    """
    Type of aggregation to perform.
    """

    NONE = "none"
    FIRST = "first"
    LAST = "last"
    MEAN = "mean"
    MEDIAN = "median"

    def to_agg_f(self) -> AggregatorCb[WeatherDataPoint]:
        if self == AggTypeOpts.NONE:
            return identity_agg
        if self == AggTypeOpts.FIRST:
            return first_agg
        if self == AggTypeOpts.LAST:
            return last_agg
        if self == AggTypeOpts.MEAN:
            return mean_agg
        if self == AggTypeOpts.MEDIAN:
            return median_agg
        raise ValueError(f"Unfeasible enum value {self}")
