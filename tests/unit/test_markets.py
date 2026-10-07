import pytest

from stockwise.domain.catalogs.colombia import ALIASES, COLOMBIAN_STOCKS, list_colombian_stocks
from stockwise.domain.markets import is_colombian_ticker, resolve_ticker


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("ecopetrol", "ECOPETROL.CL"),
        ("ECOPETROL.BVC", "ECOPETROL.CL"),
        ("  isa  ", "ISA.CL"),
        ("ISA.CL", "ISA.CL"),
        ("Bancolombia", "CIBEST.CL"),
        ("PFBCOLOM", "PFCIBEST.CL"),
        ("AAPL", "AAPL"),
        ("aapl", "AAPL"),
        ("CIB", "CIB"),  # ADR en NYSE: no debe resolverse a la BVC
        ("^GSPC", "^GSPC"),
        ("SAP.DE", "SAP.DE"),
    ],
)
def test_resolve_ticker(raw, expected):
    assert resolve_ticker(raw) == expected


def test_is_colombian_ticker():
    assert is_colombian_ticker("ECOPETROL.CL")
    assert is_colombian_ticker("isa.cl")
    assert not is_colombian_ticker("AAPL")


def test_catalog_integrity():
    valid_types = {"COMUN", "PREFERENTE", "ETF"}
    for base, meta in COLOMBIAN_STOCKS.items():
        assert base == base.upper() and "." not in base
        assert meta["type"] in valid_types
        assert meta["name"] and meta["sector"]


def test_aliases_point_to_catalog():
    assert set(ALIASES.values()) <= set(COLOMBIAN_STOCKS)


def test_list_colombian_stocks_filters_by_sector():
    etfs = list_colombian_stocks("etf")
    assert etfs and all(s["type"] == "ETF" and s["symbol"].endswith(".CL") for s in etfs)
    assert len(list_colombian_stocks()) == len(COLOMBIAN_STOCKS)
    assert list_colombian_stocks("sector-inexistente") == []
