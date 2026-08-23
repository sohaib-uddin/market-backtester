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

## Development Approach

The engine is being developed in tested, feature-complete milestones. Core
simulation correctness will be established before adding data-provider
integrations and the graphical interface.

## Status

The simulation engine now includes validated market data, execution,
portfolio accounting, event-driven processing, CSV ingestion, and local
historical-data caching.

The next milestone adds a provider-independent data service and integration
with a free historical market-data source.