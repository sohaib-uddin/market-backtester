from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from enum import Enum
from math import isfinite
from numbers import Real
from typing import Any


class ParameterKind(Enum):
    INTEGER = "integer"
    FLOAT = "float"
    BOOLEAN = "boolean"
    CHOICE = "choice"


@dataclass(frozen=True)
class StrategyParameter:
    key: str
    label: str
    kind: ParameterKind
    default: Any
    minimum: float | None = None
    maximum: float | None = None
    step: float | None = None
    choices: tuple[Any, ...] = ()
    description: str = ""

    def __post_init__(self):
        if not self.key.strip():
            raise ValueError(
                "parameter key must not be empty"
            )

        if not self.key.isidentifier():
            raise ValueError(
                "parameter key must be a valid identifier"
            )

        if not self.label.strip():
            raise ValueError(
                "parameter label must not be empty"
            )

        if not isinstance(
            self.kind,
            ParameterKind,
        ):
            raise TypeError(
                "kind must be a ParameterKind"
            )

        if (
            self.minimum is not None
            and self.maximum is not None
            and self.minimum > self.maximum
        ):
            raise ValueError(
                f"{self.key} minimum must not "
                "exceed maximum"
            )

        if (
            self.step is not None
            and self.step <= 0
        ):
            raise ValueError(
                f"{self.key} step must be positive"
            )

        if (
            self.kind is ParameterKind.CHOICE
            and not self.choices
        ):
            raise ValueError(
                f"{self.key} must define choices"
            )

        self.validate(self.default)

    def validate(self, value: Any) -> Any:
        if self.kind is ParameterKind.INTEGER:
            if (
                isinstance(value, bool)
                or not isinstance(value, int)
            ):
                raise TypeError(
                    f"{self.key} must be an integer"
                )

        elif self.kind is ParameterKind.FLOAT:
            if (
                isinstance(value, bool)
                or not isinstance(value, Real)
            ):
                raise TypeError(
                    f"{self.key} must be a number"
                )

            if not isfinite(value):
                raise ValueError(
                    f"{self.key} must be finite"
                )

            value = float(value)

        elif self.kind is ParameterKind.BOOLEAN:
            if not isinstance(value, bool):
                raise TypeError(
                    f"{self.key} must be a boolean"
                )

        elif self.kind is ParameterKind.CHOICE:
            if value not in self.choices:
                raise ValueError(
                    f"{self.key} must be one of "
                    f"{self.choices}"
                )

        if (
            self.minimum is not None
            and value < self.minimum
        ):
            raise ValueError(
                f"{self.key} must be at least "
                f"{self.minimum}"
            )

        if (
            self.maximum is not None
            and value > self.maximum
        ):
            raise ValueError(
                f"{self.key} must be at most "
                f"{self.maximum}"
            )

        return value


class ParameterSchema:
    def __init__(
        self,
        parameters: Iterable[
            StrategyParameter
        ],
    ):
        self._parameters = tuple(parameters)

        keys = [
            parameter.key
            for parameter in self._parameters
        ]

        if len(keys) != len(set(keys)):
            raise ValueError(
                "parameter keys must be unique"
            )

        self._by_key = {
            parameter.key: parameter
            for parameter in self._parameters
        }

    @property
    def parameters(
        self,
    ) -> tuple[StrategyParameter, ...]:
        return self._parameters

    def resolve(
        self,
        values: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        supplied_values = (
            dict(values)
            if values is not None
            else {}
        )

        unknown_keys = (
            set(supplied_values)
            - set(self._by_key)
        )

        if unknown_keys:
            unknown_text = ", ".join(
                sorted(unknown_keys)
            )

            raise ValueError(
                "unknown strategy parameters: "
                f"{unknown_text}"
            )

        resolved = {}

        for parameter in self._parameters:
            value = supplied_values.get(
                parameter.key,
                parameter.default,
            )

            resolved[parameter.key] = (
                parameter.validate(value)
            )

        return resolved