import plotly.graph_objects as go
from datetime import (
    date,
    datetime,
    time,
    timedelta,
)
from pathlib import Path

import streamlit as st

from backtester import (
    BarInterval,
    ParameterKind,
    create_default_strategy_registry,
    AssetClass,
    Instrument,
    create_default_instrument_catalogue,
    BacktestApplication,
    BacktestConfiguration,
    HistoricalDataCache,
    HistoricalDataService,
    YahooFinanceProvider,
)


st.set_page_config(
    page_title="Market Backtester",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)


INTERVAL_LABELS = {
    BarInterval.ONE_MINUTE: "1 minute",
    BarInterval.FIVE_MINUTES: "5 minutes",
    BarInterval.FIFTEEN_MINUTES: "15 minutes",
    BarInterval.ONE_HOUR: "1 hour",
    BarInterval.ONE_DAY: "1 day",
}

ASSET_CLASS_LABELS = {
    AssetClass.EQUITY: "Equities",
    AssetClass.ETF: "ETFs",
    AssetClass.FOREX: "Currency pairs",
    AssetClass.FUTURE: "Commodity futures",
    AssetClass.INDEX: "Indices",
    AssetClass.CRYPTOCURRENCY: (
        "Cryptocurrencies"
    ),
}


def render_strategy_parameter(parameter):
    key = f"strategy_{parameter.key}"

    if parameter.kind is ParameterKind.INTEGER:
        return st.number_input(
            parameter.label,
            min_value=(
                int(parameter.minimum)
                if parameter.minimum is not None
                else None
            ),
            max_value=(
                int(parameter.maximum)
                if parameter.maximum is not None
                else None
            ),
            value=int(parameter.default),
            step=(
                int(parameter.step)
                if parameter.step is not None
                else 1
            ),
            help=parameter.description or None,
            key=key,
        )

    if parameter.kind is ParameterKind.FLOAT:
        return st.number_input(
            parameter.label,
            min_value=parameter.minimum,
            max_value=parameter.maximum,
            value=float(parameter.default),
            step=(
                float(parameter.step)
                if parameter.step is not None
                else 0.01
            ),
            help=parameter.description or None,
            key=key,
        )

    if parameter.kind is ParameterKind.BOOLEAN:
        return st.checkbox(
            parameter.label,
            value=parameter.default,
            help=parameter.description or None,
            key=key,
        )

    if parameter.kind is ParameterKind.CHOICE:
        return st.selectbox(
            parameter.label,
            options=parameter.choices,
            index=parameter.choices.index(
                parameter.default
            ),
            help=parameter.description or None,
            key=key,
        )

    raise ValueError(
        f"unsupported parameter kind: "
        f"{parameter.kind}"
    )

@st.cache_resource
def create_application():
    data_service = HistoricalDataService(
        provider=YahooFinanceProvider(),
        cache=HistoricalDataCache(
            Path("data") / "cache"
        ),
    )

    strategy_registry = (
        create_default_strategy_registry()
    )

    return BacktestApplication(
        data_service=data_service,
        strategy_registry=(
            strategy_registry
        ),
    )


registry = create_default_strategy_registry()

instrument_catalogue = (
    create_default_instrument_catalogue()
)

definition_by_name = {
    definition.name: definition
    for definition in registry.definitions
}


st.title("Market Backtester")

st.caption(
    "Research historical trading strategies "
    "with configurable execution, portfolio "
    "risk controls, and performance analytics."
)


