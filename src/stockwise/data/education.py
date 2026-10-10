"""Gestor de datos y catálogo educativo para StockWise.

Carga el catálogo pedagógico estructurado (recursos externos, guías de gráficas
y categorías de glosario) y provee funciones de consulta y filtrado para la interfaz web,
con soporte bilingüe (Español / Inglés).
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from stockwise.domain.education import (
    get_glossary,
    get_metric_labels,
)

_CATALOG_PATH = Path(__file__).resolve().parent / "education_catalog.json"
_CACHE: dict[str, Any] | None = None

GLOSSARY_CATEGORY_NAMES_EN: dict[str, str] = {
    "all": "All Concepts",
    "valuation": "Valuation & Multiples",
    "health": "Profitability & Financial Health",
    "technical": "Technical Analysis & Charts",
    "risk": "Risk & Volatility",
    "forecast_events": "Forecasting & Catalysts",
}

CHART_GUIDES_EN: dict[str, dict[str, Any]] = {
    "candles_and_bands": {
        "id": "candles_and_bands",
        "title": "Japanese Candlesticks, Moving Averages & Bollinger Bands",
        "tab_ref": "📊 Technical",
        "purpose": "Identify dominant trend direction, dynamic support/resistance zones, and volatility compression or breakouts.",
        "what_you_see": [
            "Japanese Candlesticks: Each candle summarizes one session. Green means the price closed above open; red means it closed below. Wicks (shadows) mark daily high and low.",
            "Moving Averages (SMA 50 & SMA 200): Smooth trendlines averaging closing prices over 50 and 200 days to filter daily noise and show underlying trend.",
            "Bollinger Bands: Central 20-day SMA flanked by two outer bands at 2 standard deviations creating a dynamic volatility channel.",
        ],
        "key_signals": [
            "Golden Cross: Occurs when the fast average (SMA 50) crosses above the slow average (SMA 200). Classic confirmation of an emerging structural bull trend.",
            "Death Cross: When SMA 50 crosses below SMA 200, signaling weakness and a possible prolonged downtrend.",
            "Bollinger Squeeze: When bands narrow into a tight neck, volatility has dried up, signaling an imminent violent breakout.",
            "Dynamic Support: In healthy uptrends, pullbacks typically stall and bounce near SMA 50 or the middle Bollinger band.",
        ],
        "rookie_mistakes": [
            "Assuming touching the upper band demands immediate selling: during robust bull runs, price can ride the upper band for weeks.",
            "Buying a falling knife simply because it looks cheap, despite trading well below a downward-sloping SMA 200.",
        ],
    },
    "oscillators_rsi_macd": {
        "id": "oscillators_rsi_macd",
        "title": "Momentum Oscillators: RSI & MACD",
        "tab_ref": "📊 Technical",
        "purpose": "Assess the velocity and intensity of buying and selling pressure to identify euphoric tops, panic bottoms, or trend exhaustion.",
        "what_you_see": [
            "RSI (Relative Strength Index): Scale from 0 to 100 with horizontal thresholds at 70 and 30, gauging recent upward vs downward momentum balance.",
            "MACD Line (blue): Difference between 12-period and 26-period exponential moving averages.",
            "Signal Line (orange): 9-period exponential moving average of the MACD line.",
            "MACD Histogram: Vertical bars showing momentum spread between MACD and Signal lines.",
        ],
        "key_signals": [
            "Overbought (RSI > 70): Price advanced rapidly in a short window. Alerts to potential near-term consolidation or pullback.",
            "Oversold (RSI < 30): Heavy selling occurred. Signals extreme pessimism and potential rebound opportunity.",
            "Bullish MACD Cross: When the MACD line crosses above the Signal line (histogram flips positive), confirming upward momentum.",
            "Bearish Divergence: When price makes a higher high while RSI or MACD registers a lower high, signaling rally exhaustion.",
        ],
        "rookie_mistakes": [
            "Blindly buying just because RSI dipped below 30: fundamentally impaired companies can stay oversold for months while prices drop further.",
            "Using oscillators in isolation without analyzing the broader macro trend on candlestick charts.",
        ],
    },
    "risk_drawdown_garch": {
        "id": "risk_drawdown_garch",
        "title": "Dynamic Risk: Underwater Drawdown & GARCH Volatility",
        "tab_ref": "⚖️ Risk",
        "purpose": "Visualize historical peak-to-trough drawdowns and determine whether the asset is in a tranquil or distressed risk regime.",
        "what_you_see": [
            "Underwater Drawdown Chart: Shows negative percentage pullbacks from the high-water mark (0% = new all-time high). Valleys illustrate drawdown depth.",
            "GARCH Conditional Volatility: Tracks annualized instantaneous volatility estimated via heteroskedastic GARCH(1,1) models.",
            "Regime Bands: Thresholds classifying current risk into Low Volatility, Normal, or Stressed regimes.",
        ],
        "key_signals": [
            "Maximum Historical Drawdown: Answers: 'What is the worst peak-to-trough decline my investment would have suffered?'. Calibrates pain tolerance.",
            "Recovery Time: Tracks how many months or years the asset took to reclaim prior highs following severe corrections.",
            "GARCH Stress Regime: When conditional volatility far exceeds historical averages, risk of sharp daily losses escalates.",
            "Conditional 95% VaR: Maximum expected single-day loss on 19 out of 20 sessions under current conditions.",
        ],
        "rookie_mistakes": [
            "Focusing solely on upside return without assessing drawdown: an asset with 25% annual returns but a 55% drawdown risks panic selling at the trough.",
            "Assuming volatility is constant over time, ignoring volatility clustering during systemic market panics.",
        ],
    },
    "forecasting_and_monte_carlo": {
        "id": "forecasting_and_monte_carlo",
        "title": "Time Series Forecasts & Monte Carlo Simulation",
        "tab_ref": "🔮 Forecast",
        "purpose": "Explore probabilistic price scenarios over coming weeks and quantify uncertainty without relying on magical predictions.",
        "what_you_see": [
            "Central Forecast (dashed line): Most probable trajectory estimated by the selected econometric model (ARIMA, ETS, Theta, or Ensemble).",
            "Confidence Fan (80% & 95%): Expanding shaded bands displaying the expected statistical dispersion range.",
            "Monte Carlo Paths: Hundreds of stochastic price trajectories simulated via Geometric Brownian Motion (GBM).",
            "Terminal Distribution: Final price frequency distribution at the end of the forecasting horizon.",
        ],
        "key_signals": [
            "Cone Divergence: Rapidly expanding confidence cones indicate elevated forecasting uncertainty.",
            "Model Skill (Skill vs. Naive): A positive skill score (>0%) verifies the model outpredicted a naive random-walk guess.",
            "Monte Carlo Profit Probability: Percentage of simulated paths closing above current price at the horizon's end.",
            "Support Breach Probability: Fraction of simulated paths that breached the designated key support level.",
        ],
        "rookie_mistakes": [
            "Treating the central projection as a guaranteed price target: financial markets are fundamentally uncertain.",
            "Relying on models with negative skill scores (skill < 0) or investing solely on econometric forecasts without business fundamentals.",
        ],
    },
    "multiactivo_comparison": {
        "id": "multiactivo_comparison",
        "title": "Multi-Asset Comparison: Base 100 Performance & Correlation",
        "tab_ref": "🆚 Compare",
        "purpose": "Compare relative performance across multiple stocks and uncover non-correlated assets to maximize diversification benefits.",
        "what_you_see": [
            "Base 100 Chart: Normalizes all asset prices to start at $100 on the initial date, enabling apples-to-apples performance comparisons.",
            "Correlation Heatmap: Color-coded grid with coefficients from -1.0 to +1.0 indicating whether assets move in sync or opposite directions.",
        ],
        "key_signals": [
            "Relative Strength: Curves consistently outpacing peers demonstrate relative market leadership.",
            "Correlation Near +1.0: Assets move almost identically (e.g., two large Colombian banks). Holding both provides negligible diversification.",
            "Low or Negative Correlation (0.0 to 0.3 or lower): Combining uncorrelated assets dampens overall portfolio drawdown.",
            "Risk / Return Table: Direct side-by-side comparison of return generated per unit of annualized volatility and drawdown incurred.",
        ],
        "rookie_mistakes": [
            "Assuming 5 stocks provide diversification when all 5 share the same sector and have 0.9 correlation.",
            "Comparing nominal share prices directly rather than normalized percentage returns (e.g., thinking a $10 stock is cheaper than a $300 stock).",
        ],
    },
}


def get_catalog_path() -> Path:
    """Retorna la ruta al archivo JSON del catálogo educativo."""
    return _CATALOG_PATH


def load_education_catalog(force_reload: bool = False) -> dict[str, Any]:
    """Carga el catálogo educativo desde el archivo JSON empaquetado.

    Usa caché en memoria por proceso salvo que se invoque con force_reload=True.
    Si el archivo no existe o está corrupto, retorna un catálogo mínimo de respaldo.
    """
    global _CACHE
    if _CACHE is not None and not force_reload:
        return _CACHE

    if _CATALOG_PATH.exists():
        try:
            with open(_CATALOG_PATH, encoding="utf-8") as f:
                _CACHE = json.load(f)
                return _CACHE
        except Exception:
            pass

    # Respaldo de emergencia en caso de fallo de E/S
    _CACHE = {
        "version": "1.0",
        "updated_at": "2026-10-09",
        "resources": [],
        "chart_guides": {},
        "glossary_categories": [
            {"id": "all", "name": "Todos los conceptos", "icon": "📚"},
        ],
    }
    return _CACHE


def get_educational_resources(
    category: str | None = None,
    level: str | None = None,
    resource_type: str | None = None,
    only_active: bool = False,
) -> list[dict[str, Any]]:
    """Obtiene y filtra los recursos pedagógicos curados.

    Args:
        category: Filtro por categoría temática (o None para todos).
        level: Filtro por nivel ('Principiante', 'Intermedio', 'Avanzado').
        resource_type: Filtro por tipo ('Curso gratuito', 'Libro fundamental', etc.).
        only_active: Si True, excluye recursos marcados como caídos o rotos.
    """
    catalog = load_education_catalog()
    resources: list[dict[str, Any]] = catalog.get("resources", [])

    filtered = []
    for r in resources:
        if only_active and r.get("status") not in ("active", "healthy", None):
            continue
        if category and category != "Todas" and r.get("category") != category:
            continue
        if level and level != "Todos" and r.get("level") != level:
            continue
        if resource_type and resource_type != "Todos" and r.get("type") != resource_type:
            continue
        filtered.append(r)
    return filtered


def get_chart_guides(lang: str = "es") -> dict[str, dict[str, Any]]:
    """Retorna el diccionario de guías de interpretación de las gráficas de StockWise."""
    if lang == "en":
        return CHART_GUIDES_EN
    catalog = load_education_catalog()
    return catalog.get("chart_guides", {})


def get_chart_guide(guide_id: str, lang: str = "es") -> dict[str, Any] | None:
    """Retorna la guía de una gráfica específica por su identificador."""
    guides = get_chart_guides(lang=lang)
    return guides.get(guide_id)


def get_glossary_categories(lang: str = "es") -> list[dict[str, Any]]:
    """Retorna la lista de categorías del glosario para filtros en la interfaz."""
    catalog = load_education_catalog()
    raw_cats = catalog.get(
        "glossary_categories",
        [{"id": "all", "name": "Todos los conceptos", "icon": "📚"}],
    )
    if lang != "en":
        return raw_cats

    translated = []
    for c in raw_cats:
        c_copy = dict(c)
        c_copy["name"] = GLOSSARY_CATEGORY_NAMES_EN.get(c.get("id", ""), c.get("name", ""))
        translated.append(c_copy)
    return translated


def search_glossary(
    query: str = "",
    category_id: str | None = None,
    lang: str = "es",
) -> list[dict[str, Any]]:
    """Busca y filtra conceptos en el glosario unificado.

    Combina el catálogo con el glosario base de métricas del dominio en el idioma seleccionado.

    Args:
        query: Cadena de texto para buscar en título, descripción o regla de oro.
        category_id: ID de categoría para filtrar ('all', 'valuation', 'health', etc.).
        lang: Código de idioma ('es' o 'en').
    """
    catalog = load_education_catalog()
    categories = catalog.get("glossary_categories", [])

    # Obtener el conjunto de llaves permitidas según la categoría
    allowed_keys: set[str] | None = None
    if category_id and category_id != "all":
        for cat in categories:
            if cat.get("id") == category_id:
                allowed_keys = set(cat.get("keys", []))
                break

    glossary = get_glossary(lang=lang)
    metric_labels = get_metric_labels(lang=lang)

    q = query.strip().lower()
    results: list[dict[str, Any]] = []

    for key, info in glossary.items():
        if allowed_keys is not None and key not in allowed_keys:
            continue

        title = info.get("title", "")
        desc = info.get("description", "")
        thumb = info.get("rule_of_thumb", "")
        friendly_label = metric_labels.get(key, key)

        if q:
            matches_title = q in title.lower() or q in friendly_label.lower() or q in key.lower()
            matches_desc = q in desc.lower()
            matches_thumb = q in thumb.lower()
            if not (matches_title or matches_desc or matches_thumb):
                continue

        results.append(
            {
                "key": key,
                "title": title,
                "friendly_label": friendly_label,
                "description": desc,
                "rule_of_thumb": thumb,
            }
        )

    # Ordenar alfabéticamente por título
    results.sort(key=lambda x: x["title"].lower())
    return results


__all__ = [
    "CHART_GUIDES_EN",
    "GLOSSARY_CATEGORY_NAMES_EN",
    "get_catalog_path",
    "get_chart_guide",
    "get_chart_guides",
    "get_educational_resources",
    "get_glossary_categories",
    "load_education_catalog",
    "search_glossary",
]
