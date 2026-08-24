from dataclasses import dataclass
from datetime import datetime
from math import isfinite, sqrt
from numbers import Real
from statistics import mean, stdev

from backtester.engine import BacktestResult
from collections.abc import Iterable
from backtester.execution import Fill
from backtester.orders import OrderSide


@dataclass(frozen=True)
class PerformanceReport:
    total_return: float
    annualised_return: float
    annualised_volatility: float
    downside_deviation: float
    sortino_ratio: float | None
    calmar_ratio: float | None
    sharpe_ratio: float | None
    maximum_drawdown: float
    maximum_drawdown_peak: datetime | None
    maximum_drawdown_trough: datetime | None
    period_returns: tuple[float, ...]

@dataclass(frozen=True)
class TradeReport:
    total_fills: int
    closed_trades: int
    winning_trades: int
    losing_trades: int
    breakeven_trades: int
    win_rate: float | None
    gross_profit: float
    gross_loss: float
    net_profit: float
    average_trade: float | None
    largest_win: float | None
    largest_loss: float | None
    profit_factor: float | None
    total_commission: float

@dataclass(frozen=True)
class BacktestAnalysis:
    performance: PerformanceReport
    trades: TradeReport

@dataclass(frozen=True)
class BenchmarkComparison:
    strategy_return: float
    benchmark_return: float
    excess_return: float
    relative_return: float


class TradeAnalyzer:
    def analyze(
        self,
        fills: Iterable[Fill],
    ) -> TradeReport:
        fill_list = tuple(fills)

        positions: dict[
            str,
            tuple[int, float],
        ] = {}

        trade_profits = []
        total_commission = 0.0

        for fill in fill_list:
            if not isinstance(fill, Fill):
                raise TypeError(
                    "trade analyzer requires "
                    "Fill objects"
                )

            total_commission += fill.commission

            current_quantity, average_cost = (
                positions.get(
                    fill.symbol,
                    (0, 0.0),
                )
            )

            if fill.side is OrderSide.BUY:
                existing_cost = (
                    current_quantity
                    * average_cost
                )

                new_quantity = (
                    current_quantity
                    + fill.quantity
                )

                new_cost = (
                    existing_cost
                    + fill.gross_value
                    + fill.commission
                )

                positions[fill.symbol] = (
                    new_quantity,
                    new_cost / new_quantity,
                )

                continue

            if fill.quantity > current_quantity:
                raise ValueError(
                    "sell fill exceeds the tracked "
                    f"position for {fill.symbol}"
                )

            net_proceeds = (
                fill.gross_value
                - fill.commission
            )

            sold_cost = (
                average_cost
                * fill.quantity
            )

            trade_profit = (
                net_proceeds
                - sold_cost
            )

            trade_profits.append(
                trade_profit
            )

            remaining_quantity = (
                current_quantity
                - fill.quantity
            )

            if remaining_quantity == 0:
                positions.pop(
                    fill.symbol,
                    None,
                )
            else:
                positions[fill.symbol] = (
                    remaining_quantity,
                    average_cost,
                )

        winning_trades = [
            profit
            for profit in trade_profits
            if profit > 0
        ]

        losing_trades = [
            profit
            for profit in trade_profits
            if profit < 0
        ]

        breakeven_trades = [
            profit
            for profit in trade_profits
            if profit == 0
        ]

        closed_trades = len(trade_profits)

        if closed_trades:
            win_rate = (
                len(winning_trades)
                / closed_trades
            )

            average_trade = (
                sum(trade_profits)
                / closed_trades
            )

            largest_win = (
                max(winning_trades)
                if winning_trades
                else None
            )

            largest_loss = (
                min(losing_trades)
                if losing_trades
                else None
            )
        else:
            win_rate = None
            average_trade = None
            largest_win = None
            largest_loss = None

        gross_profit = sum(
            winning_trades
        )

        gross_loss = -sum(
            losing_trades
        )

        if gross_loss > 0:
            profit_factor = (
                gross_profit / gross_loss
            )
        else:
            profit_factor = None

        return TradeReport(
            total_fills=len(fill_list),
            closed_trades=closed_trades,
            winning_trades=len(
                winning_trades
            ),
            losing_trades=len(
                losing_trades
            ),
            breakeven_trades=len(
                breakeven_trades
            ),
            win_rate=win_rate,
            gross_profit=gross_profit,
            gross_loss=gross_loss,
            net_profit=sum(trade_profits),
            average_trade=average_trade,
            largest_win=largest_win,
            largest_loss=largest_loss,
            profit_factor=profit_factor,
            total_commission=total_commission,
        )


