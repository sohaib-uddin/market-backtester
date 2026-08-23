import pytest

from backtester.orders import Order, OrderSide


def test_buy_order_stores_valid_data():
    order = Order(
        symbol="AAPL",
        quantity=10,
        side=OrderSide.BUY,
    )

    assert order.symbol == "AAPL"
    assert order.quantity == 10
    assert order.side is OrderSide.BUY


def test_sell_order_stores_valid_data():
    order = Order(
        symbol="MSFT",
        quantity=5,
        side=OrderSide.SELL,
    )

    assert order.symbol == "MSFT"
    assert order.quantity == 5
    assert order.side is OrderSide.SELL


def test_order_normalises_symbol():
    order = Order(
        symbol="  aapl  ",
        quantity=10,
        side=OrderSide.BUY,
    )

    assert order.symbol == "AAPL"


@pytest.mark.parametrize("quantity", [0, -1, -100])
def test_order_rejects_non_positive_quantity(quantity):
    with pytest.raises(ValueError, match="quantity"):
        Order(
            symbol="AAPL",
            quantity=quantity,
            side=OrderSide.BUY,
        )


def test_order_rejects_empty_symbol():
    with pytest.raises(ValueError, match="symbol"):
        Order(
            symbol="",
            quantity=10,
            side=OrderSide.BUY,
        )