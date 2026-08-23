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

## Development Approach

The engine is being developed in tested, feature-complete milestones. Core
simulation correctness will be established before adding data-provider
integrations and the graphical interface.

## Status

The historical market-data, execution, and portfolio-accounting foundations
are complete. The next milestone connects these components through the
event-driven simulation engine.