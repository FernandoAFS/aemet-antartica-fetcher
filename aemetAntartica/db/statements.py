from collections.abc import Sequence
from math import isinf, isnan
from string import Template

import structlog

from aemetAntartica.model.fetch import WeatherDataPoint

logger = structlog.get_logger(__name__)

SQL_DATE_FORMAT = "%Y-%m-%d %H:%M:%SZ"

CREATE_TABLE_STATEMENT = """
CREATE TABLE IF NOT EXISTS datapoints(
    fhora DATETIME ,
    station VARCHAR,
    vel FLOAT,
    temp FLOAT,
    pres FLOAT,
    PRIMARY KEY(fhora, station)
);
""".strip()

DROP_TABLE_STATEMENT = """
DROP TABLE IF EXISTS datapoints;
""".strip()


FETCH_COLUMNS = ["fhora", "vel", "temp", "pres"]
FETCH_INTERVAL_TEMPLATE = Template(
    """
SELECT
    fhora,
    vel,
    temp,
    pres
FROM datapoints
WHERE
    station == "$station_id"
    and fhora between "$date_0" and "$date_f"
ORDER BY fhora;
""".strip()
)


def insert_statement_gen(d_in: Sequence[WeatherDataPoint], station: str) -> str:
    """
    Insert statement function generator.
    """

    def float_format(d: float) -> str:
        if isnan(d):
            return '"NaN"'
        if isinf(d):
            return '"NaN"'
        return f"{d}"

    def data_upd_gen():
        for d in d_in:
            date = d.fhora.strftime(SQL_DATE_FORMAT)
            yield f'("{date}", "{station}", {float_format(d.vel)}, {float_format(d.temp)}, {float_format(d.pres)})'

    values = ",\n".join(data_upd_gen())

    return f"""
INSERT INTO datapoints (fhora, station, vel, temp, pres )
values {values};
    """.strip()
