"""
Exceptions for fetching. Created to help error control
"""


class StationIdValueError(ValueError):
    "When station_id is not recognized."


class IniDateValueError(ValueError):
    "D0 is wrong"


class EndDateValueError(ValueError):
    "Df is wrong"


class DateRangeValueError(ValueError):
    "Both d0 and df are to blame. i.e. when df < d0"
