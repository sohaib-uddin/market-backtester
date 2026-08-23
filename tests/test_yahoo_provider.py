from datetime import datetime, timedelta

import pytest

from backtester.cache import (
    BarInterval,
    HistoricalDataRequest,
)
from backtester.providers import YahooFinanceProvider


class FakeDataFrame:
    def __init__(self, rows):
        self._rows = rows
        self.empty = not rows

    def iterrows(self):
        yield from self._rows


def make_request():
    return HistoricalDataRequest(
        symbol="AAPL",
        interval=BarInterval.ONE_DAY,
        start=datetime(2025, 1, 2),
        end=datetime(2025, 1, 3),
    )


def test_yahoo_provider_converts_downloaded_rows():
    calls = []

    def fake_download(**kwargs):
        calls.append(kwargs)

        return FakeDataFrame(
            [
                (
                    datetime(2025, 1, 2),
                    {
                        "Open": 100.0,
                        "High": 104.0,
                        "Low": 99.0,
                        "Close": 102.0,
                        "Volume": 1_000,
                    },
                )
            ]
        )

    provider = YahooFinanceProvider(
        downloader=fake_download,
    )

    feed = provider.fetch(make_request())
    bars = list(feed)

    assert len(bars) == 1
    assert bars[0].symbol == "AAPL"
    assert bars[0].timestamp == datetime(
        2025,
        1,
        2,
    )
    assert bars[0].close == 102.0
    assert bars[0].volume == 1_000

    assert calls[0]["tickers"] == "AAPL"
    assert calls[0]["interval"] == "1d"
    assert calls[0]["start"] == datetime(
        2025,
        1,
        2,
    )
    assert calls[0]["end"] == (
        datetime(2025, 1, 3)
        + timedelta(days=1)
    )


def test_yahoo_provider_rejects_empty_response():
    provider = YahooFinanceProvider(
        downloader=lambda **kwargs: FakeDataFrame(
            []
        )
    )

    with pytest.raises(ValueError, match="no data"):
        provider.fetch(make_request())