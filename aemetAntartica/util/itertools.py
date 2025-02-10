"""
Extra itertools. Mostly taken from itertools documentation recepies
"""

from collections import deque
from collections.abc import Iterable, Sequence
from itertools import islice


def grouper[T](iterable: Iterable[T], n: int) -> Iterable[Sequence[T]]:
    "Returns chunks of of items"
    iterators = [iter(iterable)] * n
    return zip(*iterators)


def sliding_window[T](iterable: Iterable[T], n: int) -> Iterable[tuple[T, ...]]:
    "Collect data into overlapping fixed-length chunks or blocks."
    # sliding_window('ABCDEFG', 4) → ABCD BCDE CDEF DEFG
    iterator = iter(iterable)
    window = deque(islice(iterator, n - 1), maxlen=n)
    for x in iterator:
        window.append(x)
        yield tuple(window)
