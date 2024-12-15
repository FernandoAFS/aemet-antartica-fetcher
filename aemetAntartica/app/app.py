"""
Main fastapi app object with route definition
"""

from fastapi import FastAPI

from .annot import AggTypeQueryParam, Date0PathParam, DateFPathParam, StationIdPathParam

app = FastAPI()


@app.get(
    "/api/antartida/datos/fechaini/{date_0}/fechafin/{date_f}/estacion/{station_id}"
)
async def station_data(
    date_0: Date0PathParam,
    date_f: DateFPathParam,
    station_id: StationIdPathParam,
    agg_type: AggTypeQueryParam = None,
):
    """
    Fetch or agregate station timeseries data
    """
    return {
        "date0": date_0,
        "dateF": date_f,
        "station_id": station_id,
        "agg_type": agg_type,
    }
