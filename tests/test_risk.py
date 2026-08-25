from datetime import datetime

import pytest

from backtester.execution import Fill
from backtester.orders import OrderSide
from backtester.portfolio import Portfolio
from backtester.risk import (
    RiskLimits,
    RiskManager,
    RiskViolation,
)


def make_buy_fill(
    *,
    quantity,
    price=100.0,
    commission=0.0,
):
    return Fill(
        symbol="AAPL",
        quantity=quantity,
        side=OrderSide.BUY,
        price=price,
        timestamp=datetime(2025, 1, 2),
        commission=commission,
    )


def test_risk_manager_accepts_fill_within_limits():
    portfolio = Portfolio(
        initial_cash=10_000.0
    )

    manager = RiskManager(
        RiskLimits(
            maximum_position_percentage=50.0,
            maximum_order_percentage=50.0,
            minimum_cash_percentage=20.0,
        )
    )

    manager.validate_fill(
        fill=make_buy_fill(
            quantity=40,
        ),
        portfolio=portfolio,
        current_prices={},
    )


def test_risk_manager_rejects_oversized_position():
    portfolio = Portfolio(
        initial_cash=10_000.0
    )

    manager = RiskManager(
        RiskLimits(
            maximum_position_percentage=50.0,
        )
    )

    with pytest.raises(
        RiskViolation,
        match="position",
    ):
        manager.validate_fill(
            fill=make_buy_fill(
                quantity=60,
            ),
            portfolio=portfolio,
            current_prices={},
        )


def test_risk_manager_rejects_cash_reserve_breach():
    portfolio = Portfolio(
        initial_cash=10_000.0
    )

    manager = RiskManager(
        RiskLimits(
            minimum_cash_percentage=30.0,
        )
    )

    with pytest.raises(
        RiskViolation,
        match="cash",
    ):
        manager.validate_fill(
            fill=make_buy_fill(
                quantity=80,
            ),
            portfolio=portfolio,
            current_prices={},
        )


@pytest.mark.parametrize(
    "percentage",
    [
        -1.0,
        101.0,
    ],
)
def test_risk_limits_reject_invalid_percentage(
    percentage,
):
    with pytest.raises(ValueError):
        RiskLimits(
            maximum_position_percentage=(
                percentage
            )
        )

def test_risk_manager_uses_contract_multiplier():
    portfolio = Portfolio(
        initial_cash=1_000_000.0
    )

    manager = RiskManager(
        RiskLimits(
            maximum_position_percentage=50.0,
            maximum_order_percentage=100.0,
        )
    )

    futures_fill = Fill(
        symbol="GC=F",
        quantity=3,
        side=OrderSide.BUY,
        price=2_000.0,
        timestamp=datetime(2025, 1, 2),
        commission=0.0,
        contract_multiplier=100.0,
    )

    with pytest.raises(
        RiskViolation,
        match="position",
    ):
        manager.validate_fill(
            fill=futures_fill,
            portfolio=portfolio,
            current_prices={},
        )