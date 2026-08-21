from dataclasses import dataclass
from datetime import datetime
from collections.abc import Iterable, Iterator


@dataclass(frozen=True)
class Bar:
    symbol: str
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float 
    volume: int 

    def __post_init__(self):
        normalised_symbol = self.symbol.strip().upper()

        if not normalised_symbol:
            raise ValueError("symbol must not be empty")

        object.__setattr__(
            self,
            "symbol",
            normalised_symbol,
        )

        prices = {
            "open": self.open,
            "high": self.high,
            "low": self.low,
            "close": self.close,
        }

        for name, price in prices.items():
            if price <= 0:
                raise ValueError(f"{name} must be positive")

        if self.high < max(self.open, self.low, self.close):
            raise ValueError(
                "high must be greater than or equal to open, low, and close"
            )

        if self.low > min(self.open, self.high, self.close):
            raise ValueError(
                "low must be less than or equal to open, high, and close"
            )

        if self.volume < 0:
            raise ValueError("volume must not be negative")

class HistoricalDataFeed:
    def __init__(self, bars: Iterable[Bar]):
        sorted_bars = sorted(
            bars,
            key=lambda bar: (bar.timestamp, bar.symbol),
        )

        bar_keys = [
            (bar.symbol, bar.timestamp)
            for bar in sorted_bars
        ]

        if len(bar_keys) != len(set(bar_keys)):
            raise ValueError(
                "duplicate bars found for the same symbol and timestamp"
            )

        self._bars = tuple(sorted_bars)

    def __iter__(self) -> Iterator[Bar]:
        return iter(self._bars)

    def __len__(self) -> int:
        return len(self._bars)

    @property
    def symbols(self) -> tuple[str, ...]:
        return tuple(
            sorted({bar.symbol for bar in self._bars})
        )

    def filter(
        self,
        *,
        symbols: Iterable[str] | None = None,
        start: datetime | None = None,
        end: datetime | None = None,
    ) -> "HistoricalDataFeed":
        if start is not None and end is not None and start > end:
            raise ValueError("start must not be later than end")

        selected_symbols = None

        if symbols is not None:
            selected_symbols = {
                symbol.strip().upper()
                for symbol in symbols
            }

        filtered_bars = [
            bar
            for bar in self._bars
            if (
                selected_symbols is None
                or bar.symbol.upper() in selected_symbols
            )
            and (
                start is None
                or bar.timestamp >= start
            )
            and (
                end is None
                or bar.timestamp <= end
            )
        ]

        return HistoricalDataFeed(filtered_bars)