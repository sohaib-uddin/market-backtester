from dataclasses import dataclass
from datetime import datetime
from math import isfinite
from numbers import Real
from backtester.data import Bar

from backtester.orders import Order, OrderSide


@dataclass(frozen=True)
class Fill:
    symbol: str
    quantity: int
    side: OrderSide
    price: float
    timestamp: datetime
    commission: float = 0.0

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

        if isinstance(self.price, bool):
            raise TypeError("price must be a number")

        if not isinstance(self.price, Real):
            raise TypeError("price must be a number")

        if not isfinite(self.price) or self.price <= 0:
            raise ValueError("price must be positive and finite")

        if not isinstance(self.timestamp, datetime):
            raise TypeError("timestamp must be a datetime")

        if isinstance(self.commission, bool):
            raise TypeError("commission must be a number")

        if not isinstance(self.commission, Real):
            raise TypeError("commission must be a number")

        if not isfinite(self.commission) or self.commission < 0:
            raise ValueError(
                "commission must be non-negative and finite"
            )

        object.__setattr__(
            self,
            "symbol",
            normalised_symbol,
        )

    @property
    def gross_value(self) -> float:
        return self.price * self.quantity

@dataclass(frozen=True)
class ExecutionModel:
    commission_per_order: float = 0.0
    slippage_bps: float = 0.0

    def __post_init__(self):
        self._validate_parameter(
            self.commission_per_order,
            "commission_per_order",
        )

        self._validate_parameter(
            self.slippage_bps,
            "slippage_bps",
        )

    @staticmethod
    def _validate_parameter(value: float, name: str):
        if isinstance(value, bool):
            raise TypeError(f"{name} must be a number")

        if not isinstance(value, Real):
            raise TypeError(f"{name} must be a number")

        if not isfinite(value):
            raise ValueError(f"{name} must be finite")

        if value < 0:
            raise ValueError(f"{name} must not be negative")

    def execute(self, order: Order, bar: Bar) -> Fill:
        if order.symbol != bar.symbol:
            raise ValueError(
                "order symbol must match the market bar symbol"
            )

        slippage_rate = self.slippage_bps / 10_000

        if order.side is OrderSide.BUY:
            execution_price = bar.close * (1 + slippage_rate)
        else:
            execution_price = bar.close * (1 - slippage_rate)

        if execution_price <= 0:
            raise ValueError(
                "slippage produced a non-positive execution price"
            )

        return Fill(
            symbol=order.symbol,
            quantity=order.quantity,
            side=order.side,
            price=execution_price,
            timestamp=bar.timestamp,
            commission=self.commission_per_order,
        )