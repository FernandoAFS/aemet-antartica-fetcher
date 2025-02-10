from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime
from fastapi import HTTPException
import structlog

from .annot import WeatherDataFetcher
from .exceptions import (
    AemetRequestError,
    DateRangeValueError,
    EndDateValueError,
    IniDateValueError,
    StationIdValueError,
)


logger = structlog.getLogger(__name__)


@dataclass(frozen=True, kw_only=True)
class AemetFastapiErrorsWrapper[T]:
    "Wrap fetcher methods with fast-api http exceptions"

    data_fetch: WeatherDataFetcher[T]

    async def stations(self) -> Sequence[str]:
        """
        List all available stations IDs
        """
        return await self.data_fetch.stations()

    async def time_range(self, station_id: str) -> tuple[datetime, datetime]:
        """
        List all available stations IDs.

        Raises exception if station_id is not in supported stations.
        """
        return await self.data_fetch.time_range(station_id)

    async def timeseries(
        self, date_0: datetime, date_f: datetime, station_id: str
    ) -> Sequence[T]:
        """
        Request station data to external API.
        """

        logger.debug(
            "Request on errors wrapper",
            date_0=date_0,
            date_f=date_f,
            station_id=station_id,
        )

        def process_exception(e: Exception, desc: str):
            logger.warn(e, args=list(map(str, e.args)))
            return HTTPException(
                status_code=400,
                detail=desc,
            )

        try:
            ts = await self.data_fetch.timeseries(date_0, date_f, station_id)
        except StationIdValueError as e:
            raise process_exception(
                e, "Station Id deemed invalid by data provider"
            ) from e
        except IniDateValueError as e:
            raise process_exception(
                e, "Inital data deemed invalid by value provider"
            ) from e
        except EndDateValueError as e:
            raise process_exception(
                e, "End data deemed invalid by value provider"
            ) from e
        except DateRangeValueError as e:
            raise process_exception(
                e, "End data deemed invalid by value provider"
            ) from e
        except AemetRequestError as e:
            raise process_exception(e, "Error on aemet server") from e
        except Exception as e:
            raise process_exception(
                e, "Unexpected error while fetching data from external source"
            ) from e
        return ts
