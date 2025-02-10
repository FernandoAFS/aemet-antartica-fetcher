"""
Main fastapi app object with route definition
"""

from contextlib import asynccontextmanager
from os import environ
from uuid import uuid4
from httpx import AsyncClient

import aiosqlite
from fastapi import FastAPI, Request, Response
from structlog import get_logger
from structlog.contextvars import (
    bind_contextvars,
)

from aemetAntartica.db.db_proxy import FetchPointDbProxy
from aemetAntartica.db.context import async_db_context_var_ctx
from aemetAntartica.fetcher.context import async_httpx_client_ctx

from .dependencies import AemetAggDataQuery
from .response import WeatherDataPointSeriesPaginationResult

logger = get_logger(__name__)

app = FastAPI()


@app.get(
    "/api/antartida/datos/fechaini/{date_0}/fechafin/{date_f}/estacion/{station_id}"
)
async def station_data(
    agg_data: AemetAggDataQuery,
) -> WeatherDataPointSeriesPaginationResult:
    """
    Fetch or agregate station timeseries data
    """
    return agg_data  # type: ignore


@app.middleware("http")
async def syslogger_context(request: Request, call_next):
    request_id = str(uuid4())
    bind_contextvars(request_id=request_id)

    client = request.client
    logger.info(
        "Recieved request",
        agent=request.headers.get("User-Agent"),
        client=client.host if client is not None else "unknown",
        referer=request.url.hostname,
        path=request.url.path,
        query=request.url.query,
        request=request.method,
    )

    response: Response = await call_next(request)

    if response.status_code == 200:
        logger.info("Successfull response")
    else:
        logger.info("Error response", status_code=response.status_code)

    return response


@app.middleware("http")
async def httpx_client_middleware(request: Request, call_next):
    logger.info("Creating httpx client context")
    async with (
        AsyncClient() as client,
    ):
        with async_httpx_client_ctx(client):
            return await call_next(request)

@app.middleware("http")
async def db_context(request: Request, call_next):
    sqlite_uri = environ.get("AEMET_SQLITE_URL")

    # DO NOTHING
    if sqlite_uri is None:
        logger.debug("Skipping sqlite context")
        return await call_next(request)

    logger.debug("Starting sqlite context")
    async with aiosqlite.connect(sqlite_uri) as conn:
        db_proxy = FetchPointDbProxy(db_connection=conn)
        async with db_proxy.table_context():
            with async_db_context_var_ctx(db_proxy):
                return await call_next(request)


