"""
Purely declarative type definitions
"""

from collections.abc import Sequence
from typing import Protocol, TypedDict
from datetime import datetime


class StationMetaData(TypedDict):
    """
    Static metadata of each supported station.
    """

    station_id: str
    date0: datetime
    datef: datetime


# TODO: COMBINE GENERICS AND EXTENDS.
class WeatherDataFetcher[T: WeatherPoint](Protocol):
    """
    Return data from external weather API
    """

    async def stations(self) -> Sequence[str]:
        """
        List all available stations IDs
        """
        ...

    async def time_range(self, station_id: str) -> tuple[datetime, datetime]:
        """
        List all available stations IDs.

        Raises exception if station_id is not in supported stations.
        """
        ...

    async def timeseries(
        self, date_0: datetime, date_f: datetime, station_id: str
    ) -> Sequence[T]:
        """
        Request station data to external API.
        """
        ...


class WeatherPoint(TypedDict):
    """
    Miniumum information for fetcher return.
    """

    fhora: str
    temp: float
    pres: float
    vel: float


class AemetTicketResponse(TypedDict):
    """
    Type annotation for misc aemet return data
    """

    estado: int
    datos: str


class AemetWeatherPoint(WeatherPoint):
    """
    Extension of weather data point for aement
    """

    identificacion: str
    nombre: str
    latitud: float
    longitud: float
    altitud: float
    srs: str
    alt_nieve: float
    ddd: int
    dddstd: int
    dddx: int
    fhora: str
    hr: int
    ins: float
    lluv: float
    pres: float
    rad_kj_m2: float  # REVIEW...
    rad_w_m2: float
    rec: float  # REVIEW...
    temp: float
    tmn: float
    tmx: float
    ts: float
    tsb: float
    tsmn: float
    tsmx: float
    vel: float
    velx: float
    albedo: float
    difusa: float
    directa: float
    # global: float # RESERVED NAME...
    ir_solar: float
    neta: float
    par: float
    tcielo: float
    ttierra: float
    uvab: float
    uvb: float
    uvi: float
    qdato: int
