from datetime import datetime

import pytest

from backtester.execution import Fill
from backtester.orders import OrderSide
from backtester.portfolio import Portfolio


def make_fill(
    *,
    quantity,
    price,
    side=OrderSide.BUY,
    commission=0.0,
    contract_multiplier=1.0,
):
    return Fill(
        symbol="AAPL",
        quantity=quantity,
        side=side,
        price=price,
        timestamp=datetime(2025, 1, 2, 9, 31),
        commission=commission,
        contract_multiplier=(
            contract_multiplier
        ),
    )


def test_portfolio_starts_with_cash_and_no_positions():
    portfolio = Portfolio(initial_cash=10_000.0)

    assert portfolio.initial_cash == 10_000.0
    assert portfolio.cash == 10_000.0
    assert portfolio.positions == {}
    assert portfolio.realised_pnl == 0.0


def test_portfolio_rejects_non_positive_initial_cash():
    with pytest.raises(ValueError, match="initial_cash"):
        Portfolio(initial_cash=0.0)


def test_buy_fill_updates_cash_and_position():
    portfolio = Portfolio(initial_cash=10_000.0)

    portfolio.apply_fill(
        make_fill(
            quantity=10,
            price=100.0,
            commission=1.0,
        )
    )

    position = portfolio.positions["AAPL"]

    assert portfolio.cash == pytest.approx(8_999.0)
    assert position.quantity == 10
    assert position.average_entry_price == pytest.approx(100.10)


def test_multiple_buys_calculate_weighted_average_entry_price():
    portfolio = Portfolio(initial_cash=10_000.0)

    portfolio.apply_fill(
        make_fill(
            quantity=10,
            price=100.0,
        )
    )

    portfolio.apply_fill(
        make_fill(
            quantity=10,
            price=110.0,
        )
    )

    position = portfolio.positions["AAPL"]

    assert position.quantity == 20
    assert position.average_entry_price == pytest.approx(105.0)
    assert portfolio.cash == pytest.approx(7_900.0)

def test_partial_sell_updates_cash_position_and_realised_pnl():
    portfolio = Portfolio(initial_cash=10_000.0)

    portfolio.apply_fill(
        make_fill(
            quantity=10,
            price=100.0,
            commission=1.0,
        )
    )

    portfolio.apply_fill(
        make_fill(
            quantity=4,
            price=110.0,
            side=OrderSide.SELL,
            commission=1.0,
        )
    )

    position = portfolio.positions["AAPL"]

    assert portfolio.cash == pytest.approx(9_438.0)
    assert position.quantity == 6
    assert position.average_entry_price == pytest.approx(100.10)
    assert portfolio.realised_pnl == pytest.approx(38.60)


def test_closing_position_removes_it_from_portfolio():
    portfolio = Portfolio(initial_cash=10_000.0)

    portfolio.apply_fill(
        make_fill(
            quantity=10,
            price=100.0,
            commission=1.0,
        )
    )

    portfolio.apply_fill(
        make_fill(
            quantity=10,
            price=110.0,
            side=OrderSide.SELL,
            commission=1.0,
        )
    )

    assert "AAPL" not in portfolio.positions
    assert portfolio.cash == pytest.approx(10_098.0)
    assert portfolio.realised_pnl == pytest.approx(98.0)


def test_portfolio_rejects_selling_more_than_owned():
    portfolio = Portfolio(initial_cash=10_000.0)

    portfolio.apply_fill(
        make_fill(
            quantity=5,
            price=100.0,
        )
    )

    cash_before_sell = portfolio.cash
    position_before_sell = portfolio.positions["AAPL"]

    with pytest.raises(ValueError, match="insufficient position"):
        portfolio.apply_fill(
            make_fill(
                quantity=6,
                price=110.0,
                side=OrderSide.SELL,
            )
        )

    assert portfolio.cash == cash_before_sell
    assert portfolio.positions["AAPL"] == position_before_sell


def test_portfolio_rejects_selling_unowned_symbol():
    portfolio = Portfolio(initial_cash=10_000.0)

    with pytest.raises(ValueError, match="insufficient position"):
        portfolio.apply_fill(
            make_fill(
                quantity=1,
                price=110.0,
                side=OrderSide.SELL,
            )
        )

def test_portfolio_calculates_value_equity_and_unrealised_pnl():
    portfolio = Portfolio(initial_cash=10_000.0)

    portfolio.apply_fill(
        make_fill(
            quantity=10,
            price=100.0,
            commission=1.0,
        )
    )

    current_prices = {
        "AAPL": 110.0,
    }

    assert portfolio.market_value(
        current_prices
    ) == pytest.approx(1_100.0)

    assert portfolio.unrealised_pnl(
        current_prices
    ) == pytest.approx(99.0)

    assert portfolio.equity(
        current_prices
    ) == pytest.approx(10_099.0)

    assert portfolio.total_pnl(
        current_prices
    ) == pytest.approx(99.0)


def test_portfolio_valuation_requires_every_position_price():
    portfolio = Portfolio(initial_cash=10_000.0)

    portfolio.apply_fill(
        make_fill(
            quantity=10,
            price=100.0,
        )
    )

    with pytest.raises(ValueError, match="AAPL"):
        portfolio.equity({})

def test_rejected_buy_does_not_change_portfolio():
    portfolio = Portfolio(initial_cash=500.0)

    with pytest.raises(ValueError, match="insufficient cash"):
        portfolio.apply_fill(
            make_fill(
                quantity=10,
                price=100.0,
                commission=1.0,
            )
        )

    assert portfolio.cash == 500.0
    assert portfolio.positions == {}
    assert portfolio.realised_pnl == 0.0

def test_futures_position_uses_contract_multiplier():
    portfolio = Portfolio(
        initial_cash=1_000_000.0
    )

    portfolio.apply_fill(
        make_fill(
            quantity=1,
            price=2_000.0,
            commission=10.0,
            contract_multiplier=100.0,
        )
    )

    position = portfolio.positions["AAPL"]

    assert position.quantity == 1

    assert position.contract_multiplier == (
        100.0
    )

    assert position.average_entry_price == (
        pytest.approx(2_000.10)
    )

    assert portfolio.cash == pytest.approx(
        799_990.0
    )

    assert portfolio.market_value(
        {
            "AAPL": 2_010.0,
        }
    ) == pytest.approx(201_000.0)

    assert portfolio.unrealised_pnl(
        {
            "AAPL": 2_010.0,
        }
    ) == pytest.approx(990.0)

    portfolio.apply_fill(
        make_fill(
            quantity=1,
            price=2_010.0,
            side=OrderSide.SELL,
            commission=10.0,
            contract_multiplier=100.0,
        )
    )

    assert portfolio.cash == pytest.approx(
        1_000_980.0
    )

    assert portfolio.realised_pnl == (
        pytest.approx(980.0)
    )

    assert portfolio.positions == {}