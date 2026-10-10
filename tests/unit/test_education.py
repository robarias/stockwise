"""Pruebas unitarias para el módulo de educación financiera con soporte bilingüe."""

from stockwise.domain.education import (
    METRIC_GLOSSARY,
    METRIC_GLOSSARY_EN,
    METRIC_LABELS,
    METRIC_LABELS_EN,
    SECTION_GUIDES,
    SECTION_GUIDES_EN,
    get_company_description,
    get_company_profiles,
    get_glossary,
    get_help,
    get_metric_labels,
    get_metric_reading,
    get_section_guides,
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
    help_text_es = get_help("pe_ratio", lang="es")
    assert "P/E Ratio" in help_text_es
    assert "Regla de oro" in help_text_es

    help_text_en = get_help("pe_ratio", lang="en")
    assert "P/E Ratio" in help_text_en
    assert "Rule of thumb" in help_text_en
    assert "investors pay" in help_text_en

    assert get_help("non_existent_key") == ""
    assert get_help("non_existent_key", lang="en") == ""


def test_interpret_pe():
    assert interpret_pe(None) is None
    assert "pérdidas" in interpret_pe(-5.0).lower()
    assert "valor" in interpret_pe(12.0).lower()
    assert "estándar" in interpret_pe(20.0).lower()
    assert "crecimiento" in interpret_pe(35.0).lower()
    assert "elevado" in interpret_pe(60.0).lower()

    # English
    assert interpret_pe(None, lang="en") is None
    assert "unprofitable" in interpret_pe(-5.0, lang="en").lower()
    assert "value" in interpret_pe(12.0, lang="en").lower()
    assert "standard" in interpret_pe(20.0, lang="en").lower()
    assert "demanding" in interpret_pe(35.0, lang="en").lower()
    assert "very high" in interpret_pe(60.0, lang="en").lower()


def test_interpret_debt_to_equity():
    assert interpret_debt_to_equity(None) is None
    assert "conservador" in interpret_debt_to_equity(0.5).lower()
    assert "moderada" in interpret_debt_to_equity(1.2).lower()
    assert "apalancamiento" in interpret_debt_to_equity(2.5).lower()

    # English
    assert interpret_debt_to_equity(None, lang="en") is None
    assert "conservative" in interpret_debt_to_equity(0.5, lang="en").lower()
    assert "moderate" in interpret_debt_to_equity(1.2, lang="en").lower()
    assert "high leverage" in interpret_debt_to_equity(2.5, lang="en").lower()


def test_interpret_dividend_yield():
    assert "sin dividendos" in interpret_dividend_yield(0.0).lower()
    assert "moderado" in interpret_dividend_yield(1.5).lower()
    assert "atractivo" in interpret_dividend_yield(3.5).lower()
    assert "payout" in interpret_dividend_yield(8.0).lower()

    # English
    assert "no dividends" in interpret_dividend_yield(0.0, lang="en").lower()
    assert "moderate" in interpret_dividend_yield(1.5, lang="en").lower()
    assert "attractive" in interpret_dividend_yield(3.5, lang="en").lower()
    assert "verify payout" in interpret_dividend_yield(8.0, lang="en").lower()


def test_interpret_volatility():
    assert interpret_volatility(None) is None
    assert "baja" in interpret_volatility(15.0).lower()
    assert "moderada" in interpret_volatility(28.0).lower()
    assert "alta" in interpret_volatility(45.0).lower()

    # English
    assert interpret_volatility(None, lang="en") is None
    assert "low" in interpret_volatility(15.0, lang="en").lower()
    assert "moderate" in interpret_volatility(28.0, lang="en").lower()
    assert "high" in interpret_volatility(45.0, lang="en").lower()


def test_interpret_drawdown():
    assert interpret_drawdown(None) is None
    assert "leve" in interpret_drawdown(-10.0).lower()
    assert "moderada" in interpret_drawdown(-25.0).lower()
    assert "severa" in interpret_drawdown(-45.0).lower()

    # English
    assert interpret_drawdown(None, lang="en") is None
    assert "mild" in interpret_drawdown(-10.0, lang="en").lower()
    assert "moderate" in interpret_drawdown(-25.0, lang="en").lower()
    assert "severe" in interpret_drawdown(-45.0, lang="en").lower()


def test_get_metric_reading():
    assert get_metric_reading("trailing_pe", 12.0) is not None
    assert get_metric_reading("payout_ratio_pct", 45.0) == "🟢 Sostenible (<60%)"
    assert get_metric_reading("payout_ratio_pct", 95.0) == "🔴 Elevado (>80%)"
    assert get_metric_reading("current_ratio", 2.0) == "🟢 Buena liquidez (>1.5)"
    assert get_metric_reading("net_profit_margin_pct", 22.0) == "🟢 Alta rentabilidad (>15%)"
    assert get_metric_reading("unknown_metric", 123) is None
    assert get_metric_reading("trailing_pe", None) is None

    # English readings
    assert get_metric_reading("trailing_pe", 12.0, lang="en") == "🟢 Value / Attractive"
    assert get_metric_reading("payout_ratio_pct", 45.0, lang="en") == "🟢 Sustainable (<60%)"
    assert get_metric_reading("payout_ratio_pct", 95.0, lang="en") == "🔴 Elevated (>80%)"
    assert get_metric_reading("current_ratio", 2.0, lang="en") == "🟢 Good Liquidity (>1.5)"
    assert get_metric_reading("net_profit_margin_pct", 22.0, lang="en") == "🟢 High Profitability (>15%)"
    assert get_metric_reading("return_on_equity_pct", 18.0, lang="en") == "🟢 High Quality (>15%)"
    assert get_metric_reading("peg_ratio", 0.8, lang="en") == "🟢 Attractive vs Growth (<1.0)"


def test_section_guides():
    assert "summary_and_fundamentals" in SECTION_GUIDES
    assert "technical" in SECTION_GUIDES
    assert "risk" in SECTION_GUIDES
    assert "forecast" in SECTION_GUIDES
    assert "events_and_news" in SECTION_GUIDES
    assert "comparison" in SECTION_GUIDES

    # English section guides parity
    guides_en = get_section_guides("en")
    guides_es = get_section_guides("es")
    assert guides_en is SECTION_GUIDES_EN
    assert set(guides_en.keys()) == set(guides_es.keys())
    for key, g_en in guides_en.items():
        assert "title" in g_en
        assert "intro" in g_en
        assert "tips" in g_en
        assert len(g_en["tips"]) == len(guides_es[key]["tips"])


def test_get_company_description():
    eco = get_company_description("ECOPETROL.CL")
    assert eco is not None and "petrolera" in eco.lower()

    eco_en = get_company_description("ECOPETROL.CL", lang="en")
    assert eco_en is not None and "oil and energy" in eco_en.lower()

    aapl = get_company_description("AAPL")
    assert aapl is not None and "apple" in aapl.lower()

    aapl_en = get_company_description("AAPL", lang="en")
    assert aapl_en is not None and "apple designs" in aapl_en.lower()

    fallback = get_company_description("RANDOM_TICKER", "A custom corporate summary.")
    assert fallback == "A custom corporate summary."

    none_desc = get_company_description("UNKNOWN_NO_SUMMARY")
    assert none_desc is None


def test_bilingual_glossary_and_labels_parity():
    # Glossaries parity
    assert set(METRIC_GLOSSARY.keys()) == set(METRIC_GLOSSARY_EN.keys())
    for _key, item in METRIC_GLOSSARY_EN.items():
        assert "title" in item
        assert "description" in item
        assert "rule_of_thumb" in item

    # Metric labels parity
    assert set(METRIC_LABELS.keys()) == set(METRIC_LABELS_EN.keys())

    # Getters
    assert get_glossary("en") is METRIC_GLOSSARY_EN
    assert get_glossary("es") is METRIC_GLOSSARY
    assert get_metric_labels("en") is METRIC_LABELS_EN
    assert get_metric_labels("es") is METRIC_LABELS
    assert len(get_company_profiles("en")) == len(get_company_profiles("es"))
