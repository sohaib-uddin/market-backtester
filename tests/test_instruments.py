import pytest

from backtester.instruments import (
    AssetClass,
    Instrument,
    InstrumentCatalogue,
    create_default_instrument_catalogue,
)


def test_instrument_stores_contract_metadata():
    instrument = Instrument(
        symbol="GC=F",
        name="Gold Futures",
        asset_class=AssetClass.FUTURE,
        quote_currency="USD",
        contract_multiplier=100.0,
        tick_size=0.10,
    )

    assert instrument.symbol == "GC=F"
    assert instrument.quote_currency == "USD"
    assert instrument.contract_multiplier == 100.0
    assert instrument.tick_size == 0.10


def test_instrument_normalises_identifiers():
    instrument = Instrument(
        symbol="  eurusd=x  ",
        name="EUR/USD",
        asset_class=AssetClass.FOREX,
        quote_currency=" usd ",
        contract_multiplier=1.0,
        tick_size=0.0001,
    )

    assert instrument.symbol == "EURUSD=X"
    assert instrument.quote_currency == "USD"


def test_catalogue_rejects_duplicate_symbol():
    instrument = Instrument(
        symbol="AAPL",
        name="Apple",
        asset_class=AssetClass.EQUITY,
        quote_currency="USD",
    )

    with pytest.raises(
        ValueError,
        match="duplicate",
    ):
        InstrumentCatalogue(
            [
                instrument,
                instrument,
            ]
        )


def test_default_catalogue_contains_multiple_assets():
    catalogue = (
        create_default_instrument_catalogue()
    )

    assert catalogue.get(
        "EURUSD=X"
    ).asset_class is AssetClass.FOREX

    assert catalogue.get(
        "GC=F"
    ).contract_multiplier == 100.0

    assert catalogue.get(
        "AAPL"
    ).asset_class is AssetClass.EQUITY