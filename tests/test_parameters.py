import pytest

from backtester.parameters import (
    ParameterKind,
    ParameterSchema,
    StrategyParameter,
)


def make_lookback_parameter():
    return StrategyParameter(
        key="lookback",
        label="Lookback period",
        kind=ParameterKind.INTEGER,
        default=20,
        minimum=2,
        maximum=200,
        step=1,
        description=(
            "Number of historical bars used "
            "in the calculation."
        ),
    )


def test_integer_parameter_accepts_valid_value():
    parameter = make_lookback_parameter()

    assert parameter.validate(50) == 50


@pytest.mark.parametrize(
    "value",
    [
        1,
        201,
    ],
)
def test_integer_parameter_rejects_out_of_range_value(
    value,
):
    parameter = make_lookback_parameter()

    with pytest.raises(ValueError, match="lookback"):
        parameter.validate(value)


def test_parameter_schema_applies_defaults():
    schema = ParameterSchema(
        [
            make_lookback_parameter(),
            StrategyParameter(
                key="use_stop_loss",
                label="Use stop loss",
                kind=ParameterKind.BOOLEAN,
                default=False,
            ),
        ]
    )

    resolved = schema.resolve(
        {
            "lookback": 50,
        }
    )

    assert resolved == {
        "lookback": 50,
        "use_stop_loss": False,
    }


def test_parameter_schema_rejects_unknown_parameter():
    schema = ParameterSchema(
        [
            make_lookback_parameter(),
        ]
    )

    with pytest.raises(
        ValueError,
        match="unknown",
    ):
        schema.resolve(
            {
                "lookback": 20,
                "invented_setting": True,
            }
        )