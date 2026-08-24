from backtester.orders import Order, OrderSide
from backtester.parameters import (
    ParameterKind,
    ParameterSchema,
    StrategyParameter,
)
from backtester.strategy import (
    Strategy,
    StrategyContext,
)
from backtester.registry import StrategyRegistry

class BuyAndHoldStrategy(Strategy):
    key = "buy_and_hold"
    name = "Buy and Hold"

    description = (
        "Buys a fixed quantity after the first "
        "observed bar and holds the position for "
        "the remainder of the backtest."
    )

    parameter_schema = ParameterSchema(
        [
            StrategyParameter(
                key="trade_quantity",
                label="Trade quantity",
                kind=ParameterKind.INTEGER,
                default=10,
                minimum=1,
                maximum=1_000_000,
                step=1,
                description=(
                    "Number of shares purchased "
                    "at the beginning of the test."
                ),
            )
        ]
    )

    def __init__(
        self,
        *,
        trade_quantity: int = 10,
    ):
        parameters = (
            self.parameter_schema.resolve(
                {
                    "trade_quantity": (
                        trade_quantity
                    ),
                }
            )
        )

        self.trade_quantity = parameters[
            "trade_quantity"
        ]

    def on_bar(
        self,
        context: StrategyContext,
    ) -> list[Order]:
        symbol = context.bar.symbol
        history = context.history[symbol]
        position = context.positions.get(
            symbol
        )

        if (
            len(history) == 1
            and position is None
        ):
            return [
                Order(
                    symbol=symbol,
                    quantity=self.trade_quantity,
                    side=OrderSide.BUY,
                )
            ]

        return []

class MovingAverageCrossoverStrategy(Strategy):
    key = "moving_average_crossover"
    name = "Moving Average Crossover"

    description = (
        "Buys when the short moving average is "
        "above the long moving average and exits "
        "when the relationship reverses."
    )

    parameter_schema = ParameterSchema(
        [
            StrategyParameter(
                key="short_window",
                label="Short moving average",
                kind=ParameterKind.INTEGER,
                default=20,
                minimum=2,
                maximum=500,
                step=1,
                description=(
                    "Number of bars in the faster "
                    "moving average."
                ),
            ),
            StrategyParameter(
                key="long_window",
                label="Long moving average",
                kind=ParameterKind.INTEGER,
                default=50,
                minimum=3,
                maximum=1_000,
                step=1,
                description=(
                    "Number of bars in the slower "
                    "moving average."
                ),
            ),
            StrategyParameter(
                key="trade_quantity",
                label="Trade quantity",
                kind=ParameterKind.INTEGER,
                default=10,
                minimum=1,
                maximum=1_000_000,
                step=1,
                description=(
                    "Number of shares purchased "
                    "when an entry signal occurs."
                ),
            ),
        ]
    )

    def __init__(
        self,
        *,
        short_window: int = 20,
        long_window: int = 50,
        trade_quantity: int = 10,
    ):
        parameters = (
            self.parameter_schema.resolve(
                {
                    "short_window": short_window,
                    "long_window": long_window,
                    "trade_quantity": (
                        trade_quantity
                    ),
                }
            )
        )

        if (
            parameters["short_window"]
            >= parameters["long_window"]
        ):
            raise ValueError(
                "short_window must be smaller "
                "than long_window"
            )

        self.short_window = parameters[
            "short_window"
        ]
        self.long_window = parameters[
            "long_window"
        ]
        self.trade_quantity = parameters[
            "trade_quantity"
        ]

    def on_bar(
        self,
        context: StrategyContext,
    ) -> list[Order]:
        symbol = context.bar.symbol
        history = context.history[symbol]

        if len(history) < self.long_window:
            return []

        closes = [
            bar.close
            for bar in history
        ]

        short_average = (
            sum(closes[-self.short_window:])
            / self.short_window
        )

        long_average = (
            sum(closes[-self.long_window:])
            / self.long_window
        )

        position = context.positions.get(
            symbol
        )

        if (
            short_average > long_average
            and position is None
        ):
            return [
                Order(
                    symbol=symbol,
                    quantity=self.trade_quantity,
                    side=OrderSide.BUY,
                )
            ]

        if (
            short_average < long_average
            and position is not None
        ):
            return [
                Order(
                    symbol=symbol,
                    quantity=position.quantity,
                    side=OrderSide.SELL,
                )
            ]

        return []

def create_default_strategy_registry(
) -> StrategyRegistry:
    return StrategyRegistry(
        [
            BuyAndHoldStrategy,
            MovingAverageCrossoverStrategy,
        ]
    )