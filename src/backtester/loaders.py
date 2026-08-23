import csv
import tempfile
from datetime import datetime
from pathlib import Path

from backtester.data import Bar, HistoricalDataFeed


class CSVBarLoader:
    REQUIRED_COLUMNS = {
        "timestamp",
        "symbol",
        "open",
        "high",
        "low",
        "close",
        "volume",
    }

    def load(
        self,
        path: str | Path,
    ) -> HistoricalDataFeed:
        csv_path = Path(path)

        if not csv_path.is_file():
            raise FileNotFoundError(
                f"historical data file not found: {csv_path}"
            )

        bars = []

        with csv_path.open(
            mode="r",
            encoding="utf-8-sig",
            newline="",
        ) as csv_file:
            reader = csv.DictReader(csv_file)

            self._validate_columns(
                reader.fieldnames,
            )

            for line_number, row in enumerate(
                reader,
                start=2,
            ):
                try:
                    bar = Bar(
                        symbol=row["symbol"],
                        timestamp=datetime.fromisoformat(
                            row["timestamp"]
                        ),
                        open=float(row["open"]),
                        high=float(row["high"]),
                        low=float(row["low"]),
                        close=float(row["close"]),
                        volume=int(row["volume"]),
                    )
                except (
                    KeyError,
                    TypeError,
                    ValueError,
                ) as error:
                    raise ValueError(
                        "invalid historical data "
                        f"on CSV line {line_number}: {error}"
                    ) from error

                bars.append(bar)

        return HistoricalDataFeed(bars)

    def _validate_columns(
        self,
        fieldnames: list[str] | None,
    ):
        if fieldnames is None:
            raise ValueError(
                "CSV file does not contain a header"
            )

        available_columns = {
            field.strip().lower()
            for field in fieldnames
        }

        missing_columns = (
            self.REQUIRED_COLUMNS
            - available_columns
        )

        if missing_columns:
            missing_text = ", ".join(
                sorted(missing_columns)
            )

            raise ValueError(
                "CSV file is missing required columns: "
                f"{missing_text}"
            )
class CSVBarWriter:
    FIELDNAMES = [
        "timestamp",
        "symbol",
        "open",
        "high",
        "low",
        "close",
        "volume",
    ]

    def write(
        self,
        feed: HistoricalDataFeed,
        path: str | Path,
    ):
        csv_path = Path(path)

        csv_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        temporary_path = None

        try:
            with tempfile.NamedTemporaryFile(
                mode="w",
                encoding="utf-8",
                newline="",
                dir=csv_path.parent,
                prefix=f".{csv_path.name}.",
                suffix=".tmp",
                delete=False,
            ) as temporary_file:
                temporary_path = Path(
                    temporary_file.name
                )

                writer = csv.DictWriter(
                    temporary_file,
                    fieldnames=self.FIELDNAMES,
                )

                writer.writeheader()

                for bar in feed:
                    writer.writerow(
                        {
                            "timestamp": (
                                bar.timestamp.isoformat()
                            ),
                            "symbol": bar.symbol,
                            "open": bar.open,
                            "high": bar.high,
                            "low": bar.low,
                            "close": bar.close,
                            "volume": bar.volume,
                        }
                    )

            temporary_path.replace(csv_path)

        finally:
            if (
                temporary_path is not None
                and temporary_path.exists()
            ):
                temporary_path.unlink()