from backtester.cache import (
    HistoricalDataCache,
    HistoricalDataRequest,
)
from backtester.data import HistoricalDataFeed
from backtester.providers import (
    HistoricalDataProvider,
)


class HistoricalDataService:
    def __init__(
        self,
        *,
        provider: HistoricalDataProvider,
        cache: HistoricalDataCache,
    ):
        self.provider = provider
        self.cache = cache

    def get(
        self,
        request: HistoricalDataRequest,
        *,
        refresh: bool = False,
    ) -> HistoricalDataFeed:
        if (
            not refresh
            and self.cache.contains(request)
        ):
            return self.cache.load(request)

        feed = self.provider.fetch(request)

        if not isinstance(
            feed,
            HistoricalDataFeed,
        ):
            raise TypeError(
                "historical data provider must return "
                "a HistoricalDataFeed"
            )

        self.cache.save(
            request=request,
            feed=feed,
        )

        return feed