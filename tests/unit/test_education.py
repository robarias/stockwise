"""Pruebas unitarias para el módulo de educación financiera."""

from stockwise.domain.education import (
    METRIC_GLOSSARY,
    METRIC_LABELS,
    SECTION_GUIDES,
    get_help,
    get_metric_reading,
    interpret_debt_to_equity,
    interpret_dividend_yield,
    interpret_drawdown,
    interpret_pe,
    interpret_volatility,
)


def test_metric_glossary_entries():
    assert "pe_ratio" in METRIC_GLOSSARY
    assert "rsi" in METRIC_GLOSSARY
    assert "volatility" in METRIC_GLOSSARY
    for info in METRIC_GLOSSARY.values():
        assert "title" in info
        assert "description" in info
        assert "rule_of_thumb" in info


def test_metric_labels():
    assert "trailing_pe" in METRIC_LABELS
    assert "net_profit_margin_pct" in METRIC_LABELS
    assert "volume" in METRIC_LABELS


def test_get_help():
    help_text = get_help("pe_ratio")
    assert "P/E Ratio" in help_text
    assert "Regla de oro" in help_text
    assert get_help("non_existent_key") == ""


def test_interpret_pe():
    assert interpret_pe(None) is None
    assert "pérdidas" in interpret_pe(-5.0).lower()
    assert "valor" in interpret_pe(12.0).lower()
    assert "estándar" in interpret_pe(20.0).lower()
    assert "crecimiento" in interpret_pe(35.0).lower()
    assert "elevado" in interpret_pe(60.0).lower()


def test_interpret_debt_to_equity():
    assert interpret_debt_to_equity(None) is None
    assert "conservador" in interpret_debt_to_equity(0.5).lower()
    assert "moderada" in interpret_debt_to_equity(1.2).lower()
    assert "apalancamiento" in interpret_debt_to_equity(2.5).lower()


def test_interpret_dividend_yield():
    assert "sin dividendos" in interpret_dividend_yield(0.0).lower()
    assert "moderado" in interpret_dividend_yield(1.5).lower()
    assert "atractivo" in interpret_dividend_yield(3.5).lower()
    assert "payout" in interpret_dividend_yield(8.0).lower()


def test_interpret_volatility():
    assert interpret_volatility(None) is None
    assert "baja" in interpret_volatility(15.0).lower()
    assert "moderada" in interpret_volatility(28.0).lower()
    assert "alta" in interpret_volatility(45.0).lower()


def test_interpret_drawdown():
    assert interpret_drawdown(None) is None
    assert "leve" in interpret_drawdown(-10.0).lower()
    assert "moderada" in interpret_drawdown(-25.0).lower()
    assert "severa" in interpret_drawdown(-45.0).lower()


def test_get_metric_reading():
    assert get_metric_reading("trailing_pe", 12.0) is not None
    assert get_metric_reading("payout_ratio_pct", 45.0) == "🟢 Sostenible (<60%)"
    assert get_metric_reading("payout_ratio_pct", 95.0) == "🔴 Elevado (>80%)"
    assert get_metric_reading("current_ratio", 2.0) == "🟢 Buena liquidez (>1.5)"
    assert get_metric_reading("net_profit_margin_pct", 22.0) == "🟢 Alta rentabilidad (>15%)"
    assert get_metric_reading("unknown_metric", 123) is None
    assert get_metric_reading("trailing_pe", None) is None


def test_section_guides():
    assert "summary_and_fundamentals" in SECTION_GUIDES
    assert "technical" in SECTION_GUIDES
    assert "risk" in SECTION_GUIDES
    assert "forecast" in SECTION_GUIDES
    assert "events_and_news" in SECTION_GUIDES
    assert "comparison" in SECTION_GUIDES


def test_get_company_description():
    from stockwise.domain.education import get_company_description

    eco = get_company_description("ECOPETROL.CL")
    assert eco is not None and "petrolera" in eco.lower()

    aapl = get_company_description("AAPL")
    assert aapl is not None and "apple" in aapl.lower()

    fallback = get_company_description("RANDOM_TICKER", "A custom corporate summary.")
    assert fallback == "A custom corporate summary."

    none_desc = get_company_description("UNKNOWN_NO_SUMMARY")
    assert none_desc is None
