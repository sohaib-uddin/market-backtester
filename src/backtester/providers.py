from abc import ABC, abstractmethod

from collections.abc import Callable
from datetime import timedelta
from typing import Any

from backtester.cache import (
    BarInterval,
    HistoricalDataRequest,
)
from backtester.data import Bar, HistoricalDataFeed


class HistoricalDataProvider(ABC):
    @abstractmethod
    def fetch(
        self,
        request: HistoricalDataRequest,
    ) -> HistoricalDataFeed:
        """
        Retrieve historical bars for one validated request.
        """
class YahooFinanceProvider(
    HistoricalDataProvider
):
    INTERVAL_VALUES = {
        BarInterval.ONE_MINUTE: "1m",
        BarInterval.FIVE_MINUTES: "5m",
        BarInterval.FIFTEEN_MINUTES: "15m",
        BarInterval.ONE_HOUR: "1h",
        BarInterval.ONE_DAY: "1d",
    }

    INTERVAL_DURATIONS = {
        BarInterval.ONE_MINUTE: timedelta(
            minutes=1
        ),
        BarInterval.FIVE_MINUTES: timedelta(
            minutes=5
        ),
        BarInterval.FIFTEEN_MINUTES: timedelta(
            minutes=15
        ),
        BarInterval.ONE_HOUR: timedelta(
            hours=1
        ),
        BarInterval.ONE_DAY: timedelta(
            days=1
        ),
    }

    def __init__(
        self,
        *,
        downloader: Callable[..., Any]
        | None = None,
    ):
        if downloader is None:
            try:
                import yfinance
            except ImportError as error:
                raise RuntimeError(
                    "yfinance is required for the "
                    "Yahoo Finance provider"
                ) from error

            downloader = yfinance.download

        self._downloader = downloader

    def fetch(
        self,
        request: HistoricalDataRequest,
    ) -> HistoricalDataFeed:
        interval = self.INTERVAL_VALUES[
            request.interval
        ]

        exclusive_end = (
            request.end
            + self.INTERVAL_DURATIONS[
                request.interval
            ]
        )

        frame = self._downloader(
            tickers=request.symbol,
            start=request.start,
            end=exclusive_end,
            interval=interval,
            auto_adjust=True,
            repair=True,
            progress=False,
            threads=False,
            multi_level_index=False,
        )

        if frame is None or frame.empty:
            raise ValueError(
                "provider returned no data for "
                f"{request.symbol}"
            )

        bars = []

        for timestamp, row in frame.iterrows():
            if hasattr(
                timestamp,
                "to_pydatetime",
            ):
                timestamp = (
                    timestamp.to_pydatetime()
                )

            bars.append(
                Bar(
                    symbol=request.symbol,
                    timestamp=timestamp,
                    open=float(row["Open"]),
                    high=float(row["High"]),
                    low=float(row["Low"]),
                    close=float(row["Close"]),
                    volume=int(row["Volume"]),
                )
            )

        return HistoricalDataFeed(bars)