"""
Interface and typing definitions
"""

from typing import Protocol, Sequence
from datetime import timedelta


# TODO: MOVE FROM PERIOD GROUPER TO FUNCTIONAL GROUPER. LET IT RETURN SEQUENCES OF OBJECTS.
class AggregatorCb[T](Protocol):
    def __call__(self, data_in: Sequence[T], period: timedelta) -> Sequence[T]:
        """
        Given sequence of data return other sequence with the same type but not the same length.
        """
        ...
