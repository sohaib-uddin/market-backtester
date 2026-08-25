from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime
from types import MappingProxyType
from typing import Any
from math import isfinite
from numbers import Real

from backtester.analytics import (
    BacktestAnalyser,
    BacktestAnalysis,
)
from backtester.cache import (
    BarInterval,
    HistoricalDataRequest,
)
from backtester.data import HistoricalDataFeed
from backtester.engine import (
    BacktestEngine,
    BacktestResult,
)
from backtester.execution import ExecutionModel
from backtester.registry import StrategyRegistry
from backtester.risk import (
    RiskLimits,
    RiskManager,
)
from backtester.services import (
    HistoricalDataService,
)


@dataclass(frozen=True)
class BacktestConfiguration:
    symbol: str
    interval: BarInterval
    start: datetime
    end: datetime
    strategy_key: str
    strategy_parameters: Mapping[str, Any]
    initial_cash: float
    contract_multiplier: float
    commission_per_order: float
    slippage_bps: float
    maximum_position_percentage: float
    maximum_order_percentage: float
    minimum_cash_percentage: float
    periods_per_year: float
    risk_free_rate: float
    refresh_data: bool = False

    def __post_init__(self):
        normalised_symbol = (
            self.symbol.strip().upper()
        )

        if not normalised_symbol:
            raise ValueError(
                "symbol must not be empty"
            )

        if not self.strategy_key.strip():
            raise ValueError(
                "strategy_key must not be empty"
            )

        if not isinstance(
            self.strategy_parameters,
            Mapping,
        ):
            raise TypeError(
                "strategy_parameters must be "
                "a mapping"
            )

        if not isinstance(
            self.refresh_data,
            bool,
        ):
            raise TypeError(
                "refresh_data must be a boolean"
            )

        if (
            isinstance(
                self.contract_multiplier,
                bool,
            )
            or not isinstance(
                self.contract_multiplier,
                Real,
            )
        ):
            raise TypeError(
                "contract_multiplier must be "
                "a number"
            )

        if (
            not isfinite(
                self.contract_multiplier
            )
            or self.contract_multiplier <= 0
        ):
            raise ValueError(
                "contract_multiplier must be "
                "positive and finite"
            )

        object.__setattr__(
            self,
            "symbol",
            normalised_symbol,
        )

        object.__setattr__(
            self,
            "strategy_parameters",
            MappingProxyType(
                dict(
                    self.strategy_parameters
                )
            ),
        )


@dataclass(frozen=True)
class ResearchRun:
    configuration: BacktestConfiguration
    request: HistoricalDataRequest
    feed: HistoricalDataFeed
    result: BacktestResult
    analysis: BacktestAnalysis


class BacktestApplication:
    def __init__(
        self,
        *,
        data_service: HistoricalDataService,
        strategy_registry: StrategyRegistry,
    ):
        if not isinstance(
            data_service,
            HistoricalDataService,
        ):
            raise TypeError(
                "data_service must be a "
                "HistoricalDataService"
            )

        if not isinstance(
            strategy_registry,
            StrategyRegistry,
        ):
            raise TypeError(
                "strategy_registry must be a "
                "StrategyRegistry"
            )

        self.data_service = data_service
        self.strategy_registry = (
            strategy_registry
        )

    def run(
        self,
        configuration: BacktestConfiguration,
    ) -> ResearchRun:
        if not isinstance(
            configuration,
            BacktestConfiguration,
        ):
            raise TypeError(
                "configuration must be a "
                "BacktestConfiguration"
            )

        request = HistoricalDataRequest(
            symbol=configuration.symbol,
            interval=configuration.interval,
            start=configuration.start,
            end=configuration.end,
        )

        feed = self.data_service.get(
            request,
            refresh=(
                configuration.refresh_data
            ),
        )

        strategy = (
            self.strategy_registry.create(
                configuration.strategy_key,
                configuration
                .strategy_parameters,
            )
        )

        execution_model = ExecutionModel(
            commission_per_order=(
                configuration
                .commission_per_order
            ),
            slippage_bps=(
                configuration.slippage_bps
            ),
        )

        risk_manager = RiskManager(
            RiskLimits(
                maximum_position_percentage=(
                    configuration
                    .maximum_position_percentage
                ),
                maximum_order_percentage=(
                    configuration
                    .maximum_order_percentage
                ),
                minimum_cash_percentage=(
                    configuration
                    .minimum_cash_percentage
                ),
            )
        )

        engine = BacktestEngine(
            initial_cash=(
                configuration.initial_cash
            ),
            execution_model=execution_model,
            risk_manager=risk_manager,
            contract_multipliers={
                configuration.symbol: (
                    configuration
                    .contract_multiplier
                ),
            },
        )

        result = engine.run(
            feed=feed,
            strategy=strategy,
        )

        analysis = BacktestAnalyser(
            periods_per_year=(
                configuration.periods_per_year
            ),
            risk_free_rate=(
                configuration.risk_free_rate
            ),
        ).analyse(result)

        return ResearchRun(
            configuration=configuration,
            request=request,
            feed=feed,
            result=result,
            analysis=analysis,
        )