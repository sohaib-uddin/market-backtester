from datetime import datetime
import pytest

from backtester.data import Bar, HistoricalDataFeed
from backtester.loaders import CSVBarLoader, CSVBarWriter


def test_csv_loader_creates_chronological_data_feed(
    tmp_path,
):
    csv_path = tmp_path / "prices.csv"

    csv_path.write_text(
        "timestamp,symbol,open,high,low,close,volume\n"
        "2025-01-03T09:31:00,AAPL,102,106,101,105,1200\n"
        "2025-01-02T09:31:00,AAPL,100,104,99,102,1000\n",
        encoding="utf-8",
    )

    feed = CSVBarLoader().load(csv_path)
    bars = list(feed)

    assert len(bars) == 2

    assert bars[0].timestamp == datetime(
        2025,
        1,
        2,
        9,
        31,
    )
    assert bars[0].symbol == "AAPL"
    assert bars[0].open == 100.0
    assert bars[0].high == 104.0
    assert bars[0].low == 99.0
    assert bars[0].close == 102.0
    assert bars[0].volume == 1_000

    assert bars[1].timestamp == datetime(
        2025,
        1,
        3,
        9,
        31,
    )

def test_csv_loader_rejects_missing_columns(tmp_path):
    csv_path = tmp_path / "missing-volume.csv"

    csv_path.write_text(
        "timestamp,symbol,open,high,low,close\n"
        "2025-01-02T09:31:00,AAPL,100,104,99,102\n",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="volume"):
        CSVBarLoader().load(csv_path)


def test_csv_loader_reports_invalid_row_number(tmp_path):
    csv_path = tmp_path / "invalid-price.csv"

    csv_path.write_text(
        "timestamp,symbol,open,high,low,close,volume\n"
        "2025-01-02T09:31:00,AAPL,invalid,104,99,102,1000\n",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="line 2"):
        CSVBarLoader().load(csv_path)


def test_csv_loader_rejects_duplicate_rows(tmp_path):
    csv_path = tmp_path / "duplicates.csv"

    csv_path.write_text(
        "timestamp,symbol,open,high,low,close,volume\n"
        "2025-01-02T09:31:00,AAPL,100,104,99,102,1000\n"
        "2025-01-02T09:31:00,AAPL,100,104,99,102,1000\n",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="duplicate"):
        CSVBarLoader().load(csv_path)


def test_csv_loader_preserves_timezone_information(
    tmp_path,
):
    csv_path = tmp_path / "timezone.csv"

    csv_path.write_text(
        "timestamp,symbol,open,high,low,close,volume\n"
        "2025-01-02T09:31:00+00:00,AAPL,100,104,99,102,1000\n",
        encoding="utf-8",
    )

    feed = CSVBarLoader().load(csv_path)
    bar = list(feed)[0]

    assert bar.timestamp.utcoffset().total_seconds() == 0

def test_csv_writer_round_trip_preserves_bars(tmp_path):
    original_feed = HistoricalDataFeed(
        [
            Bar(
                symbol="AAPL",
                timestamp=datetime(
                    2025,
                    1,
                    2,
                    9,
                    31,
                ),
                open=100.25,
                high=104.50,
                low=99.75,
                close=102.20,
                volume=1_000,
            ),
            Bar(
                symbol="MSFT",
                timestamp=datetime(
                    2025,
                    1,
                    2,
                    9,
                    31,
                ),
                open=420.10,
                high=425.30,
                low=418.60,
                close=423.80,
                volume=900,
            ),
        ]
    )

    csv_path = tmp_path / "cache" / "prices.csv"

    CSVBarWriter().write(
        original_feed,
        csv_path,
    )

    restored_feed = CSVBarLoader().load(csv_path)

    assert list(restored_feed) == list(original_feed)


def test_csv_writer_creates_parent_directories(
    tmp_path,
):
    csv_path = (
        tmp_path
        / "nested"
        / "historical"
        / "prices.csv"
    )

    CSVBarWriter().write(
        HistoricalDataFeed([]),
        csv_path,
    )

    assert csv_path.is_file()

    restored_feed = CSVBarLoader().load(csv_path)

    assert len(restored_feed) == 0