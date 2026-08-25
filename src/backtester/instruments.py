from collections.abc import Iterable
from dataclasses import dataclass
from enum import Enum
from math import isfinite
from numbers import Real


class AssetClass(Enum):
    EQUITY = "equity"
    ETF = "etf"
    FOREX = "forex"
    FUTURE = "future"
    INDEX = "index"
    CRYPTOCURRENCY = "cryptocurrency"


@dataclass(frozen=True)
class Instrument:
    symbol: str
    name: str
    asset_class: AssetClass
    quote_currency: str
    contract_multiplier: float = 1.0
    tick_size: float = 0.01

    def __post_init__(self):
        if not isinstance(self.symbol, str):
            raise TypeError(
                "symbol must be a string"
            )

        normalised_symbol = (
            self.symbol.strip().upper()
        )

        if not normalised_symbol:
            raise ValueError(
                "symbol must not be empty"
            )

        if (
            not isinstance(self.name, str)
            or not self.name.strip()
        ):
            raise ValueError(
                "name must not be empty"
            )

        if not isinstance(
            self.asset_class,
            AssetClass,
        ):
            raise TypeError(
                "asset_class must be an "
                "AssetClass"
            )

        if not isinstance(
            self.quote_currency,
            str,
        ):
            raise TypeError(
                "quote_currency must be a string"
            )

        normalised_currency = (
            self.quote_currency
            .strip()
            .upper()
        )

        if not normalised_currency:
            raise ValueError(
                "quote_currency must not be empty"
            )

        self._validate_positive_number(
            self.contract_multiplier,
            "contract_multiplier",
        )

        self._validate_positive_number(
            self.tick_size,
            "tick_size",
        )

        object.__setattr__(
            self,
            "symbol",
            normalised_symbol,
        )

        object.__setattr__(
            self,
            "name",
            self.name.strip(),
        )

        object.__setattr__(
            self,
            "quote_currency",
            normalised_currency,
        )

        object.__setattr__(
            self,
            "contract_multiplier",
            float(self.contract_multiplier),
        )

        object.__setattr__(
            self,
            "tick_size",
            float(self.tick_size),
        )

    @staticmethod
    def _validate_positive_number(
        value: float,
        name: str,
    ):
        if (
            isinstance(value, bool)
            or not isinstance(value, Real)
        ):
            raise TypeError(
                f"{name} must be a number"
            )

        if not isfinite(value) or value <= 0:
            raise ValueError(
                f"{name} must be positive "
                "and finite"
            )


class InstrumentCatalogue:
    def __init__(
        self,
        instruments: Iterable[Instrument],
    ):
        instrument_list = tuple(
            instruments
        )

        for instrument in instrument_list:
            if not isinstance(
                instrument,
                Instrument,
            ):
                raise TypeError(
                    "catalogue entries must be "
                    "Instrument objects"
                )

        symbols = [
            instrument.symbol
            for instrument in instrument_list
        ]

        if len(symbols) != len(set(symbols)):
            raise ValueError(
                "duplicate instrument symbol"
            )

        self._instruments = instrument_list

        self._by_symbol = {
            instrument.symbol: instrument
            for instrument in instrument_list
        }

    @property
    def instruments(
        self,
    ) -> tuple[Instrument, ...]:
        return self._instruments

    def get(
        self,
        symbol: str,
    ) -> Instrument:
        normalised_symbol = (
            symbol.strip().upper()
        )

        if normalised_symbol not in self._by_symbol:
            raise KeyError(
                f"unknown instrument: "
                f"{normalised_symbol}"
            )

        return self._by_symbol[
            normalised_symbol
        ]

    def for_asset_class(
        self,
        asset_class: AssetClass,
    ) -> tuple[Instrument, ...]:
        return tuple(
            instrument
            for instrument in self._instruments
            if instrument.asset_class
            is asset_class
        )


def create_default_instrument_catalogue(
) -> InstrumentCatalogue:
    return InstrumentCatalogue(
        [
            Instrument(
                symbol="AAPL",
                name="Apple",
                asset_class=AssetClass.EQUITY,
                quote_currency="USD",
            ),
            Instrument(
                symbol="MSFT",
                name="Microsoft",
                asset_class=AssetClass.EQUITY,
                quote_currency="USD",
            ),
            Instrument(
                symbol="SPY",
                name="S&P 500 ETF",
                asset_class=AssetClass.ETF,
                quote_currency="USD",
            ),
            Instrument(
                symbol="EURUSD=X",
                name="EUR/USD",
                asset_class=AssetClass.FOREX,
                quote_currency="USD",
                tick_size=0.0001,
            ),
            Instrument(
                symbol="GBPUSD=X",
                name="GBP/USD",
                asset_class=AssetClass.FOREX,
                quote_currency="USD",
                tick_size=0.0001,
            ),
            Instrument(
                symbol="USDJPY=X",
                name="USD/JPY",
                asset_class=AssetClass.FOREX,
                quote_currency="JPY",
                tick_size=0.01,
            ),
            Instrument(
                symbol="GC=F",
                name="Gold Futures",
                asset_class=AssetClass.FUTURE,
                quote_currency="USD",
                contract_multiplier=100.0,
                tick_size=0.10,
            ),
            Instrument(
                symbol="SI=F",
                name="Silver Futures",
                asset_class=AssetClass.FUTURE,
                quote_currency="USD",
                contract_multiplier=5_000.0,
                tick_size=0.005,
            ),
            Instrument(
                symbol="CL=F",
                name="Crude Oil Futures",
                asset_class=AssetClass.FUTURE,
                quote_currency="USD",
                contract_multiplier=1_000.0,
                tick_size=0.01,
            ),
            Instrument(
                symbol="^GSPC",
                name="S&P 500 Index",
                asset_class=AssetClass.INDEX,
                quote_currency="USD",
            ),
            Instrument(
                symbol="BTC-USD",
                name="Bitcoin / US Dollar",
                asset_class=(
                    AssetClass.CRYPTOCURRENCY
                ),
                quote_currency="USD",
                tick_size=0.01,
            ),
        ]
    )