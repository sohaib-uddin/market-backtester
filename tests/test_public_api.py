from backtester import (
    BacktestEngine,
    Bar,
    ExecutionModel,
    Fill,
    HistoricalDataFeed,
    Order,
    OrderSide,
    Portfolio,
    Position,
    BacktestResult,
    EquityPoint,
    PositionView,
    Strategy,
    StrategyContext,
    BarInterval,
    CSVBarLoader,
    CSVBarWriter,
    HistoricalDataCache,
    HistoricalDataRequest,
    HistoricalDataProvider,
    HistoricalDataService,
    YahooFinanceProvider,
    )


def test_public_api_exposes_core_components():
    assert BacktestEngine is not None
    assert Bar is not None
    assert HistoricalDataFeed is not None
    assert Order is not None
    assert OrderSide is not None
    assert Fill is not None
    assert ExecutionModel is not None
    assert Portfolio is not None
    assert Position is not None
    assert BacktestResult is not None
    assert EquityPoint is not None
    assert PositionView is not None
    assert Strategy is not None
    assert StrategyContext is not None
    assert BarInterval is not None
    assert CSVBarLoader is not None
    assert CSVBarWriter is not None
    assert HistoricalDataCache is not None
    assert HistoricalDataRequest is not None
    assert HistoricalDataProvider is not None
    assert HistoricalDataService is not None
    assert YahooFinanceProvider is not None