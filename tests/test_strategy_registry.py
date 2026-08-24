import pytest

from backtester.parameters import (
    ParameterKind,
    ParameterSchema,
    StrategyParameter,
)
from backtester.registry import StrategyRegistry
from backtester.strategy import Strategy


class DummyStrategy(Strategy):
    key = "dummy"
    name = "Dummy strategy"
    description = "Strategy used for testing."

    parameter_schema = ParameterSchema(
        [
            StrategyParameter(
                key="lookback",
                label="Lookback period",
                kind=ParameterKind.INTEGER,
                default=20,
                minimum=2,
                maximum=200,
                step=1,
            )
        ]
    )

    def __init__(self, lookback):
        self.lookback = lookback

    def on_bar(self, context):
        return []


def test_registry_describes_registered_strategy():
    registry = StrategyRegistry(
        [
            DummyStrategy,
        ]
    )

    definitions = registry.definitions

    assert len(definitions) == 1
    assert definitions[0].key == "dummy"
    assert definitions[0].name == "Dummy strategy"
    assert definitions[0].parameter_schema is (
        DummyStrategy.parameter_schema
    )


def test_registry_creates_strategy_with_parameters():
    registry = StrategyRegistry(
        [
            DummyStrategy,
        ]
    )

    strategy = registry.create(
        "dummy",
        {
            "lookback": 50,
        },
    )

    assert isinstance(strategy, DummyStrategy)
    assert strategy.lookback == 50


def test_registry_rejects_duplicate_strategy_key():
    with pytest.raises(
        ValueError,
        match="duplicate",
    ):
        StrategyRegistry(
            [
                DummyStrategy,
                DummyStrategy,
            ]
        )