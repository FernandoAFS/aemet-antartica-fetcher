"""
Pure functions to be used by different fetcher service implementations
"""

import httpx

from .annot import AemetTicketResponse, AemetWeatherPoint
from .context import async_httpx_client_var, api_key_var
from asyncstdlib import lru_cache


async def aemet_fetch_ticket(ticket_uri: str) -> AemetTicketResponse:
    """
    Fetch the ticket for antartica data.
    """
    client = async_httpx_client_var.get()
    api_key = api_key_var.get()
    headers = {"api_key": api_key}
    ticketReq = await client.get(ticket_uri, headers=headers)

    if ticketReq.status_code != httpx.codes.OK:
        raise ValueError("Aemet ticket request non OK response", ticket_uri, ticketReq)
    ticketJson: AemetTicketResponse = ticketReq.json()
    if ticketJson["estado"] != 200:
        raise ValueError(
            "Aemet ticket content non OK status",
            ticket_uri,
            ticketReq,
            ticketJson,
        )

    return ticketJson


async def aemet_fetch_data(data_uri: str) -> list[AemetWeatherPoint]:
    """
    Fetch data given the uri in a ticket.
    """
    client = async_httpx_client_var.get()
    api_key = api_key_var.get()

    headers = {"api_key": api_key}
    dataReq = await client.get(data_uri, headers=headers)
    if dataReq.status_code != httpx.codes.OK:
        raise ValueError("Aemet data request non OK response", data_uri, dataReq)
    # IMPLICIT TYPE CASTING...
    return dataReq.json()


async def aemet_2_step_fetch(ticket_uri: str) -> list[AemetWeatherPoint]:
    """
    Wrapper around ticket and data fetching.
    """

    ticket = await aemet_fetch_ticket(ticket_uri)
    return await aemet_fetch_data(ticket["datos"])


@lru_cache
async def cached_aemet_2_step_fetch(ticket_uri: str) -> list[AemetWeatherPoint]:
    "Cached wrapper around aemet_2_step_fetch"
    return await aemet_2_step_fetch(ticket_uri)
