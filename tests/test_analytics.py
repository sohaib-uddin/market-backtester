from datetime import datetime

import pytest


from backtester.engine import (
    BacktestResult,
    EquityPoint,
)
from backtester.analytics import (
    BacktestAnalyser,
    PerformanceAnalyzer,
    TradeAnalyzer,
)
from backtester.execution import Fill
from backtester.orders import OrderSide


def make_result(equities):
    points = tuple(
        EquityPoint(
            timestamp=datetime(
                2025,
                1,
                index + 2,
            ),
            equity=equity,
        )
        for index, equity in enumerate(
            equities
        )
    )

    initial_cash = equities[0]
    final_equity = equities[-1]

    return BacktestResult(
        initial_cash=initial_cash,
        final_equity=final_equity,
        total_return=(
            final_equity / initial_cash
        ) - 1,
        orders_submitted=0,
        fills=0,
        unfilled_orders=0,
        equity_curve=points,
        fill_history=(),
    )


def test_analyzer_calculates_returns_and_drawdown():
    result = make_result(
        [
            100.0,
            110.0,
            88.0,
            99.0,
        ]
    )

    report = PerformanceAnalyzer(
        periods_per_year=252,
    ).analyze(result)

    assert report.total_return == pytest.approx(
        -0.01
    )

    assert report.period_returns == pytest.approx(
        (
            0.10,
            -0.20,
            0.125,
        )
    )

    assert report.maximum_drawdown == pytest.approx(
        0.20
    )

    assert report.maximum_drawdown_peak == datetime(
        2025,
        1,
        3,
    )

    assert report.maximum_drawdown_trough == datetime(
        2025,
        1,
        4,
    )


def test_analyzer_handles_flat_equity_curve():
    result = make_result(
        [
            100.0,
            100.0,
            100.0,
        ]
    )

    report = PerformanceAnalyzer().analyze(
        result
    )

    assert report.annualised_volatility == 0.0
    assert report.sharpe_ratio is None
    assert report.maximum_drawdown == 0.0
    assert report.downside_deviation == 0.0
    assert report.sortino_ratio is None
    assert report.calmar_ratio is None


def test_analyzer_rejects_invalid_periods_per_year():
    with pytest.raises(
        ValueError,
        match="periods_per_year",
    ):
        PerformanceAnalyzer(
            periods_per_year=0,
        )

def make_fill(
    *,
    side,
    quantity,
    price,
    commission,
    day,
):
    return Fill(
        symbol="AAPL",
        quantity=quantity,
        side=side,
        price=price,
        commission=commission,
        timestamp=datetime(
            2025,
            1,
            day,
        ),
    )


def test_trade_analyzer_calculates_closed_trade_stats():
    fills = (
        make_fill(
            side=OrderSide.BUY,
            quantity=10,
            price=100.0,
            commission=10.0,
            day=2,
        ),
        make_fill(
            side=OrderSide.SELL,
            quantity=5,
            price=110.0,
            commission=5.0,
            day=3,
        ),
        make_fill(
            side=OrderSide.SELL,
            quantity=5,
            price=90.0,
            commission=5.0,
            day=4,
        ),
    )

    report = TradeAnalyzer().analyze(fills)

    assert report.total_fills == 3
    assert report.closed_trades == 2
    assert report.winning_trades == 1
    assert report.losing_trades == 1
    assert report.win_rate == pytest.approx(0.5)
    assert report.gross_profit == pytest.approx(40.0)
    assert report.gross_loss == pytest.approx(60.0)
    assert report.net_profit == pytest.approx(-20.0)
    assert report.profit_factor == pytest.approx(
        40 / 60
    )
    assert report.total_commission == pytest.approx(
        20.0
    )


def test_trade_analyzer_handles_no_closed_trades():
    fills = (
        make_fill(
            side=OrderSide.BUY,
            quantity=10,
            price=100.0,
            commission=1.0,
            day=2,
        ),
    )

    report = TradeAnalyzer().analyze(fills)

    assert report.closed_trades == 0
    assert report.win_rate is None
    assert report.profit_factor is None
    assert report.net_profit == 0.0

def test_performance_report_includes_downside_risk():
    result = make_result(
        [
            100.0,
            110.0,
            104.5,
        ]
    )

    report = PerformanceAnalyzer(
        periods_per_year=1,
        risk_free_rate=0.0,
    ).analyze(result)

    expected_downside_deviation = (
        (
            0.0 ** 2
            + (-0.05) ** 2
        ) / 2
    ) ** 0.5

    expected_mean_return = (
        0.10 - 0.05
    ) / 2

    assert report.downside_deviation == (
        pytest.approx(
            expected_downside_deviation
        )
    )

    assert report.sortino_ratio == pytest.approx(
        expected_mean_return
        / expected_downside_deviation
    )

    assert report.calmar_ratio == pytest.approx(
        report.annualised_return
        / report.maximum_drawdown
    )

def test_backtest_analyser_combines_reports():
    result = make_result(
        [
            100.0,
            110.0,
            99.0,
        ]
    )

    analysis = BacktestAnalyser(
        periods_per_year=252,
        risk_free_rate=0.02,
    ).analyse(result)

    assert analysis.performance.total_return == (
        pytest.approx(-0.01)
    )

    assert analysis.performance.maximum_drawdown == (
        pytest.approx(0.10)
    )

    assert analysis.trades.total_fills == 0
    assert analysis.trades.closed_trades == 0

def test_backtest_analyser_compares_with_benchmark():
    strategy_result = make_result(
        [
            100.0,
            105.0,
            110.0,
        ]
    )

    benchmark_result = make_result(
        [
            100.0,
            102.0,
            105.0,
        ]
    )

    comparison = BacktestAnalyser().compare(
        strategy_result=strategy_result,
        benchmark_result=benchmark_result,
    )

    assert comparison.strategy_return == (
        pytest.approx(0.10)
    )

    assert comparison.benchmark_return == (
        pytest.approx(0.05)
    )

    assert comparison.excess_return == (
        pytest.approx(0.05)
    )

    assert comparison.relative_return == (
        pytest.approx(
            (1.10 / 1.05) - 1
        )
    )