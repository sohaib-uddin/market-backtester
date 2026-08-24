from backtester.engine import BacktestEngine
from datetime import datetime

import pytest

from backtester.data import Bar, HistoricalDataFeed
from backtester.orders import Order, OrderSide
from backtester.strategy import Strategy
from backtester.execution import ExecutionModel
from backtester.risk import (
    RiskLimits,
    RiskManager,
)

def test_engine_initialises():
    engine = BacktestEngine()

    assert engine.current_time is None

class BuyOnceStrategy(Strategy):
    def __init__(self):
        self.observed_history_lengths = []

    def on_bar(self, context):
        symbol_history = context.history[
            context.bar.symbol
        ]

        self.observed_history_lengths.append(
            len(symbol_history)
        )

        if len(symbol_history) == 1:
            return [
                Order(
                    symbol=context.bar.symbol,
                    quantity=10,
                    side=OrderSide.BUY,
                )
            ]

        return []


def test_engine_executes_signal_on_next_bar_open():
    feed = HistoricalDataFeed(
        [
            Bar(
                symbol="AAPL",
                timestamp=datetime(2025, 1, 2),
                open=100.0,
                high=102.0,
                low=99.0,
                close=100.0,
                volume=1_000,
            ),
            Bar(
                symbol="AAPL",
                timestamp=datetime(2025, 1, 3),
                open=105.0,
                high=111.0,
                low=104.0,
                close=110.0,
                volume=1_200,
            ),
            Bar(
                symbol="AAPL",
                timestamp=datetime(2025, 1, 4),
                open=120.0,
                high=122.0,
                low=118.0,
                close=120.0,
                volume=1_100,
            ),
        ]
    )

    strategy = BuyOnceStrategy()
    engine = BacktestEngine(initial_cash=10_000.0)

    result = engine.run(
        feed=feed,
        strategy=strategy,
    )

    assert strategy.observed_history_lengths == [1, 2, 3]
    assert result.orders_submitted == 1
    assert result.fills == 1
    assert result.final_equity == pytest.approx(10_150.0)
    assert result.total_return == pytest.approx(0.015)
def test_order_from_final_bar_remains_unfilled():
    feed = HistoricalDataFeed(
        [
            Bar(
                symbol="AAPL",
                timestamp=datetime(2025, 1, 2),
                open=100.0,
                high=102.0,
                low=99.0,
                close=100.0,
                volume=1_000,
            )
        ]
    )

    result = BacktestEngine(
        initial_cash=10_000.0
    ).run(
        feed=feed,
        strategy=BuyOnceStrategy(),
    )

    assert result.orders_submitted == 1
    assert result.fills == 0
    assert result.unfilled_orders == 1
    assert result.final_equity == 10_000.0


def test_engine_handles_empty_data_feed():
    result = BacktestEngine(
        initial_cash=10_000.0
    ).run(
        feed=HistoricalDataFeed([]),
        strategy=BuyOnceStrategy(),
    )

    assert result.final_equity == 10_000.0
    assert result.total_return == 0.0
    assert result.orders_submitted == 0
    assert result.fills == 0
    assert result.unfilled_orders == 0
    assert result.equity_curve == ()


def test_engine_applies_commission_and_slippage():
    feed = HistoricalDataFeed(
        [
            Bar(
                symbol="AAPL",
                timestamp=datetime(2025, 1, 2),
                open=100.0,
                high=101.0,
                low=99.0,
                close=100.0,
                volume=1_000,
            ),
            Bar(
                symbol="AAPL",
                timestamp=datetime(2025, 1, 3),
                open=100.0,
                high=101.0,
                low=99.0,
                close=100.0,
                volume=1_000,
            ),
        ]
    )

    engine = BacktestEngine(
        initial_cash=10_000.0,
        execution_model=ExecutionModel(
            commission_per_order=1.0,
            slippage_bps=100.0,
        ),
    )

    result = engine.run(
        feed=feed,
        strategy=BuyOnceStrategy(),
    )

    assert result.fills == 1
    assert result.fill_history[0].price == pytest.approx(
        101.0
    )
    assert result.final_equity == pytest.approx(
        9_989.0
    )
    assert result.total_return == pytest.approx(
        -0.0011
    )
def test_empty_run_clears_previous_engine_time():
    engine = BacktestEngine(
        initial_cash=10_000.0
    )

    populated_feed = HistoricalDataFeed(
        [
            Bar(
                symbol="AAPL",
                timestamp=datetime(2025, 1, 2),
                open=100.0,
                high=102.0,
                low=99.0,
                close=100.0,
                volume=1_000,
            )
        ]
    )

    engine.run(
        feed=populated_feed,
        strategy=BuyOnceStrategy(),
    )

    assert engine.current_time == datetime(
        2025,
        1,
        2,
    )

    engine.run(
        feed=HistoricalDataFeed([]),
        strategy=BuyOnceStrategy(),
    )

    assert engine.current_time is None

def test_engine_records_risk_rejected_fill():
    feed = HistoricalDataFeed(
        [
            Bar(
                symbol="AAPL",
                timestamp=datetime(2025, 1, 2),
                open=100.0,
                high=101.0,
                low=99.0,
                close=100.0,
                volume=1_000,
            ),
            Bar(
                symbol="AAPL",
                timestamp=datetime(2025, 1, 3),
                open=100.0,
                high=101.0,
                low=99.0,
                close=100.0,
                volume=1_000,
            ),
        ]
    )

    engine = BacktestEngine(
        initial_cash=10_000.0,
        risk_manager=RiskManager(
            RiskLimits(
                maximum_position_percentage=5.0,
            )
        ),
    )

    result = engine.run(
        feed=feed,
        strategy=BuyOnceStrategy(),
    )

    assert result.orders_submitted == 1
    assert result.fills == 0
    assert result.rejected_orders == 1

    rejection = result.rejection_history[0]

    assert rejection.order.symbol == "AAPL"
    assert rejection.attempted_fill.price == 100.0
    assert "position" in rejection.reason
    assert result.final_equity == 10_000.0