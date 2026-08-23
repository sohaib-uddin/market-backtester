from datetime import datetime
import pytest

from backtester.data import Bar, HistoricalDataFeed


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


def test_bar_rejects_empty_symbol():
    with pytest.raises(ValueError, match="symbol"):
        Bar(
            symbol="",
            timestamp=datetime(2025, 1, 2),
            open=100.0,
            high=105.0,
            low=95.0,
            close=102.0,
            volume=1_000,
        )


def test_bar_rejects_inconsistent_prices():
    with pytest.raises(ValueError, match="high"):
        Bar(
            symbol="AAPL",
            timestamp=datetime(2025, 1, 2),
            open=100.0,
            high=99.0,
            low=95.0,
            close=102.0,
            volume=1_000,
        )


def test_bar_rejects_negative_volume():
    with pytest.raises(ValueError, match="volume"):
        Bar(
            symbol="AAPL",
            timestamp=datetime(2025, 1, 2),
            open=100.0,
            high=105.0,
            low=95.0,
            close=102.0,
            volume=-1,
        )

def test_historical_data_feed_sorts_bars_chronologically():
    later_bar = Bar(
        symbol="AAPL",
        timestamp=datetime(2025, 1, 3),
        open=102.0,
        high=106.0,
        low=101.0,
        close=105.0,
        volume=1_200,
    )

    earlier_bar = Bar(
        symbol="AAPL",
        timestamp=datetime(2025, 1, 2),
        open=100.0,
        high=104.0,
        low=99.0,
        close=102.0,
        volume=1_000,
    )

    feed = HistoricalDataFeed([later_bar, earlier_bar])

    assert list(feed) == [earlier_bar, later_bar]


def test_historical_data_feed_rejects_duplicate_bars():
    bar = Bar(
        symbol="AAPL",
        timestamp=datetime(2025, 1, 2),
        open=100.0,
        high=104.0,
        low=99.0,
        close=102.0,
        volume=1_000,
    )

    with pytest.raises(ValueError, match="duplicate"):
        HistoricalDataFeed([bar, bar])


def test_historical_data_feed_reports_its_length():
    bars = [
        Bar(
            symbol="AAPL",
            timestamp=datetime(2025, 1, 2),
            open=100.0,
            high=104.0,
            low=99.0,
            close=102.0,
            volume=1_000,
        ),
        Bar(
            symbol="AAPL",
            timestamp=datetime(2025, 1, 3),
            open=102.0,
            high=106.0,
            low=101.0,
            close=105.0,
            volume=1_200,
        ),
    ]

    feed = HistoricalDataFeed(bars)

    assert len(feed) == 2

def test_historical_data_feed_filters_by_symbol():
    aapl_bar = Bar(
        symbol="AAPL",
        timestamp=datetime(2025, 1, 2),
        open=100.0,
        high=104.0,
        low=99.0,
        close=102.0,
        volume=1_000,
    )

    msft_bar = Bar(
        symbol="MSFT",
        timestamp=datetime(2025, 1, 2),
        open=420.0,
        high=425.0,
        low=418.0,
        close=423.0,
        volume=900,
    )

    feed = HistoricalDataFeed([aapl_bar, msft_bar])

    filtered_feed = feed.filter(symbols=["AAPL"])

    assert list(filtered_feed) == [aapl_bar]


def test_historical_data_feed_filters_by_date_range():
    first_bar = Bar(
        symbol="AAPL",
        timestamp=datetime(2025, 1, 2),
        open=100.0,
        high=104.0,
        low=99.0,
        close=102.0,
        volume=1_000,
    )

    middle_bar = Bar(
        symbol="AAPL",
        timestamp=datetime(2025, 1, 3),
        open=102.0,
        high=106.0,
        low=101.0,
        close=105.0,
        volume=1_200,
    )

    last_bar = Bar(
        symbol="AAPL",
        timestamp=datetime(2025, 1, 4),
        open=105.0,
        high=108.0,
        low=103.0,
        close=107.0,
        volume=1_100,
    )

    feed = HistoricalDataFeed([first_bar, middle_bar, last_bar])

    filtered_feed = feed.filter(
        start=datetime(2025, 1, 3),
        end=datetime(2025, 1, 3),
    )

    assert list(filtered_feed) == [middle_bar]


def test_historical_data_feed_lists_available_symbols():
    feed = HistoricalDataFeed(
        [
            Bar(
                symbol="MSFT",
                timestamp=datetime(2025, 1, 2),
                open=420.0,
                high=425.0,
                low=418.0,
                close=423.0,
                volume=900,
            ),
            Bar(
                symbol="AAPL",
                timestamp=datetime(2025, 1, 2),
                open=100.0,
                high=104.0,
                low=99.0,
                close=102.0,
                volume=1_000,
            ),
        ]
    )

    assert feed.symbols == ("AAPL", "MSFT")

def test_bar_normalises_symbol():
    bar = Bar(
        symbol="  aapl  ",
        timestamp=datetime(2025, 1, 2),
        open=100.0,
        high=104.0,
        low=99.0,
        close=102.0,
        volume=1_000,
    )

    assert bar.symbol == "AAPL"


def test_feed_detects_duplicates_after_symbol_normalisation():
    first_bar = Bar(
        symbol="aapl",
        timestamp=datetime(2025, 1, 2),
        open=100.0,
        high=104.0,
        low=99.0,
        close=102.0,
        volume=1_000,
    )

    duplicate_bar = Bar(
        symbol="AAPL",
        timestamp=datetime(2025, 1, 2),
        open=100.0,
        high=104.0,
        low=99.0,
        close=102.0,
        volume=1_000,
    )

    with pytest.raises(ValueError, match="duplicate"):
        HistoricalDataFeed([first_bar, duplicate_bar])


def test_feed_rejects_reversed_date_range():
    feed = HistoricalDataFeed([])

    with pytest.raises(ValueError, match="start"):
        feed.filter(
            start=datetime(2025, 1, 3),
            end=datetime(2025, 1, 2),
        )

@pytest.mark.parametrize(
    "close_price",
    [
        float("nan"),
        float("inf"),
        float("-inf"),
    ],
)
def test_bar_rejects_non_finite_prices(
    close_price,
):
    with pytest.raises(ValueError, match="close"):
        Bar(
            symbol="AAPL",
            timestamp=datetime(2025, 1, 2),
            open=100.0,
            high=105.0,
            low=95.0,
            close=close_price,
            volume=1_000,
        )


def test_bar_rejects_non_datetime_timestamp():
    with pytest.raises(TypeError, match="timestamp"):
        Bar(
            symbol="AAPL",
            timestamp="2025-01-02",
            open=100.0,
            high=105.0,
            low=95.0,
            close=102.0,
            volume=1_000,
        )


@pytest.mark.parametrize(
    "volume",
    [
        True,
        1.5,
    ],
)
def test_bar_rejects_non_integer_volume(volume):
    with pytest.raises(TypeError, match="volume"):
        Bar(
            symbol="AAPL",
            timestamp=datetime(2025, 1, 2),
            open=100.0,
            high=105.0,
            low=95.0,
            close=102.0,
            volume=volume,
        )