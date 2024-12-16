"""
Extra itertools. Mostly taken from itertools documentation recepies
"""

from collections.abc import Iterable, Sequence

def grouper[T](iterable: Iterable[T], n: int) -> Iterable[Sequence[T]]:
    "Returns chunks of of items"
    iterators = [iter(iterable)] * n
    return zip(*iterators)