with st.sidebar:
    st.header("Backtest configuration")

    st.subheader("Market data")

    asset_class = st.selectbox(
        "Asset class",
        options=list(ASSET_CLASS_LABELS),
        format_func=ASSET_CLASS_LABELS.get,
    )

    available_instruments = (
        instrument_catalogue.for_asset_class(
            asset_class
        )
    )

    instrument_options = [
        *available_instruments,
        None,
    ]

    selected_instrument = st.selectbox(
        "Instrument",
        options=instrument_options,
        format_func=lambda instrument: (
            "Custom symbol"
            if instrument is None
            else (
                f"{instrument.name} "
                f"({instrument.symbol})"
            )
        ),
    )

    if selected_instrument is None:
        custom_symbol = st.text_input(
            "Yahoo Finance symbol",
            value="",
            help=(
                "Enter a provider-compatible "
                "symbol such as AAPL, EURUSD=X, "
                "GC=F, or BTC-USD."
            ),
        )

        custom_name = st.text_input(
            "Instrument name",
            value="Custom instrument",
        )

        custom_quote_currency = (
            st.text_input(
                "Quote currency",
                value="USD",
            )
        )

        custom_multiplier = (
            st.number_input(
                "Contract multiplier",
                min_value=0.000001,
                value=1.0,
                step=1.0,
                format="%.6f",
            )
        )

        custom_tick_size = st.number_input(
            "Tick size",
            min_value=0.000001,
            value=0.01,
            step=0.0001,
            format="%.6f",
        )

        try:
            instrument = Instrument(
                symbol=custom_symbol,
                name=custom_name,
                asset_class=asset_class,
                quote_currency=(
                    custom_quote_currency
                ),
                contract_multiplier=(
                    custom_multiplier
                ),
                tick_size=custom_tick_size,
            )
        except (
            TypeError,
            ValueError,
        ):
            instrument = None

    else:
        instrument = selected_instrument

        st.caption(
            f"Quote currency: "
            f"{instrument.quote_currency} · "
            f"Contract multiplier: "
            f"{instrument.contract_multiplier:g} · "
            f"Tick size: "
            f"{instrument.tick_size:g}"
        )

    symbol = (
        instrument.symbol
        if instrument is not None
        else ""
    )

    interval = st.selectbox(
        "Bar interval",
        options=list(INTERVAL_LABELS),
        format_func=INTERVAL_LABELS.get,
        index=4,
    )

    default_end = date.today()
    default_start = (
        default_end
        - timedelta(days=365 * 5)
    )

    start_date = st.date_input(
        "Start date",
        value=default_start,
        max_value=default_end,
    )

    end_date = st.date_input(
        "End date",
        value=default_end,
        min_value=start_date,
        max_value=default_end,
    )

    refresh_data = st.checkbox(
        "Refresh cached data",
        value=False,
        help=(
            "Download the request again instead "
            "of using an existing local cache."
        ),
    )

    st.divider()
    st.subheader("Strategy")

    selected_strategy_name = st.selectbox(
        "Strategy",
        options=list(definition_by_name),
    )

    selected_definition = (
        definition_by_name[
            selected_strategy_name
        ]
    )

    st.caption(
        selected_definition.description
    )

    strategy_parameters = {}

    for parameter in (
        selected_definition
        .parameter_schema
        .parameters
    ):
        strategy_parameters[
            parameter.key
        ] = render_strategy_parameter(
            parameter
        )

    st.divider()
    st.subheader("Portfolio")

    initial_cash = st.number_input(
        "Initial cash",
        min_value=100.0,
        value=100_000.0,
        step=1_000.0,
        format="%.2f",
    )

    with st.expander(
        "Execution assumptions",
        expanded=False,
    ):
        commission_per_order = (
            st.number_input(
                "Commission per order",
                min_value=0.0,
                value=0.0,
                step=0.25,
                format="%.2f",
            )
        )

        slippage_bps = st.number_input(
            "Slippage (basis points)",
            min_value=0.0,
            value=5.0,
            step=1.0,
            format="%.2f",
        )

    with st.expander(
        "Risk controls",
        expanded=False,
    ):
        maximum_position_percentage = (
            st.slider(
                "Maximum position (%)",
                min_value=1.0,
                max_value=100.0,
                value=100.0,
                step=1.0,
            )
        )

        maximum_order_percentage = (
            st.slider(
                "Maximum order (%)",
                min_value=1.0,
                max_value=100.0,
                value=100.0,
                step=1.0,
            )
        )

        minimum_cash_percentage = (
            st.slider(
                "Minimum cash reserve (%)",
                min_value=0.0,
                max_value=99.0,
                value=0.0,
                step=1.0,
            )
        )

    with st.expander(
        "Analytics assumptions",
        expanded=False,
    ):
        periods_per_year = st.number_input(
            "Periods per year",
            min_value=1.0,
            value=252.0,
            step=1.0,
        )

        risk_free_rate_percentage = (
            st.number_input(
                "Annual risk-free rate (%)",
                min_value=-99.0,
                value=0.0,
                step=0.25,
                format="%.2f",
            )
        )

    run_backtest = st.button(
        "Run backtest",
        type="primary",
        use_container_width=True,
    )


