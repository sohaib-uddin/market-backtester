import hashlib
import re
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path

from backtester.data import HistoricalDataFeed
from backtester.loaders import (
    CSVBarLoader,
    CSVBarWriter,
)


class BarInterval(Enum):
    ONE_MINUTE = "1m"
    FIVE_MINUTES = "5m"
    FIFTEEN_MINUTES = "15m"
    ONE_HOUR = "1h"
    ONE_DAY = "1d"


@dataclass(frozen=True)
class HistoricalDataRequest:
    symbol: str
    interval: BarInterval
    start: datetime
    end: datetime

    def __post_init__(self):
        normalised_symbol = self.symbol.strip().upper()

        if not normalised_symbol:
            raise ValueError(
                "symbol must not be empty"
            )

        if not isinstance(
            self.interval,
            BarInterval,
        ):
            raise TypeError(
                "interval must be a BarInterval"
            )

        if not isinstance(self.start, datetime):
            raise TypeError(
                "start must be a datetime"
            )

        if not isinstance(self.end, datetime):
            raise TypeError(
                "end must be a datetime"
            )

        if self.start > self.end:
            raise ValueError(
                "start must not be later than end"
            )

        object.__setattr__(
            self,
            "symbol",
            normalised_symbol,
        )


class HistoricalDataCache:
    def __init__(
        self,
        root_directory: str | Path,
    ):
        self.root_directory = Path(
            root_directory
        )

        self.loader = CSVBarLoader()
        self.writer = CSVBarWriter()

    def path_for(
        self,
        request: HistoricalDataRequest,
    ) -> Path:
        safe_symbol = re.sub(
            r"[^A-Z0-9._-]+",
            "_",
            request.symbol,
        ).strip("._")

        request_key = "|".join(
            [
                request.symbol,
                request.interval.value,
                request.start.isoformat(),
                request.end.isoformat(),
            ]
        )

        digest = hashlib.sha256(
            request_key.encode("utf-8")
        ).hexdigest()[:10]

        filename = (
            f"{safe_symbol}_"
            f"{request.interval.value}_"
            f"{request.start:%Y%m%dT%H%M%S}_"
            f"{request.end:%Y%m%dT%H%M%S}_"
            f"{digest}.csv"
        )

        return self.root_directory / filename

    def contains(
        self,
        request: HistoricalDataRequest,
    ) -> bool:
        return self.path_for(request).is_file()

    def save(
        self,
        *,
        request: HistoricalDataRequest,
        feed: HistoricalDataFeed,
    ):
        self._validate_feed(
            request=request,
            feed=feed,
        )

        self.writer.write(
            feed,
            self.path_for(request),
        )

    def load(
        self,
        request: HistoricalDataRequest,
    ) -> HistoricalDataFeed:
        return self.loader.load(
            self.path_for(request)
        )

    @staticmethod
    def _validate_feed(
        *,
        request: HistoricalDataRequest,
        feed: HistoricalDataFeed,
    ):
        for bar in feed:
            if bar.symbol != request.symbol:
                raise ValueError(
                    "cached bar symbol does not match "
                    "the historical data request"
                )

            if not (
                request.start
                <= bar.timestamp
                <= request.end
            ):
                raise ValueError(
                    "cached bar timestamp is outside "
                    "the requested date range"
                )