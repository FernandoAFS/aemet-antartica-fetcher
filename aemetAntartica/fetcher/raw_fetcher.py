"""
Fetcher service for aemet open data
"""

from collections.abc import (
    Mapping,
    Sequence,
)
from dataclasses import dataclass
from datetime import datetime
from string import Template

import httpx
import structlog

from .annot import AemetTicketResponse, AemetWeatherPoint, StationMetaData
from .context import async_httpx_client_var
from .exceptions import (
    DateRangeValueError,
    EndDateValueError,
    IniDateValueError,
    StationIdValueError,
    AemetRequestError,
)

logger = structlog.getLogger(__name__)


@dataclass(frozen=True)
class AemetWeatherDataFetcher:
    """
    Fetch data from aemet open portal. https://opendata.aemet.es/...

    Stations metadata in memory and requests timesereis from aemet opendata portal.

    Timeseries method stub only. Implement in subclass.

    Naieve implementation. This will only work for requests with a max range of 1 month.
    """

    "Simple station metadata dict"
    stations_metadata: Mapping[str, StationMetaData]

    "Must have a requested key. See: https://opendata.aemet.es/centrodedescargas/inicio"
    api_key: str

    """Standard python template to generate ticket fetch uri.
    see https://docs.python.org/3/library/string.html#template-strings. The template will have the following parameters:
    - date0
    - dateF
    - station_id
    """
    uri_template: str = "https://opendata.aemet.es/opendata/api/antartida/datos/fechaini/$date0/fechafin/$dateF/estacion/$station_id"

    "Strftime date format use to interpolate date in uri string"
    uri_date_format: str = "%Y-%m-%dT%H:%M:%SUTC"

    def _get_station_metadata(self, station_name: str) -> StationMetaData:
        try:
            return self.stations_metadata[station_name]
        except KeyError as e:
            raise StationIdValueError(f"Station name {station_name} not found") from e

    async def stations(self) -> Sequence[str]:
        return list(self.stations_metadata.keys())

    async def time_range(self, station_id: str) -> tuple[datetime, datetime]:
        station_metadata = self._get_station_metadata(station_id)
        return (
            station_metadata["date0"],
            station_metadata["datef"],
        )

    def _params_to_uri(self, date0: datetime, dateF: datetime, station_id: str) -> str:
        return Template(self.uri_template).substitute(
            {
                "date0": date0.strftime(self.uri_date_format),
                "dateF": dateF.strftime(self.uri_date_format),
                "station_id": station_id,
            }
        )

    def _common_timeseries_param_validation(
        self, date_0: datetime, date_f: datetime, station_id: str
    ):
        """
        Raise exception on commmon parameter errors.
        """
        station_metadata = self._get_station_metadata(station_id)

        d_min = station_metadata["date0"]
        d_max = station_metadata["datef"]

        if date_f < date_0:
            DateRangeValueError(
                f"end date must be later than init date: date_f={date_f}, date_0={date_0}"
            )

        if date_0 < d_min:
            raise IniDateValueError(
                f"Requested date is below minimum: min_date={d_min}, requested_d0={date_0}"
            )

        if date_f > d_max:
            raise EndDateValueError(
                f"Requested date is above max: max_date={d_max}, requested_dF={date_f}"
            )

    async def timeseries(
        self, date_0: datetime, date_f: datetime, station_id: str
    ) -> Sequence[AemetWeatherPoint]:
        """
        Directly fetch as much as possible in one request.
        """

        client = async_httpx_client_var.get()
        headers = {"api_key": self.api_key}

        # BASIC VALIDATION
        self._common_timeseries_param_validation(date_0, date_f, station_id)
        months_diff = date_f.month - date_0.month
        days_diff = date_f.day - date_0.day
        if (months_diff >= 1) & (days_diff > 0):
            raise DateRangeValueError(
                "This fetch implementation does not support requests of more than 1 month"
            )

        # REQUESTS PER SE

        ## METADATA
        station_metadata = self._get_station_metadata(station_id)
        ticket_uri = self._params_to_uri(
            date_0,
            date_f,
            station_metadata["station_id"],
        )

        logger.debug(
            "Starting ticket request",
            date_0=date_0,
            date_f=date_f,
            station_id=station_id,
        )
        ticketReq = await client.get(ticket_uri, headers=headers)

        if ticketReq.status_code != httpx.codes.OK:
            raise AemetRequestError(
                "Aemet ticket request non OK response", ticket_uri, ticketReq
            )

        ticket_json: AemetTicketResponse = ticketReq.json()
        # TODO: INCLUDE ERROR FOR TOO MANY REQUESTS
        if ticket_json["estado"] != 200:
            raise AemetRequestError(
                "Aemet ticket content non OK status",
                ticket_uri,
                ticketReq,
                ticket_json,
            )

        data_uri = ticket_json["datos"]

        logger.debug(
            "Starting data request", date_0=date_0, date_f=date_f, station_id=station_id
        )
        dataReq = await client.get(data_uri, headers=headers)
        if dataReq.status_code != httpx.codes.OK:
            raise AemetRequestError(
                "Aemet data request non OK response", data_uri, dataReq
            )

        logger.debug(
            "Data recieved", date_0=date_0, date_f=date_f, station_id=station_id
        )

        return dataReq.json()
