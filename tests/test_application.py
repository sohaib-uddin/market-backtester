from datetime import datetime

import pytest

from backtester.application import (
    BacktestApplication,
    BacktestConfiguration,
)
from backtester.cache import (
    BarInterval,
    HistoricalDataCache,
)
from backtester.data import Bar, HistoricalDataFeed
from backtester.providers import (
    HistoricalDataProvider,
)
from backtester.services import (
    HistoricalDataService,
)
from backtester.strategies import (
    create_default_strategy_registry,
)


class FakeProvider(HistoricalDataProvider):
    def fetch(self, request):
        return HistoricalDataFeed(
            [
                Bar(
                    symbol=request.symbol,
                    timestamp=datetime(
                        2025,
                        1,
                        2,
                    ),
                    open=100.0,
                    high=101.0,
                    low=99.0,
                    close=100.0,
                    volume=1_000,
                ),
                Bar(
                    symbol=request.symbol,
                    timestamp=datetime(
                        2025,
                        1,
                        3,
                    ),
                    open=105.0,
                    high=106.0,
                    low=104.0,
                    close=105.0,
                    volume=1_000,
                ),
                Bar(
                    symbol=request.symbol,
                    timestamp=datetime(
                        2025,
                        1,
                        4,
                    ),
                    open=110.0,
                    high=111.0,
                    low=109.0,
                    close=110.0,
                    volume=1_000,
                ),
            ]
        )


def test_application_runs_complete_research_flow(
    tmp_path,
):
    data_service = HistoricalDataService(
        provider=FakeProvider(),
        cache=HistoricalDataCache(
            tmp_path
        ),
    )

    application = BacktestApplication(
        data_service=data_service,
        strategy_registry=(
            create_default_strategy_registry()
        ),
    )

    configuration = BacktestConfiguration(
        symbol="AAPL",
        interval=BarInterval.ONE_DAY,
        start=datetime(2025, 1, 2),
        end=datetime(2025, 1, 4),
        strategy_key="buy_and_hold",
        strategy_parameters={
            "trade_quantity": 5,
        },
        initial_cash=10_000.0,
        contract_multiplier=10.0,
        commission_per_order=0.0,
        slippage_bps=0.0,
        maximum_position_percentage=100.0,
        maximum_order_percentage=100.0,
        minimum_cash_percentage=0.0,
        periods_per_year=252,
        risk_free_rate=0.0,
    )

    research_run = application.run(
        configuration
    )

    assert research_run.configuration is (
        configuration
    )

    assert len(research_run.feed) == 3

    assert (
        research_run.result.final_equity
        == pytest.approx(10_250.0)
    )

    assert (
        research_run.result
        .fill_history[0]
        .contract_multiplier
        == 10.0
    )

    assert (
        research_run.analysis
        .performance.total_return
        == pytest.approx(0.025)
    )