class PerformanceAnalyzer:
    def __init__(
        self,
        *,
        periods_per_year: float = 252,
        risk_free_rate: float = 0.0,
    ):
        if (
            isinstance(periods_per_year, bool)
            or not isinstance(
                periods_per_year,
                Real,
            )
        ):
            raise TypeError(
                "periods_per_year must be a number"
            )

        if (
            not isfinite(periods_per_year)
            or periods_per_year <= 0
        ):
            raise ValueError(
                "periods_per_year must be "
                "positive and finite"
            )

        if (
            isinstance(risk_free_rate, bool)
            or not isinstance(
                risk_free_rate,
                Real,
            )
        ):
            raise TypeError(
                "risk_free_rate must be a number"
            )

        if (
            not isfinite(risk_free_rate)
            or risk_free_rate <= -1
        ):
            raise ValueError(
                "risk_free_rate must be finite "
                "and greater than -1"
            )

        self.periods_per_year = float(
            periods_per_year
        )

        self.risk_free_rate = float(
            risk_free_rate
        )

    def analyze(
        self,
        result: BacktestResult,
    ) -> PerformanceReport:
        equities = [
            point.equity
            for point in result.equity_curve
        ]

        period_returns = self._calculate_returns(
            equities
        )

        annualised_return = (
            self._annualised_return(
                total_return=result.total_return,
                periods=len(period_returns),
            )
        )

        annualised_volatility = (
            self._annualised_volatility(
                period_returns
            )
        )

        downside_deviation = (
            self._downside_deviation(
                period_returns
            )
        )

        sortino_ratio = self._sortino_ratio(
            period_returns,
            downside_deviation,
        )

        sharpe_ratio = self._sharpe_ratio(
            period_returns
        )

        (
            maximum_drawdown,
            drawdown_peak,
            drawdown_trough,
        ) = self._maximum_drawdown(result)

        if maximum_drawdown > 0:
            calmar_ratio = (
                annualised_return
                / maximum_drawdown
            )
        else:
            calmar_ratio = None

        return PerformanceReport(
            total_return=result.total_return,
            annualised_return=annualised_return,
            annualised_volatility=(
                annualised_volatility
            ),
            downside_deviation=(
                downside_deviation
            ),
            sortino_ratio=sortino_ratio,
            calmar_ratio=calmar_ratio,
            sharpe_ratio=sharpe_ratio,
            maximum_drawdown=maximum_drawdown,
            maximum_drawdown_peak=(
                drawdown_peak
            ),
            maximum_drawdown_trough=(
                drawdown_trough
            ),
            period_returns=period_returns,
        )

    @staticmethod
    def _calculate_returns(
        equities: list[float],
    ) -> tuple[float, ...]:
        returns = []

        for previous, current in zip(
            equities,
            equities[1:],
        ):
            if previous <= 0:
                raise ValueError(
                    "equity must remain positive"
                )

            returns.append(
                (current / previous) - 1
            )

        return tuple(returns)

    def _annualised_return(
        self,
        *,
        total_return: float,
        periods: int,
    ) -> float:
        if periods == 0:
            return 0.0

        if total_return <= -1:
            return -1.0

        return (
            (1 + total_return)
            ** (
                self.periods_per_year
                / periods
            )
        ) - 1

    def _annualised_volatility(
        self,
        returns: tuple[float, ...],
    ) -> float:
        if len(returns) < 2:
            return 0.0

        return (
            stdev(returns)
            * sqrt(self.periods_per_year)
        )

    def _sharpe_ratio(
        self,
        returns: tuple[float, ...],
    ) -> float | None:
        if len(returns) < 2:
            return None

        return_deviation = stdev(returns)

        if return_deviation == 0:
            return None

        risk_free_per_period = (
            (1 + self.risk_free_rate)
            ** (
                1 / self.periods_per_year
            )
        ) - 1

        excess_return = (
            mean(returns)
            - risk_free_per_period
        )

        return (
            excess_return
            / return_deviation
            * sqrt(self.periods_per_year)
        )
        def _downside_deviation(
            self,
            returns: tuple[float, ...],
        ) -> float:
            if not returns:
                return 0.0

            target_return = (
                (1 + self.risk_free_rate)
                ** (
                    1 / self.periods_per_year
                )
            ) - 1

            downside_squares = [
                min(
                    period_return
                    - target_return,
                    0.0,
                ) ** 2
                for period_return in returns
            ]

            period_downside_deviation = (
                sum(downside_squares)
                / len(downside_squares)
            ) ** 0.5

            return (
                period_downside_deviation
                * sqrt(self.periods_per_year)
            )

        def _sortino_ratio(
            self,
            returns: tuple[float, ...],
            annualised_downside_deviation: float,
        ) -> float | None:
            if (
                not returns
                or annualised_downside_deviation
                == 0
            ):
                return None

            target_return = (
                (1 + self.risk_free_rate)
                ** (
                    1 / self.periods_per_year
                )
            ) - 1

            mean_excess_return = (
                mean(returns)
                - target_return
            )

            annualised_excess_return = (
                mean_excess_return
                * self.periods_per_year
            )

            return (
                annualised_excess_return
                / annualised_downside_deviation
            )

    def _downside_deviation(
        self,
        returns: tuple[float, ...],
    ) -> float:
        if not returns:
            return 0.0

        target_return = (
            (1 + self.risk_free_rate)
            ** (
                1 / self.periods_per_year
            )
        ) - 1

        downside_squares = [
            min(
                period_return
                - target_return,
                0.0,
            ) ** 2
            for period_return in returns
        ]

        period_downside_deviation = (
            sum(downside_squares)
            / len(downside_squares)
        ) ** 0.5

        return (
            period_downside_deviation
            * sqrt(self.periods_per_year)
        )

    def _sortino_ratio(
        self,
        returns: tuple[float, ...],
        annualised_downside_deviation: float,
    ) -> float | None:
        if (
            not returns
            or annualised_downside_deviation
            == 0
        ):
            return None

        target_return = (
            (1 + self.risk_free_rate)
            ** (
                1 / self.periods_per_year
            )
        ) - 1

        mean_excess_return = (
            mean(returns)
            - target_return
        )

        annualised_excess_return = (
            mean_excess_return
            * self.periods_per_year
        )

        return (
            annualised_excess_return
            / annualised_downside_deviation
        )


    @staticmethod
    def _maximum_drawdown(
        result: BacktestResult,
    ) -> tuple[
        float,
        datetime | None,
        datetime | None,
    ]:
        if not result.equity_curve:
            return 0.0, None, None

        peak_equity = (
            result.equity_curve[0].equity
        )

        peak_timestamp = (
            result.equity_curve[0].timestamp
        )

        maximum_drawdown = 0.0
        maximum_peak = None
        maximum_trough = None

        for point in result.equity_curve:
            if point.equity > peak_equity:
                peak_equity = point.equity
                peak_timestamp = point.timestamp

            drawdown = (
                peak_equity - point.equity
            ) / peak_equity

            if drawdown > maximum_drawdown:
                maximum_drawdown = drawdown
                maximum_peak = peak_timestamp
                maximum_trough = point.timestamp

        return (
            maximum_drawdown,
            maximum_peak,
            maximum_trough,
        )

