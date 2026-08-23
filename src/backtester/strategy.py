from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Mapping

from backtester.data import Bar
from backtester.orders import Order


@dataclass(frozen=True)
class PositionView:
    symbol: str
    quantity: int
    average_entry_price: float


@dataclass(frozen=True)
class StrategyContext:
    bar: Bar
    history: Mapping[str, tuple[Bar, ...]]
    cash: float
    equity: float
    positions: Mapping[str, PositionView]


class Strategy(ABC):
    @abstractmethod
    def on_bar(
        self,
        context: StrategyContext,
    ) -> list[Order]:
        """
        Process one completed market bar and return new orders.

        Orders returned here are eligible for execution at the
        opening price of the next available bar for that symbol.
        """