from datetime import datetime

import pytest

from backtester.data import Bar, HistoricalDataFeed
from backtester.engine import BacktestEngine
from backtester.orders import OrderSide
from backtester.strategies import (
    BuyAndHoldStrategy,
    MovingAverageCrossoverStrategy,
    create_default_strategy_registry,
)


def make_bar(day, close):
    return Bar(
        symbol="AAPL",
        timestamp=datetime(2025, 1, day),
        open=close,
        high=close + 1,
        low=close - 1,
        close=close,
        volume=1_000,
    )


def test_moving_average_strategy_exposes_parameters():
    parameters = (
        MovingAverageCrossoverStrategy
        .parameter_schema
        .parameters
    )

    assert [
        parameter.key
        for parameter in parameters
    ] == [
        "short_window",
        "long_window",
        "trade_quantity",
    ]


def test_moving_average_strategy_rejects_invalid_windows():
    with pytest.raises(
        ValueError,
        match="short_window",
    ):
        MovingAverageCrossoverStrategy(
            short_window=10,
            long_window=5,
            trade_quantity=10,
        )


def test_moving_average_strategy_buys_and_exits():
    feed = HistoricalDataFeed(
        [
            make_bar(2, 10.0),
            make_bar(3, 10.0),
            make_bar(4, 12.0),
            make_bar(5, 14.0),
            make_bar(6, 8.0),
            make_bar(7, 6.0),
        ]
    )

    strategy = MovingAverageCrossoverStrategy(
        short_window=2,
        long_window=3,
        trade_quantity=5,
    )

    result = BacktestEngine(
        initial_cash=10_000.0
    ).run(
        feed=feed,
        strategy=strategy,
    )

    assert result.orders_submitted == 2
    assert result.fills == 2

    assert [
        fill.side
        for fill in result.fill_history
    ] == [
        OrderSide.BUY,
        OrderSide.SELL,
    ]

    assert result.final_equity == pytest.approx(
        9_960.0
    )

def test_buy_and_hold_buys_once():
    feed = HistoricalDataFeed(
        [
            make_bar(2, 100.0),
            make_bar(3, 105.0),
            make_bar(4, 110.0),
        ]
    )

    strategy = BuyAndHoldStrategy(
        trade_quantity=5,
    )

    result = BacktestEngine(
        initial_cash=10_000.0
    ).run(
        feed=feed,
        strategy=strategy,
    )

    assert result.orders_submitted == 1
    assert result.fills == 1
    assert result.fill_history[0].side is (
        OrderSide.BUY
    )
    assert result.final_equity == pytest.approx(
        10_025.0
    )


def test_default_registry_contains_builtin_strategies():
    registry = create_default_strategy_registry()

    assert [
        definition.key
        for definition in registry.definitions
    ] == [
        "buy_and_hold",
        "moving_average_crossover",
    ]