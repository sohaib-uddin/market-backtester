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