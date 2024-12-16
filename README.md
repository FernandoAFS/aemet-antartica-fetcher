
# Aemet Antartica data fetching

Fast-api based aemet-antartica data fetcher.

Usage requires amet-api-key. More information in [AEMET OpenData](https://opendata.aemet.es/centrodedescargas/inicio)

## Install

`poetry install [--all-extras]`

Recommended all extras for testing...


## Dev run

```
poetry shell
AEMET_API_KEY="<YOUR-AEMET-KEY>" fastapi dev aemetAntartica/app/app.py
```

Then check your [localhost:8000/docs](http://localhost:8000/docs)


## Testing:

### Unit testing:

```
poetry shell
pytest pytest test/aemetAntartica/unitary/
```

### Integration testing:

```
poetry shell
AEMET_API_KEY="<YOUR-AEMET-KEY>" pytest test/aemetAntartica/integration/
```

This tests are done to check the different fetch implementation.


## Config:

All config options are environment-variable based:

### Required:

- AEMET_API_KEY: aemet open data api key.

### Optional:

- AEMET_FETCHER_TYPE: serial, concurrent or naive (default: serial)
- AEMET_CACHED: none or memory (default: memory)
- AEMET_DATE_GEN: month or naive (default: month)
- AEMET_STATIONS_METADATA_JSON: path to the stations metadata file (default data if none)
- AEMET_TIMEZONE_RESULT: any timezone from. See zoneinfo.available_timzone(). (default: Europe/Madrid)
