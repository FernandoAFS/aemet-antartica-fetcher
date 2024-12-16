"""
Extra bisect-based functionality.
"""

from typing import Sequence, Callable
import bisect


def find_between[T, V](
    values: Sequence[T], left: V, right: V, key: Callable[[T], V]
) -> Sequence[T]:
    """
    Efficiently return only value between left and right limits.
    V value must be comparable
    """

    # IGNORING TYPES UNTIL THERE IS A WAY TO SPECIFY V AS COMPARABLE TYPE.
    s_vals = sorted(values, key=key)  # type: ignore
    ndx0 = bisect.bisect_left(s_vals, left, key=key)  # type: ignore
    ndxf = bisect.bisect_left(s_vals, right, key=key)  # type: ignore

    return s_vals[ndx0:ndxf]
