from datetime import datetime
import pytest

from backtester.cache import (
    BarInterval,
    HistoricalDataCache,
    HistoricalDataRequest,
)
from backtester.data import Bar, HistoricalDataFeed


def make_request(
    *,
    symbol="AAPL",
    interval=BarInterval.ONE_MINUTE,
):
    return HistoricalDataRequest(
        symbol=symbol,
        interval=interval,
        start=datetime(2025, 1, 2),
        end=datetime(2025, 1, 31),
    )


def test_historical_data_request_normalises_symbol():
    request = make_request(
        symbol="  aapl  ",
    )

    assert request.symbol == "AAPL"


def test_cache_saves_and_restores_requested_data(
    tmp_path,
):
    cache = HistoricalDataCache(
        root_directory=tmp_path,
    )

    request = make_request()

    original_feed = HistoricalDataFeed(
        [
            Bar(
                symbol="AAPL",
                timestamp=datetime(
                    2025,
                    1,
                    2,
                    9,
                    31,
                ),
                open=100.0,
                high=104.0,
                low=99.0,
                close=102.0,
                volume=1_000,
            )
        ]
    )

    assert not cache.contains(request)

    cache.save(
        request=request,
        feed=original_feed,
    )

    assert cache.contains(request)

    restored_feed = cache.load(request)

    assert list(restored_feed) == list(original_feed)


def test_cache_uses_different_paths_for_intervals(
    tmp_path,
):
    cache = HistoricalDataCache(
        root_directory=tmp_path,
    )

    minute_request = make_request(
        interval=BarInterval.ONE_MINUTE,
    )

    daily_request = make_request(
        interval=BarInterval.ONE_DAY,
    )

    assert cache.path_for(
        minute_request
    ) != cache.path_for(
        daily_request
    )

def test_request_rejects_reversed_date_range():
    with pytest.raises(ValueError, match="start"):
        HistoricalDataRequest(
            symbol="AAPL",
            interval=BarInterval.ONE_DAY,
            start=datetime(2025, 2, 1),
            end=datetime(2025, 1, 1),
        )


def test_cache_rejects_wrong_symbol(tmp_path):
    cache = HistoricalDataCache(
        root_directory=tmp_path,
    )

    request = make_request(
        symbol="AAPL",
    )

    incorrect_feed = HistoricalDataFeed(
        [
            Bar(
                symbol="MSFT",
                timestamp=datetime(
                    2025,
                    1,
                    2,
                    9,
                    31,
                ),
                open=420.0,
                high=425.0,
                low=418.0,
                close=423.0,
                volume=900,
            )
        ]
    )

    with pytest.raises(
        ValueError,
        match="symbol",
    ):
        cache.save(
            request=request,
            feed=incorrect_feed,
        )


def test_cache_rejects_bar_outside_requested_range(
    tmp_path,
):
    cache = HistoricalDataCache(
        root_directory=tmp_path,
    )

    request = make_request()

    incorrect_feed = HistoricalDataFeed(
        [
            Bar(
                symbol="AAPL",
                timestamp=datetime(
                    2025,
                    2,
                    1,
                    9,
                    31,
                ),
                open=100.0,
                high=104.0,
                low=99.0,
                close=102.0,
                volume=1_000,
            )
        ]
    )

    with pytest.raises(
        ValueError,
        match="date range",
    ):
        cache.save(
            request=request,
            feed=incorrect_feed,
        )