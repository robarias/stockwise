"""
Pruebas unitarias para el análisis de eventos, sentimiento de noticias y correlación de mercado.
Sin acceso a red (pruebas puras y deterministas).
"""

import pandas as pd

from stockwise.analytics.events import (
    analyze_earnings_impact,
    compute_headline_sentiment,
    correlate_news_with_market,
    parse_upcoming_events,
)
from stockwise.viz.technical import build_technical_figure


def test_compute_headline_sentiment_english():
    pos = compute_headline_sentiment("Apple beats revenue expectations and reports record profit")
    assert pos["label"] == "Positivo"
    assert pos["score"] > 0
    assert "beat" in pos["positive_matches"] or "record" in pos["positive_matches"]

    neg = compute_headline_sentiment("Tesla stock plunges after earnings miss and warning")
    assert neg["label"] == "Negativo"
    assert neg["score"] < 0

    neu = compute_headline_sentiment("Company schedules annual shareholder meeting")
    assert neu["label"] == "Neutral"
    assert neu["score"] == 0.0


def test_compute_headline_sentiment_spanish():
    pos = compute_headline_sentiment("Ecopetrol reporta récord en utilidades y anuncia dividendo extraordinario")
    assert pos["label"] == "Positivo"
    assert pos["score"] > 0

    neg = compute_headline_sentiment("Acción cae tras caída en ventas e investigación de regulador")
    assert neg["label"] == "Negativo"
    assert neg["score"] < 0


def test_correlate_news_with_market(ohlcv):
    first_date = ohlcv.index[10].strftime("%Y-%m-%d")
    news_items = [
        {
            "title": "Empresa reporta ganancias sólidas",
            "published_at": f"{first_date} 10:00",
            "publisher": "Reuters",
        },
        {
            "title": "Sin fecha válida",
            "publisher": "Unknown",
        },
    ]

    correlated = correlate_news_with_market(news_items, ohlcv)
    assert len(correlated) == 2

    # Primer item debe tener market_impact
    imp = correlated[0]["market_impact"]
    assert imp is not None
    assert imp["session_date"] == first_date
    assert "day_change_pct" in imp
    assert "volume_ratio" in imp
    assert isinstance(imp["abnormal_volume"], bool)

    # Segundo item sin fecha
    assert correlated[1]["market_impact"] is None


def test_correlate_news_with_empty_history():
    news_items = [{"title": "Récord de ventas", "published_at": "2026-05-01"}]
    res = correlate_news_with_market(news_items, pd.DataFrame())
    assert len(res) == 1
    assert res[0]["sentiment"]["label"] == "Positivo"
    assert res[0]["market_impact"] is None


def test_analyze_earnings_impact(ohlcv):
    sample_date = ohlcv.index[5].strftime("%Y-%m-%d")
    earnings_df = pd.DataFrame(
        [
            {"Earnings Date": sample_date, "Reported EPS": 2.15, "EPS Estimate": 2.00, "Surprise(%)": 7.5},
        ]
    )

    impacts = analyze_earnings_impact(earnings_df, ohlcv, limit=2)
    assert len(impacts) == 1
    assert impacts[0]["reported_eps"] == 2.15
    assert impacts[0]["eps_estimate"] == 2.00
    assert impacts[0]["surprise_pct"] == 7.5
    assert impacts[0]["market_reaction"] is not None
    assert impacts[0]["market_reaction"]["session_date"] == sample_date


def test_parse_upcoming_events():
    cal = {
        "Earnings Date": ["2026-11-05"],
        "Ex-Dividend Date": "2026-08-10",
        "Dividend Date": "2026-08-15",
        "Earnings Average": 1.95,
        "Revenue Average": 50000000000.0,
    }
    parsed = parse_upcoming_events(cal)
    assert parsed["earnings_date"] == "2026-11-05"
    assert parsed["ex_dividend_date"] == "2026-08-10"
    assert parsed["earnings_average"] == 1.95
    assert parsed["revenue_average"] == 50000000000.0


def test_technical_figure_with_event_markers(ohlcv):
    event_date = ohlcv.index[-10].strftime("%Y-%m-%d")
    events = [
        {"date": event_date, "type": "EARNINGS", "label": "E", "text": "Balance positivo"},
        {"date": event_date, "type": "NEWS", "label": "N", "text": "Noticia importante"},
    ]
    fig = build_technical_figure("TEST", ohlcv, "USD", show_days=100, events=events)
    # Debe tener anotaciones creadas
    assert hasattr(fig.layout, "annotations")
    annots = fig.layout.annotations
    labels = [a.text for a in annots]
    assert any("<b>E</b>" in t for t in labels)
    assert any("<b>N</b>" in t for t in labels)
