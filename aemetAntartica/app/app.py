"""
Main fastapi app object with route definition
"""

from uuid import uuid4

from fastapi import FastAPI, Request, Response
from structlog import get_logger
from structlog.contextvars import (
    bind_contextvars,
)

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
