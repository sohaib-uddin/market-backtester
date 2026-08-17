from datetime import datetime

from backtester.data import Bar


def test_bar_stores_ohlcv_data():
    timestamp = datetime(2025, 1, 2)

    bar = Bar(
        symbol="AAPL",
        timestamp=timestamp,
        open=243.85,
        high=244.18,
        low=241.89,
        close=243.85,
        volume=55_720_000,
    )

    assert bar.symbol == "AAPL"
    assert bar.timestamp == timestamp
    assert bar.open == 243.85
    assert bar.high == 244.18
    assert bar.low == 241.89
    assert bar.close == 243.85
    assert bar.volume