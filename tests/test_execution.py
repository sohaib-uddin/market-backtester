from datetime import datetime
from backtester.data import Bar

import pytest

from backtester.execution import ExecutionModel, Fill
from backtester.orders import Order, OrderSide


def test_fill_stores_execution_details():
    timestamp = datetime(2025, 1, 2, 9, 31)

    fill = Fill(
        symbol="AAPL",
        quantity=10,
        side=OrderSide.BUY,
        price=100.50,
        timestamp=timestamp,
        commission=1.25,
    )

    assert fill.symbol == "AAPL"
    assert fill.quantity == 10
    assert fill.side is OrderSide.BUY
    assert fill.price == 100.50
    assert fill.timestamp == timestamp
    assert fill.commission == 1.25


def test_fill_calculates_gross_value():
    fill = Fill(
        symbol="AAPL",
        quantity=10,
        side=OrderSide.BUY,
        price=100.50,
        timestamp=datetime(2025, 1, 2, 9, 31),
        commission=1.25,
    )

    assert fill.gross_value == 1_005.00


@pytest.mark.parametrize("price", [0.0, -1.0])
def test_fill_rejects_non_positive_price(price):
    with pytest.raises(ValueError, match="price"):
        Fill(
            symbol="AAPL",
            quantity=10,
            side=OrderSide.BUY,
            price=price,
            timestamp=datetime(2025, 1, 2, 9, 31),
        )


def test_fill_rejects_negative_commission():
    with pytest.raises(ValueError, match="commission"):
        Fill(
            symbol="AAPL",
            quantity=10,
            side=OrderSide.BUY,
            price=100.0,
            timestamp=datetime(2025, 1, 2, 9, 31),
            commission=-1.0,
        )

def test_execution_model_applies_buy_slippage_and_commission():
    model = ExecutionModel(
        commission_per_order=1.50,
        slippage_bps=10.0,
    )

    bar = Bar(
        symbol="AAPL",
        timestamp=datetime(2025, 1, 2, 9, 31),
        open=99.0,
        high=101.0,
        low=98.0,
        close=100.0,
        volume=10_000,
    )

    order = Order(
        symbol="AAPL",
        quantity=10,
        side=OrderSide.BUY,
    )

    fill = model.execute(order, bar)

    assert fill.price == pytest.approx(100.10)
    assert fill.commission == 1.50
    assert fill.timestamp == bar.timestamp


def test_execution_model_applies_sell_slippage():
    model = ExecutionModel(
        commission_per_order=0.0,
        slippage_bps=10.0,
    )

    bar = Bar(
        symbol="AAPL",
        timestamp=datetime(2025, 1, 2, 9, 31),
        open=99.0,
        high=101.0,
        low=98.0,
        close=100.0,
        volume=10_000,
    )

    order = Order(
        symbol="AAPL",
        quantity=10,
        side=OrderSide.SELL,
    )

    fill = model.execute(order, bar)

    assert fill.price == pytest.approx(99.90)


@pytest.mark.parametrize(
    "commission, slippage",
    [
        (-1.0, 0.0),
        (0.0, -1.0),
    ],
)
def test_execution_model_rejects_negative_parameters(
    commission,
    slippage,
):
    with pytest.raises(ValueError):
        ExecutionModel(
            commission_per_order=commission,
            slippage_bps=slippage,
        )

def test_execution_rejects_order_for_different_symbol():
    model = ExecutionModel()

    bar = Bar(
        symbol="MSFT",
        timestamp=datetime(2025, 1, 2, 9, 31),
        open=420.0,
        high=425.0,
        low=418.0,
        close=423.0,
        volume=10_000,
    )

    order = Order(
        symbol="AAPL",
        quantity=10,
        side=OrderSide.BUY,
    )

    with pytest.raises(ValueError, match="symbol"):
        model.execute(order, bar)

def test_execution_model_accepts_explicit_reference_price():
    model = ExecutionModel(
        commission_per_order=1.0,
        slippage_bps=10.0,
    )

    bar = Bar(
        symbol="AAPL",
        timestamp=datetime(2025, 1, 3, 9, 31),
        open=105.0,
        high=111.0,
        low=104.0,
        close=110.0,
        volume=10_000,
    )

    order = Order(
        symbol="AAPL",
        quantity=10,
        side=OrderSide.BUY,
    )

    fill = model.execute(
        order,
        bar,
        reference_price=bar.open,
    )

    assert fill.price == pytest.approx(105.105)

def test_fill_applies_contract_multiplier():
    fill = Fill(
        symbol="GC=F",
        quantity=2,
        side=OrderSide.BUY,
        price=2_000.0,
        timestamp=datetime(2025, 1, 2),
        commission=5.0,
        contract_multiplier=100.0,
    )

    assert fill.contract_multiplier == 100.0

    assert fill.gross_value == pytest.approx(
        400_000.0
    )