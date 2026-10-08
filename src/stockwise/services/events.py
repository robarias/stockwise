"""
Servicio para la obtención y enriquecimiento de noticias y eventos corporativos.
Orquesta la consulta a Yahoo Finance con las funciones analíticas de correlación e impacto.
"""

from typing import Any

import pandas as pd
import yfinance as yf

from stockwise.analytics.events import (
    analyze_earnings_impact,
    correlate_news_with_market,
    parse_upcoming_events,
)
from stockwise.domain.catalogs.colombia import COLOMBIAN_STOCKS
from stockwise.domain.markets import is_colombian_ticker, resolve_ticker


def _extract_search_terms(symbol: str) -> list[str]:
    """Genera términos de búsqueda optimizados para el motor de noticias de Yahoo Finance."""
    terms = [symbol]
    if is_colombian_ticker(symbol):
        base = symbol.split(".")[0].upper()
        terms.append(base)
        if base in COLOMBIAN_STOCKS:
            terms.append(COLOMBIAN_STOCKS[base]["name"])
        # Mapeos especiales a ADRs en EE. UU. para noticias internacionales
        if base in ("CIBEST", "PFCIBEST", "BANCOLOMBIA"):
            terms.append("CIB")
        elif base == "ECOPETROL":
            terms.append("EC")
    return list(dict.fromkeys(terms))


def fetch_stock_events_and_news(
    ticker: str,
    hist: pd.DataFrame | None = None,
    limit: int = 10,
) -> dict[str, Any]:
    """
    Obtiene eventos corporativos (calendario, próximos dividendos, reportes trimestrales)
    y noticias recientes correlacionadas con el precio del activo.
    """
    symbol = resolve_ticker(ticker)
    stock = yf.Ticker(symbol)

    # 1. Calendario corporativo próximo
    calendar_raw = getattr(stock, "calendar", None)
    upcoming = parse_upcoming_events(calendar_raw)

    # 2. Histórico de precios si no fue provisto
    if hist is None or hist.empty:
        try:
            hist = stock.history(period="1y", interval="1d")
        except Exception:
            hist = pd.DataFrame()

    # 3. Reportes trimestrales históricos (sorpresa de EPS y reacción)
    earnings_dates = getattr(stock, "earnings_dates", None)
    recent_earnings = analyze_earnings_impact(earnings_dates, hist, limit=4)

    # 4. Noticias recientes
    raw_news: list[dict[str, Any]] = []
    seen_links: set[str] = set()

    for term in _extract_search_terms(symbol):
        try:
            search_res = yf.Search(term, news_count=limit)
            items = getattr(search_res, "news", []) or []
            for item in items:
                link = item.get("link") or item.get("uuid")
                if link and link not in seen_links:
                    seen_links.add(link)
                    raw_news.append(item)
                    if len(raw_news) >= limit:
                        break
        except Exception:
            continue
        if len(raw_news) >= limit:
            break

    # Si yf.Search no arrojó resultados, intentar fallback a stock.news
    if not raw_news:
        try:
            direct_news = getattr(stock, "news", []) or []
            for item in direct_news:
                link = item.get("link") or item.get("uuid")
                if link and link not in seen_links:
                    seen_links.add(link)
                    raw_news.append(item)
                    if len(raw_news) >= limit:
                        break
        except Exception:
            pass

    # 5. Formatear y correlacionar con mercado
    formatted_news = []
    for item in raw_news:
        ts = item.get("providerPublishTime")
        pub_str = None
        if ts is not None:
            try:
                pub_str = pd.to_datetime(ts, unit="s").strftime("%Y-%m-%d %H:%M")
            except (ValueError, TypeError):
                pub_str = None

        formatted_news.append({
            "title": item.get("title", ""),
            "publisher": item.get("publisher", "Fuente desconocida"),
            "link": item.get("link", ""),
            "providerPublishTime": ts,
            "published_at": pub_str,
        })

    enriched_news = correlate_news_with_market(formatted_news, hist)

    # 6. Resumen global de sentimiento
    pos_count = sum(1 for n in enriched_news if n.get("sentiment", {}).get("label") == "Positivo")
    neg_count = sum(1 for n in enriched_news if n.get("sentiment", {}).get("label") == "Negativo")
    neu_count = sum(1 for n in enriched_news if n.get("sentiment", {}).get("label") == "Neutral")
    total_news = len(enriched_news)

    overall_label = "Neutral"
    if total_news > 0:
        if pos_count > neg_count and pos_count >= total_news * 0.4:
            overall_label = "Mayoritariamente Positivo"
        elif neg_count > pos_count and neg_count >= total_news * 0.4:
            overall_label = "Mayoritariamente Negativo"

    return {
        "symbol": symbol,
        "upcoming_events": upcoming,
        "recent_earnings_reports": recent_earnings,
        "news": enriched_news,
        "sentiment_summary": {
            "total_news": total_news,
            "positive_count": pos_count,
            "negative_count": neg_count,
            "neutral_count": neu_count,
            "overall_label": overall_label,
        },
    }
