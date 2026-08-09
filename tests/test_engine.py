from backtester.engine import BacktestEngine

def test_engine_initialises():
    engine = BacktestEngine()

    assert engine.current_time is None