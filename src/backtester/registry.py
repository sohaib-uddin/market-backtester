from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from typing import Any

from backtester.parameters import ParameterSchema
from backtester.strategy import Strategy


@dataclass(frozen=True)
class StrategyDefinition:
    key: str
    name: str
    description: str
    parameter_schema: ParameterSchema
    strategy_class: type[Strategy]


class StrategyRegistry:
    def __init__(
        self,
        strategy_classes: Iterable[
            type[Strategy]
        ] = (),
    ):
        self._definitions = {}

        for strategy_class in strategy_classes:
            self.register(strategy_class)

    def register(
        self,
        strategy_class: type[Strategy],
    ):
        if (
            not isinstance(strategy_class, type)
            or not issubclass(
                strategy_class,
                Strategy,
            )
        ):
            raise TypeError(
                "registered strategy must inherit "
                "from Strategy"
            )

        key = getattr(
            strategy_class,
            "key",
            "",
        )

        name = getattr(
            strategy_class,
            "name",
            "",
        )

        description = getattr(
            strategy_class,
            "description",
            "",
        )

        parameter_schema = getattr(
            strategy_class,
            "parameter_schema",
            None,
        )

        if not isinstance(key, str) or not key:
            raise ValueError(
                "strategy must define a non-empty key"
            )

        if not isinstance(name, str) or not name:
            raise ValueError(
                "strategy must define a non-empty name"
            )

        if not isinstance(description, str):
            raise TypeError(
                "strategy description must be a string"
            )

        if not isinstance(
            parameter_schema,
            ParameterSchema,
        ):
            raise TypeError(
                "strategy must define a "
                "ParameterSchema"
            )

        if key in self._definitions:
            raise ValueError(
                f"duplicate strategy key: {key}"
            )

        self._definitions[key] = StrategyDefinition(
            key=key,
            name=name,
            description=description,
            parameter_schema=parameter_schema,
            strategy_class=strategy_class,
        )

    @property
    def definitions(
        self,
    ) -> tuple[StrategyDefinition, ...]:
        return tuple(
            self._definitions.values()
        )

    def create(
        self,
        key: str,
        values: Mapping[str, Any] | None = None,
    ) -> Strategy:
        if key not in self._definitions:
            raise ValueError(
                f"unknown strategy: {key}"
            )

        definition = self._definitions[key]

        parameters = (
            definition.parameter_schema.resolve(
                values
            )
        )

        return definition.strategy_class(
            **parameters
        )