"""Pruebas del servidor MCP: registro de herramientas (sin red) y flujos reales (marcados `network`)."""

import asyncio

import pytest
from fastmcp import Client

from stockwise.interfaces.mcp import server

EXPECTED_TOOLS = {
    "get_stock_quote", "get_international_stock_price", "get_technical_analysis", "get_fundamental_analysis",
    "get_risk_and_performance", "compare_stocks", "get_historical_candles", "forecast_stock_prices",
    "list_colombian_stocks_catalog", "get_colombian_stock_analysis", "get_colombian_trm", "convert_usd_to_cop",
    "get_stock_events_and_news", "generate_investment_memo_pdf",
    "calculate_black_scholes", "get_options_surface", "optimize_portfolio",
}


def _list_tool_names() -> set[str]:
    async def run():
        async with Client(server.mcp) as client:
            return {t.name for t in await client.list_tools()}

    return asyncio.run(run())


def test_all_tools_registered():
    assert _list_tool_names() == EXPECTED_TOOLS


def test_catalog_tool_without_network():
    out = server.list_colombian_stocks_catalog("Financiero")
    assert out["currency"] == "COP" and out["total"] == len(out["stocks"]) > 0


def test_colombian_analysis_rejects_non_colombian_ticker():
    out = server.get_colombian_stock_analysis("AAPL")
    assert "error" in out and "colombiano" in out["error"]


def test_parse_tickers_variants():
    expected = ["AAPL", "MSFT"]
    assert server._parse_tickers(["AAPL", "MSFT"]) == expected
    assert server._parse_tickers("AAPL, MSFT") == expected
    assert server._parse_tickers("['AAPL', 'MSFT']") == expected
    assert server._parse_tickers('["AAPL","MSFT"]') == expected


def test_dividend_yield_is_already_percent():
    assert server._dividend_yield_pct({"dividendYield": 0.32}) == 0.32
    assert server._dividend_yield_pct({"dividendRate": 1.08, "currentPrice": 100.0, "dividendYield": 0.5}) == 1.08
    assert server._dividend_yield_pct({}) is None


def test_root_server_shim_compatibility():
    import server as root_server

    assert root_server.mcp is server.mcp
    assert callable(root_server.main)


def test_calculate_black_scholes_tool():
    res = server.calculate_black_scholes(spot=100.0, strike=100.0, dte_days=30.0, volatility=0.20)
    assert "price" in res and res["price"] > 0
    assert "greeks" in res and "delta" in res["greeks"]
    assert "moneyness_status" in res


def test_optimize_portfolio_tool_validation():
    res = server.optimize_portfolio(tickers=["AAPL"])
    assert "error" in res
    assert "al menos 2" in res["error"]



@pytest.mark.network
def test_forecast_tool_end_to_end(tmp_path, monkeypatch):
    monkeypatch.setenv("STOCKWISE_CHARTS_DIR", str(tmp_path))
    from stockwise.config import get_settings

    get_settings.cache_clear()
    out = server.forecast_stock_prices("ECOPETROL", horizon=10, model="ets")
    get_settings.cache_clear()
    assert out["symbol"] == "ECOPETROL.CL" and out["currency"] == "COP"
    assert (tmp_path / out["chart_html"].split("/")[-1]).exists()
