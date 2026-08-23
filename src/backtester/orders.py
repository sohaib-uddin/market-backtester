from dataclasses import dataclass
from enum import Enum


class OrderSide(Enum):
    BUY = "buy"
    SELL = "sell"


@dataclass(frozen=True)
class Order:
    symbol: str
    quantity: int
    side: OrderSide

    def __post_init__(self):
        normalised_symbol = self.symbol.strip().upper()

        if not normalised_symbol:
            raise ValueError("symbol must not be empty")

        if isinstance(self.quantity, bool):
            raise TypeError("quantity must be an integer")

        if not isinstance(self.quantity, int):
            raise TypeError("quantity must be an integer")

        if self.quantity <= 0:
            raise ValueError("quantity must be positive")

        if not isinstance(self.side, OrderSide):
            raise TypeError("side must be an OrderSide")

        object.__setattr__(
            self,
            "symbol",
            normalised_symbol,
        )