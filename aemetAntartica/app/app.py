"""
Main fastapi app object with route definition
"""

from fastapi import FastAPI

from .dependencies import AemetAggDataQuery
from .response import WeatherDataPointSeriesPaginationResult

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
