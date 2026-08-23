from dataclasses import dataclass
from math import isfinite
from numbers import Real

from backtester.execution import Fill
from backtester.orders import OrderSide


@dataclass
class Position:
    symbol: str
    quantity: int = 0
    average_entry_price: float = 0.0


class Portfolio:
    def __init__(self, initial_cash: float):
        if isinstance(initial_cash, bool):
            raise TypeError("initial_cash must be a number")

        if not isinstance(initial_cash, Real):
            raise TypeError("initial_cash must be a number")

        if not isfinite(initial_cash) or initial_cash <= 0:
            raise ValueError(
                "initial_cash must be positive and finite"
            )

        self.initial_cash = float(initial_cash)
        self.cash = float(initial_cash)
        self.positions: dict[str, Position] = {}
        self.realised_pnl = 0.0

    def apply_fill(self, fill: Fill):
        if fill.side is OrderSide.BUY:
            self._apply_buy(fill)
        else:
            self._apply_sell(fill)

    def _apply_buy(self, fill: Fill):
        total_cost = fill.gross_value + fill.commission

        if total_cost > self.cash:
            raise ValueError(
                "insufficient cash to execute buy fill"
            )

        existing_position = self.positions.get(fill.symbol)

        if existing_position is None:
            existing_quantity = 0
            existing_cost = 0.0
        else:
            existing_quantity = existing_position.quantity
            existing_cost = (
                existing_position.average_entry_price
                * existing_position.quantity
            )

        new_quantity = existing_quantity + fill.quantity
        new_total_cost = (
            existing_cost
            + fill.gross_value
            + fill.commission
        )

        self.positions[fill.symbol] = Position(
            symbol=fill.symbol,
            quantity=new_quantity,
            average_entry_price=(
                new_total_cost / new_quantity
            ),
        )

        self.cash -= total_cost

    def _apply_sell(self, fill: Fill):
        existing_position = self.positions.get(fill.symbol)

        if (
            existing_position is None
            or existing_position.quantity < fill.quantity
        ):
            raise ValueError(
                "insufficient position to execute sell fill"
            )

        sale_proceeds = (
            fill.gross_value
            - fill.commission
        )

        sold_cost_basis = (
            existing_position.average_entry_price
            * fill.quantity
        )

        realised_profit = (
            sale_proceeds
            - sold_cost_basis
        )

        remaining_quantity = (
            existing_position.quantity
            - fill.quantity
        )

        self.cash += sale_proceeds
        self.realised_pnl += realised_profit

        if remaining_quantity == 0:
            del self.positions[fill.symbol]
        else:
            self.positions[fill.symbol] = Position(
                symbol=fill.symbol,
                quantity=remaining_quantity,
                average_entry_price=(
                    existing_position.average_entry_price
                ),
            )
            
    def market_value(
        self,
        current_prices: dict[str, float],
    ) -> float:
        total_value = 0.0

        for symbol, position in self.positions.items():
            price = self._get_current_price(
                symbol,
                current_prices,
            )

            total_value += position.quantity * price

        return total_value

    def unrealised_pnl(
        self,
        current_prices: dict[str, float],
    ) -> float:
        total_unrealised_pnl = 0.0

        for symbol, position in self.positions.items():
            price = self._get_current_price(
                symbol,
                current_prices,
            )

            total_unrealised_pnl += (
                price - position.average_entry_price
            ) * position.quantity

        return total_unrealised_pnl

    def equity(
        self,
        current_prices: dict[str, float],
    ) -> float:
        return (
            self.cash
            + self.market_value(current_prices)
        )

    def total_pnl(
        self,
        current_prices: dict[str, float],
    ) -> float:
        return (
            self.equity(current_prices)
            - self.initial_cash
        )

    @staticmethod
    def _get_current_price(
        symbol: str,
        current_prices: dict[str, float],
    ) -> float:
        if symbol not in current_prices:
            raise ValueError(
                f"missing current price for {symbol}"
            )

        price = current_prices[symbol]

        if isinstance(price, bool):
            raise TypeError(
                f"current price for {symbol} must be a number"
            )

        if not isinstance(price, Real):
            raise TypeError(
                f"current price for {symbol} must be a number"
            )

        if not isfinite(price) or price <= 0:
            raise ValueError(
                f"current price for {symbol} "
                "must be positive and finite"
            )

        return float(price)