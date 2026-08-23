from datetime import datetime

from backtester.cache import (
    BarInterval,
    HistoricalDataCache,
    HistoricalDataRequest,
)
from backtester.data import Bar, HistoricalDataFeed
from backtester.providers import HistoricalDataProvider
from backtester.services import HistoricalDataService


class FakeProvider(HistoricalDataProvider):
    def __init__(self, feed):
        self.feed = feed
        self.requests = []

    def fetch(self, request):
        self.requests.append(request)
        return self.feed


def make_request():
    return HistoricalDataRequest(
        symbol="AAPL",
        interval=BarInterval.ONE_DAY,
        start=datetime(2025, 1, 2),
        end=datetime(2025, 1, 31),
    )


def make_feed():
    return HistoricalDataFeed(
        [
            Bar(
                symbol="AAPL",
                timestamp=datetime(
                    2025,
                    1,
                    2,
                ),
                open=100.0,
                high=104.0,
                low=99.0,
                close=102.0,
                volume=1_000,
            )
        ]
    )


def test_service_fetches_and_caches_missing_data(
    tmp_path,
):
    request = make_request()
    provider = FakeProvider(make_feed())
    cache = HistoricalDataCache(tmp_path)

    service = HistoricalDataService(
        provider=provider,
        cache=cache,
    )

    result = service.get(request)

    assert list(result) == list(make_feed())
    assert provider.requests == [request]
    assert cache.contains(request)


def test_service_reuses_cached_data(tmp_path):
    request = make_request()
    cache = HistoricalDataCache(tmp_path)

    cache.save(
        request=request,
        feed=make_feed(),
    )

    provider = FakeProvider(
        HistoricalDataFeed([])
    )

    service = HistoricalDataService(
        provider=provider,
        cache=cache,
    )

    result = service.get(request)

    assert list(result) == list(make_feed())
    assert provider.requests == []


def test_service_refresh_bypasses_existing_cache(
    tmp_path,
):
    request = make_request()
    cache = HistoricalDataCache(tmp_path)

    cache.save(
        request=request,
        feed=make_feed(),
    )

    provider = FakeProvider(make_feed())

    service = HistoricalDataService(
        provider=provider,
        cache=cache,
    )

    service.get(
        request,
        refresh=True,
    )

    assert provider.requests == [request]