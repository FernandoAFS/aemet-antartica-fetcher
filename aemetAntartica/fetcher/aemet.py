"""
Fetcher service for aemet open data
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Mapping
from string import Template

import httpx

from .annot import AemetTicketResponse, AemetWeatherPoint, StationMetaData
from .exceptions import EndDateValueError, IniDateValueError, StationIdValueError


@dataclass(frozen=True)
class AemetWeatherDataFetcher:
    """
    Fetch data from aemet open portal. https://opendata.aemet.es/...

    Stations metadata in memory and requests timesereis from aemet opendata portal.
    """

    "Must have a requested key. See: https://opendata.aemet.es/centrodedescargas/inicio"
    api_key: str

    "Simple station metadata dict"
    stations_metadata: Mapping[str, StationMetaData]

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

    async def stations(self) -> list[str]:
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

    async def timeseries(
        self, date0: datetime, dateF: datetime, station_id: str
    ) -> list[AemetWeatherPoint]:
        station_metadata = self._get_station_metadata(station_id)

        dMin = station_metadata["date0"]
        dMax = station_metadata["datef"]

        if date0 < dMin:
            raise IniDateValueError(
                f"Requested date is below minimum: min_date={dMin}, requested_d0={date0}"
            )

        if dateF > dMax:
            raise EndDateValueError(
                f"Requested date is above max: max_date={dMax}, requested_dF={dateF}"
            )

        ticket_uri = self._params_to_uri(
            date0,
            dateF,
            station_metadata["station_id"],
        )
        # TODO: INCLUDE LOGGING OF ALL THE URIS USED.

        headers = {"api_key": self.api_key}

        async with httpx.AsyncClient() as client:
            ticketReq = await client.get(ticket_uri, headers=headers)
            if ticketReq.status_code != httpx.codes.OK:
                raise ValueError(
                    "Aemet ticket request non OK response", ticket_uri, ticketReq
                )
            ticketJson: AemetTicketResponse = ticketReq.json()
            if ticketJson["estado"] != 200:
                raise ValueError(
                    "Aemet ticket content non OK status",
                    ticket_uri,
                    ticketReq,
                    ticketJson,
                )

            data_uri = ticketJson["datos"]
            dataReq = await client.get(data_uri)
            if dataReq.status_code != httpx.codes.OK:
                raise ValueError(
                    "Aemet data request non OK response", data_uri, dataReq
                )

            # IMPLICIT TYPE CASTING...
            return dataReq.json()