if run_backtest:
    if instrument is None:
        st.error(
            "Enter valid custom instrument "
            "details before running."
        )

    elif (
        interval is not BarInterval.ONE_DAY
        and (
            end_date - start_date
        ).days > 60
    ):
        st.error(
            "The free provider limits intraday "
            "history to approximately 60 days. "
            "Choose a shorter range or daily bars."
        )

    else:
        configuration = BacktestConfiguration(
            symbol=instrument.symbol,
            interval=interval,
            start=datetime.combine(
                start_date,
                time.min,
            ),
            end=datetime.combine(
                end_date,
                time.min,
            ),
            strategy_key=(
                selected_definition.key
            ),
            strategy_parameters=(
                strategy_parameters
            ),
            initial_cash=initial_cash,
            contract_multiplier=(
                instrument.contract_multiplier
            ),
            commission_per_order=(
                commission_per_order
            ),
            slippage_bps=slippage_bps,
            maximum_position_percentage=(
                maximum_position_percentage
            ),
            maximum_order_percentage=(
                maximum_order_percentage
            ),
            minimum_cash_percentage=(
                minimum_cash_percentage
            ),
            periods_per_year=periods_per_year,
            risk_free_rate=(
                risk_free_rate_percentage
                / 100
            ),
            refresh_data=refresh_data,
        )

        try:
            with st.spinner(
                "Downloading data and running "
                "the historical simulation..."
            ):
                research_run = (
                    create_application().run(
                        configuration
                    )
                )

            st.session_state[
                "research_run"
            ] = research_run

            st.session_state[
                "instrument"
            ] = instrument

        except Exception as error:
            st.error(
                "The backtest could not be "
                f"completed: {error}"
            )


if "research_run" not in st.session_state:
    st.info(
        "Configure a historical test in the "
        "sidebar, then select Run backtest."
    )

else:
    research_run = st.session_state[
        "research_run"
    ]

    result = research_run.result
    performance = (
        research_run.analysis.performance
    )
    trades = research_run.analysis.trades

    displayed_instrument = (
        st.session_state["instrument"]
    )

    st.subheader(
        f"{displayed_instrument.name} · "
        f"{selected_definition.name}"
    )

    st.caption(
        f"{len(research_run.feed):,} bars · "
        f"{INTERVAL_LABELS.get(
            research_run.configuration.interval,
            research_run.configuration.interval.value,
        )} · "
        f"{research_run.configuration.start.date()} "
        f"to "
        f"{research_run.configuration.end.date()}"
    )

    metric_columns = st.columns(6)

    metric_columns[0].metric(
        "Final equity",
        f"{result.final_equity:,.2f} "
        f"{displayed_instrument.quote_currency}",
    )

    metric_columns[1].metric(
        "Total return",
        f"{performance.total_return:.2%}",
    )

    metric_columns[2].metric(
        "Maximum drawdown",
        f"{performance.maximum_drawdown:.2%}",
    )

    metric_columns[3].metric(
        "Sharpe ratio",
        (
            f"{performance.sharpe_ratio:.2f}"
            if performance.sharpe_ratio
            is not None
            else "N/A"
        ),
    )

    metric_columns[4].metric(
        "Completed trades",
        f"{trades.closed_trades:,}",
    )

    metric_columns[5].metric(
        "Rejected orders",
        f"{result.rejected_orders:,}",
    )

    chart = go.Figure(
        data=[
            go.Candlestick(
                x=[
                    bar.timestamp
                    for bar in research_run.feed
                ],
                open=[
                    bar.open
                    for bar in research_run.feed
                ],
                high=[
                    bar.high
                    for bar in research_run.feed
                ],
                low=[
                    bar.low
                    for bar in research_run.feed
                ],
                close=[
                    bar.close
                    for bar in research_run.feed
                ],
                name=displayed_instrument.symbol,
            )
        ]
    )

    chart.update_layout(
        title="Historical price",
        xaxis_title="Date",
        yaxis_title=(
            f"Price "
            f"({displayed_instrument.quote_currency})"
        ),
        xaxis_rangeslider_visible=False,
        height=500,
        margin=dict(
            l=20,
            r=20,
            t=60,
            b=20,
        ),
    )

    st.plotly_chart(
        chart,
        use_container_width=True,
    )

    st.success(
        "Backtest completed successfully."
    )