from typing import TypeAlias, Literal
from fastapi import FastAPI
from .annot import Date0PathParam, DateFPathParam, StationIdPathParam, AggTypeQueryParam

AggregationTimeOptions: TypeAlias = (
    Literal["Hourly"] | Literal["Daily"] | Literal["Monthly"]
)

app = FastAPI()


@app.get("/api/antartida/datos/fechaini/{date0}/fechafin/{dateF}/estacion/{station_id}")
async def stationData(
    date0: Date0PathParam,
    dateF: DateFPathParam,
    station_id: StationIdPathParam,
    agg_type: AggTypeQueryParam = None,
):
    return {
        "date0": date0,
        "dateF": dateF,
        "station_id": station_id,
        "agg_type": agg_type,
    }
