from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime
from types import MappingProxyType

from backtester.data import HistoricalDataFeed
from backtester.execution import ExecutionModel, Fill
from backtester.orders import Order
from backtester.portfolio import Portfolio
from backtester.strategy import (
    PositionView,
    Strategy,
    StrategyContext,
)
from backtester.risk import (
    RiskManager,
    RiskViolation,
)
from collections.abc import Mapping
from math import isfinite
from numbers import Real


@dataclass(frozen=True)
class EquityPoint:
    timestamp: datetime
    equity: float

@dataclass(frozen=True)
class RejectedOrder:
    order: Order
    attempted_fill: Fill
    timestamp: datetime
    reason: str


@dataclass(frozen=True)
class BacktestResult:
    initial_cash: float
    final_equity: float
    total_return: float
    orders_submitted: int
    fills: int
    unfilled_orders: int
    equity_curve: tuple[EquityPoint, ...]
    fill_history: tuple[Fill, ...]
    rejected_orders: int = 0
    rejection_history: tuple[
        RejectedOrder,
        ...,
    ] = ()


class BacktestEngine:
    def __init__(
        self,
        *,
        initial_cash: float = 100_000.0,
        execution_model: ExecutionModel | None = None,
        contract_multipliers: Mapping[
            str,
            float,
        ] | None = None,
        risk_manager: RiskManager | None = None,
    ):
        self.initial_cash = initial_cash

        self.execution_model = (
            execution_model
            if execution_model is not None
            else ExecutionModel()
        )

        supplied_multipliers = (
            contract_multipliers
            if contract_multipliers is not None
            else {}
        )

        self.contract_multipliers = {}

        for symbol, multiplier in (
            supplied_multipliers.items()
        ):
            if (
                isinstance(multiplier, bool)
                or not isinstance(
                    multiplier,
                    Real,
                )
            ):
                raise TypeError(
                    "contract multiplier must be "
                    "a number"
                )

            if (
                not isfinite(multiplier)
                or multiplier <= 0
            ):
                raise ValueError(
                    "contract multiplier must be "
                    "positive and finite"
                )

            normalised_symbol = (
                symbol.strip().upper()
            )

            if not normalised_symbol:
                raise ValueError(
                    "contract multiplier symbol "
                    "must not be empty"
                )

            self.contract_multipliers[
                normalised_symbol
            ] = float(multiplier)

        self.risk_manager = (
            risk_manager
            if risk_manager is not None
            else RiskManager()
        )

        if not isinstance(
            self.risk_manager,
            RiskManager,
        ):
            raise TypeError(
                "risk_manager must be a "
                "RiskManager"
            )

        self.current_time: datetime | None = None


    def run(
        self,
        *,
        feed: HistoricalDataFeed,
        strategy: Strategy,
    ) -> BacktestResult:
        self.current_time = None

        portfolio = Portfolio(
            initial_cash=self.initial_cash
        )

        history = defaultdict(list)
        latest_prices: dict[str, float] = {}
        pending_orders = defaultdict(list)

        equity_curve: list[EquityPoint] = []
        fill_history: list[Fill] = []
        rejection_history: list[
            RejectedOrder
        ] = []
        orders_submitted = 0

        for bar in feed:
            self.current_time = bar.timestamp

            orders_to_fill = pending_orders.pop(
                bar.symbol,
                [],
            )

            for order in orders_to_fill:
                fill = self.execution_model.execute(
                    order,
                    bar,
                    reference_price=bar.open,
                    contract_multiplier=(
                        self.contract_multipliers
                        .get(order.symbol, 1.0)
                    ),
                )

                valuation_prices = dict(
                    latest_prices
                )

                valuation_prices[bar.symbol] = (
                    bar.open
                )

                try:
                    self.risk_manager.validate_fill(
                        fill=fill,
                        portfolio=portfolio,
                        current_prices=(
                            valuation_prices
                        ),
                    )

                    portfolio.apply_fill(fill)

                except RiskViolation as error:
                    rejection_history.append(
                        RejectedOrder(
                            order=order,
                            attempted_fill=fill,
                            timestamp=bar.timestamp,
                            reason=str(error),
                        )
                    )

                    continue

                fill_history.append(fill)

            latest_prices[bar.symbol] = bar.close
            history[bar.symbol].append(bar)

            history_view = MappingProxyType(
                {
                    symbol: tuple(symbol_bars)
                    for symbol, symbol_bars
                    in history.items()
                }
            )

            position_view = MappingProxyType(
                {
                    symbol: PositionView(
                        symbol=position.symbol,
                        quantity=position.quantity,
                        average_entry_price=(
                            position.average_entry_price
                        ),
                    )
                    for symbol, position
                    in portfolio.positions.items()
                }
            )

            current_equity = portfolio.equity(
                latest_prices
            )

            context = StrategyContext(
                bar=bar,
                history=history_view,
                cash=portfolio.cash,
                equity=current_equity,
                positions=position_view,
            )

            new_orders = strategy.on_bar(context)

            if not isinstance(new_orders, list):
                raise TypeError(
                    "strategy.on_bar must return a list"
                )

            for order in new_orders:
                if not isinstance(order, Order):
                    raise TypeError(
                        "strategy must return Order objects"
                    )

                if order.symbol != bar.symbol:
                    raise ValueError(
                        "strategy orders must match "
                        "the current bar symbol"
                    )

                pending_orders[order.symbol].append(
                    order
                )
                orders_submitted += 1

            equity_curve.append(
                EquityPoint(
                    timestamp=bar.timestamp,
                    equity=current_equity,
                )
            )

        if latest_prices:
            final_equity = portfolio.equity(
                latest_prices
            )
        else:
            final_equity = portfolio.cash

        unfilled_orders = sum(
            len(orders)
            for orders in pending_orders.values()
        )

        return BacktestResult(
            initial_cash=portfolio.initial_cash,
            final_equity=final_equity,
            total_return=(
                final_equity / portfolio.initial_cash
            ) - 1,
            orders_submitted=orders_submitted,
            fills=len(fill_history),
            unfilled_orders=unfilled_orders,
            equity_curve=tuple(equity_curve),
            fill_history=tuple(fill_history),
            rejected_orders=len(
                rejection_history
            ),
            rejection_history=tuple(
                rejection_history
            ),
        )