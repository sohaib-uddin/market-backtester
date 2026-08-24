# Market Backtester

A Python financial market backtesting engine for researching and evaluating trading strategies.

## Project Goals

The project will progressively implement:

- Historical market data handling
- Trading strategy interfaces
- Signal generation
- Order and fill modelling
- Portfolio and position accounting
- Transaction costs and slippage
- Performance analytics
- Risk metrics
- Multi-asset backtesting
- Event-driven simulation

## Architecture

Market Data → Strategy → Signals → Orders → Execution → Portfolio → Performance

## Current Features

- Immutable OHLCV market bars
- Validation of symbols, prices, and volume
- Consistent ticker-symbol normalisation
- Chronologically ordered historical data feeds
- Duplicate bar detection
- Multi-asset symbol filtering
- Inclusive date-range filtering
- Automated tests for market-data behaviour

- Validated buy and sell orders
- Simulated fills using configurable commission and slippage
- Cash and long-position accounting
- Commission-aware average entry prices
- Partial and complete position closing
- Realised and unrealised profit calculation
- Portfolio market value, equity, and total profit
- Protection against overspending and unsupported short selling
- Event-driven historical simulation
- Next-bar-open order execution
- Protection against same-bar look-ahead bias
- Read-only strategy context and historical observations
- Equity-curve recording
- Filled and unfilled order tracking
- Repeatable backtests with isolated run state
- Validated CSV historical-data loading
- Chronological restoration of unordered input data
- Timezone-aware timestamp preservation
- Atomic CSV cache writing
- Request-specific historical data caching
- Cache integrity checks for symbols and date ranges
- Configurable minute, hourly, and daily intervals
- Provider-independent historical-data architecture
- Free Yahoo Finance historical-data integration
- Automatic price-repair support
- Cache-first retrieval with optional refresh
- Offline, deterministic provider tests
- Typed and validated strategy parameters
- Automatic parameter defaults and range checks
- Interface-ready strategy metadata
- Extensible strategy registry
- Configurable buy-and-hold benchmark
- Configurable moving-average crossover strategy

## Execution Assumptions

Orders are currently filled using the closing price of the market bar being
processed. The execution model can apply configurable slippage in basis points
and a fixed commission per order.

Buy orders receive a higher simulated execution price and sell orders receive
a lower simulated execution price. These conservative assumptions reduce the
risk of overstating strategy performance.

The current portfolio supports long positions. Short selling will only be
introduced when borrowing costs, margin requirements, and short-position
accounting can be modelled correctly.

## Simulation Timing

Strategies receive each completed historical bar in chronological order. Orders
generated from that bar are queued and executed using the opening price of the
next available bar for the same symbol.

This timing model prevents a strategy from observing a closing price and then
unrealistically executing at that already-known price. Commission and slippage
are applied when the queued order is filled.

Orders generated from the final bar remain unfilled because no future market
bar exists on which to execute them.

## Historical Data Storage

Historical bars can be loaded from standard CSV files containing:

- `timestamp`
- `symbol`
- `open`
- `high`
- `low`
- `close`
- `volume`

Downloaded datasets can be cached locally using request-specific filenames.
Cache identity includes the symbol, bar interval, start time, and end time.

Files are written atomically through a temporary file, reducing the risk of
leaving corrupted or partially written datasets. Data is validated again when
loaded, so cached files cannot bypass the engine's market-data rules.

## Free Market Data

The initial provider adapter uses `yfinance`, which requires no API key and is
suitable for personal research and educational use.

Daily data supports long historical ranges. Intraday data availability is more
limited; the provider currently restricts intraday history to approximately
the most recent 60 days. The application will communicate these limitations
through its interface.

The provider layer is replaceable. Alternative free or licensed providers can
be added without changing strategies, portfolio accounting, or the simulation
engine.

Price repair is enabled to help detect and correct certain missing values,
currency-unit errors, and split-related inconsistencies. Downloaded data still
passes through the engine's own validation before it can be cached or used.

Provider documentation:

- [yfinance documentation](https://ranaroussi.github.io/yfinance/)
- [yfinance download API](https://ranaroussi.github.io/yfinance/reference/api/yfinance.download.html)

## Configurable Strategies

Strategies describe their own user-adjustable parameters through typed schemas.
Each parameter can define:

- A machine-readable key
- A user-facing label and description
- An integer, decimal, boolean, or choice type
- A default value
- Minimum and maximum values
- An input step size
- Available choices

The graphical interface will use this metadata to generate appropriate controls
automatically. Adding a strategy therefore does not require rewriting the
interface.

The built-in strategies currently include:

### Buy and Hold

Purchases a configurable number of shares near the beginning of the backtest
and holds them as a performance benchmark.

### Moving Average Crossover

Compares configurable short and long moving averages. It enters when the short
average is above the long average and exits when the relationship reverses.
Orders continue to follow next-bar execution timing.

## Development Approach

The engine is being developed in tested, feature-complete milestones. Core
simulation correctness will be established before adding data-provider
integrations and the graphical interface.

## Status

The engine now supports free historical data, caching, realistic event timing,
portfolio accounting, and interface-ready configurable strategies.

The next milestone adds performance and risk analytics, including drawdown,
volatility, Sharpe ratio, trade statistics, and benchmark comparison.