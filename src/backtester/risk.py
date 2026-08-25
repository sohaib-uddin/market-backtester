from dataclasses import dataclass
from math import isfinite
from numbers import Real

from backtester.execution import Fill
from backtester.orders import OrderSide
from backtester.portfolio import Portfolio


class RiskViolation(ValueError):
    pass


@dataclass(frozen=True)
class RiskLimits:
    maximum_position_percentage: float = 100.0
    maximum_order_percentage: float = 100.0
    minimum_cash_percentage: float = 0.0

    def __post_init__(self):
        self._validate_percentage(
            self.maximum_position_percentage,
            "maximum_position_percentage",
        )

        self._validate_percentage(
            self.maximum_order_percentage,
            "maximum_order_percentage",
        )

        self._validate_percentage(
            self.minimum_cash_percentage,
            "minimum_cash_percentage",
        )

    @staticmethod
    def _validate_percentage(
        value: float,
        name: str,
    ):
        if (
            isinstance(value, bool)
            or not isinstance(value, Real)
        ):
            raise TypeError(
                f"{name} must be a number"
            )

        if (
            not isfinite(value)
            or value < 0
            or value > 100
        ):
            raise ValueError(
                f"{name} must be between "
                "0 and 100"
            )


class RiskManager:
    def __init__(
        self,
        limits: RiskLimits | None = None,
    ):
        self.limits = (
            limits
            if limits is not None
            else RiskLimits()
        )

        if not isinstance(
            self.limits,
            RiskLimits,
        ):
            raise TypeError(
                "limits must be RiskLimits"
            )

    def validate_fill(
        self,
        *,
        fill: Fill,
        portfolio: Portfolio,
        current_prices: dict[str, float],
    ):
        if not isinstance(fill, Fill):
            raise TypeError(
                "fill must be a Fill"
            )

        if not isinstance(
            portfolio,
            Portfolio,
        ):
            raise TypeError(
                "portfolio must be a Portfolio"
            )

        if fill.side is OrderSide.SELL:
            return

        valuation_prices = {
            symbol.strip().upper(): price
            for symbol, price
            in current_prices.items()
        }

        valuation_prices[fill.symbol] = (
            fill.price
        )

        equity = portfolio.equity(
            valuation_prices
        )

        order_cost = (
            fill.gross_value
            + fill.commission
        )

        maximum_order_value = (
            equity
            * self.limits
            .maximum_order_percentage
            / 100
        )

        if order_cost > maximum_order_value:
            raise RiskViolation(
                "order value exceeds the maximum "
                "order percentage"
            )

        existing_position = (
            portfolio.positions.get(
                fill.symbol
            )
        )

        existing_quantity = (
            existing_position.quantity
            if existing_position is not None
            else 0
        )

        existing_position_value = (
            existing_quantity
            * fill.price
            * (
                existing_position
                .contract_multiplier
                if existing_position is not None
                else 1.0
            )
        )

        new_fill_value = (
            fill.quantity
            * fill.price
            * fill.contract_multiplier
        )

        projected_position_value = (
            existing_position_value
            + new_fill_value
        )

        maximum_position_value = (
            equity
            * self.limits
            .maximum_position_percentage
            / 100
        )

        if (
            projected_position_value
            > maximum_position_value
        ):
            raise RiskViolation(
                "position value exceeds the "
                "maximum position percentage"
            )

        remaining_cash = (
            portfolio.cash
            - order_cost
        )

        required_cash = (
            equity
            * self.limits
            .minimum_cash_percentage
            / 100
        )

        if remaining_cash < required_cash:
            raise RiskViolation(
                "cash remaining after the fill "
                "would breach the minimum cash "
                "percentage"
            )