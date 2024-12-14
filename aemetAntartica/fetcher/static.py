"""
Static data definition for specific task at hand.

all is used as defaults.
"""

from typing import Mapping
from datetime import datetime
from .annot import StationMetaData

_date0 = datetime.fromisoformat("2020-01-01T00:00:00+0000")
_dateF = datetime.fromisoformat("2024-01-01T00:00:00+0000")

named_station_metadata: Mapping[str, StationMetaData] = {
    "Meteo Station Gabriel de Castilla": {
        "station_id": "89070",
        "date0": _date0,
        "datef": _dateF,
    },
    "Meteo Station Juan Carlos I": {
        "station_id": "89064",
        "date0": _date0,
        "datef": _dateF,
    },
}