class BacktestAnalyser:
    def __init__(
        self,
        *,
        periods_per_year: float = 252,
        risk_free_rate: float = 0.0,
    ):
        self.performance_analyzer = (
            PerformanceAnalyzer(
                periods_per_year=(
                    periods_per_year
                ),
                risk_free_rate=risk_free_rate,
            )
        )

        self.trade_analyzer = TradeAnalyzer()

    def analyse(
        self,
        result: BacktestResult,
    ) -> BacktestAnalysis:
        if not isinstance(
            result,
            BacktestResult,
        ):
            raise TypeError(
                "result must be a BacktestResult"
            )

        return BacktestAnalysis(
            performance=(
                self.performance_analyzer
                .analyze(result)
            ),
            trades=(
                self.trade_analyzer.analyze(
                    result.fill_history
                )
            ),
        )

    def compare(
        self,
        *,
        strategy_result: BacktestResult,
        benchmark_result: BacktestResult,
    ) -> BenchmarkComparison:
        if not isinstance(
            strategy_result,
            BacktestResult,
        ):
            raise TypeError(
                "strategy_result must be a "
                "BacktestResult"
            )

        if not isinstance(
            benchmark_result,
            BacktestResult,
        ):
            raise TypeError(
                "benchmark_result must be a "
                "BacktestResult"
            )

        strategy_return = (
            strategy_result.total_return
        )

        benchmark_return = (
            benchmark_result.total_return
        )

        benchmark_growth = (
            1 + benchmark_return
        )

        if benchmark_growth <= 0:
            raise ValueError(
                "benchmark growth must remain "
                "positive"
            )

        return BenchmarkComparison(
            strategy_return=strategy_return,
            benchmark_return=benchmark_return,
            excess_return=(
                strategy_return
                - benchmark_return
            ),
            relative_return=(
                (1 + strategy_return)
                / benchmark_growth
            ) - 1,
        )