"""
Análisis de eventos corporativos, noticias y correlación de impacto en mercado.
Funciones puras sobre DataFrames y estructuras de datos: sin red ni E/S.
"""

import re
from datetime import datetime
from typing import Any

import numpy as np
import pandas as pd

POSITIVE_KEYWORDS = {
    # Inglés
    "record", "beat", "beats", "beating", "surge", "surges", "surging", "jump", "jumps", "rally", "rallies",
    "gain", "gains", "profit", "profitable", "growth", "outperform", "upgrade", "upgraded", "buy", "bullish",
    "soar", "soars", "boost", "boosts", "dividend", "dividends", "strong", "higher", "positive", "exceeds",
    # Español
    "récord", "supera", "ganancia", "ganancias", "utilidad", "utilidades", "crecimiento", "sube", "alza",
    "repunta", "repunte", "dividendo", "dividendos", "mejora", "alcista", "compra", "positivo", "fuerte",
    "rentabilidad", "adjudica", "acuerdo", "alianza", "histórico",
}

NEGATIVE_KEYWORDS = {
    # Inglés
    "plunge", "plunges", "fall", "falls", "drop", "drops", "miss", "misses", "missing", "loss", "losses",
    "decline", "declines", "cut", "cuts", "downgrade", "downgraded", "sell", "bearish", "tumble", "tumbles",
    "crash", "probe", "investigation", "lawsuit", "fine", "fraud", "debt", "risk", "warning", "weak",
    "slump", "lower", "negative", "disappoints",
    # Español
    "cae", "caída", "caen", "desplome", "desploma", "pérdida", "pérdidas", "retroceso", "retrocede", "baja",
    "bajan", "recorte", "rebaja", "deuda", "sanción", "investigación", "demanda", "riesgo", "alerta", "débil",
    "bajista", "negativo", "incumplimiento", "falla", "crisis", "litigio",
}


def _tokenize(text: str) -> set[str]:
    """Extrae palabras en minúsculas ignorando puntuación."""
    return set(re.findall(r"\b\w+\b", text.lower()))


def compute_headline_sentiment(title: str, summary: str = "") -> dict[str, Any]:
    """
    Evalúa el sentimiento de un titular/resumen financiero en español o inglés.
    Retorna score (-1.0 a 1.0) y etiqueta ('Positivo', 'Negativo', 'Neutral').
    """
    words = _tokenize(f"{title} {summary}")
    pos_matches = words.intersection(POSITIVE_KEYWORDS)
    neg_matches = words.intersection(NEGATIVE_KEYWORDS)

    pos_count = len(pos_matches)
    neg_count = len(neg_matches)
    total = pos_count + neg_count

    if total == 0:
        score = 0.0
        label = "Neutral"
    else:
        score = (pos_count - neg_count) / total
        if score >= 0.2:
            label = "Positivo"
        elif score <= -0.2:
            label = "Negativo"
        else:
            label = "Neutral"

    return {
        "score": round(float(score), 2),
        "label": label,
        "positive_matches": sorted(pos_matches),
        "negative_matches": sorted(neg_matches),
    }


def _normalize_index_dates(df: pd.DataFrame) -> pd.DataFrame:
    """Retorna copia con DatetimeIndex normalizado sin zona horaria ni horas."""
    if df.empty or not isinstance(df.index, pd.DatetimeIndex):
        return df.copy()
    out = df.copy()
    dt_idx = out.index
    if isinstance(dt_idx, pd.DatetimeIndex):
        if dt_idx.tz is not None:
            dt_idx = dt_idx.tz_localize(None)
        out.index = dt_idx.normalize()
    return out


def correlate_news_with_market(
    news_items: list[dict[str, Any]],
    hist: pd.DataFrame,
) -> list[dict[str, Any]]:
    """
    Cruza una lista de noticias con el historial de precios para evaluar la reacción del mercado.
    Para cada noticia calcula:
    - Retorno de la sesión (% cambio respecto al cierre anterior o intradía)
    - Gap de apertura (%)
    - Ratio de volumen vs media móvil de 20 ruedas
    - Indicador de volumen anormal (> 1.5x)
    """
    if hist.empty or "Close" not in hist.columns:
        # Si no hay histórico, retorna noticias con sentimiento sin impacto de mercado
        enriched: list[dict[str, Any]] = []
        for item in news_items:
            copied = dict(item)
            sentiment = compute_headline_sentiment(item.get("title", ""))
            copied["sentiment"] = sentiment
            copied["market_impact"] = None
            enriched.append(copied)
        return enriched

    norm_hist = _normalize_index_dates(hist)
    has_volume = "Volume" in norm_hist.columns
    if has_volume:
        vol_sma20 = norm_hist["Volume"].rolling(window=20, min_periods=5).mean()
    else:
        vol_sma20 = pd.Series(index=norm_hist.index, dtype=float)

    trading_days = list(norm_hist.index)
    enriched_news: list[dict[str, Any]] = []

    for item in news_items:
        copied = dict(item)
        title = item.get("title", "")
        copied["sentiment"] = compute_headline_sentiment(title)

        # Determinar fecha de la noticia
        pub_date: pd.Timestamp | None = None
        ts = item.get("providerPublishTime")
        if ts is not None:
            try:
                pub_date = pd.to_datetime(ts, unit="s").normalize()
            except (ValueError, TypeError):
                pub_date = None

        if pub_date is None and item.get("published_at"):
            try:
                pub_date = pd.to_datetime(item["published_at"]).normalize()
            except (ValueError, TypeError):
                pub_date = None

        impact = None
        if pub_date is not None:
            # Buscar la sesión de negociación correspondiente (igual o la siguiente hábil)
            candidate_days = [d for d in trading_days if d >= pub_date]
            if candidate_days:
                session_date = candidate_days[0]
                idx_pos = trading_days.index(session_date)
                curr_row = norm_hist.iloc[idx_pos]

                prev_row = norm_hist.iloc[idx_pos - 1] if idx_pos > 0 else None
                close_curr = float(curr_row["Close"])
                open_curr = float(curr_row["Open"]) if "Open" in curr_row else close_curr

                if prev_row is not None:
                    prev_close = float(prev_row["Close"])
                    day_change_pct = round(((close_curr - prev_close) / prev_close) * 100, 2)
                    gap_pct = round(((open_curr - prev_close) / prev_close) * 100, 2)
                else:
                    day_change_pct = round(((close_curr - open_curr) / open_curr) * 100, 2) if open_curr else 0.0
                    gap_pct = 0.0

                vol_ratio = 1.0
                curr_vol = float(curr_row["Volume"]) if has_volume else 0.0
                mean_vol = float(vol_sma20.iloc[idx_pos]) if has_volume and not pd.isna(vol_sma20.iloc[idx_pos]) else 0.0
                if mean_vol > 0:
                    vol_ratio = round(curr_vol / mean_vol, 2)

                impact = {
                    "session_date": session_date.strftime("%Y-%m-%d"),
                    "day_change_pct": day_change_pct,
                    "gap_pct": gap_pct,
                    "volume": int(curr_vol),
                    "volume_ratio": vol_ratio,
                    "abnormal_volume": vol_ratio >= 1.5,
                }

        copied["market_impact"] = impact
        enriched_news.append(copied)

    return enriched_news


def analyze_earnings_impact(
    earnings_df: pd.DataFrame | None,
    hist: pd.DataFrame,
    limit: int = 4,
) -> list[dict[str, Any]]:
    """
    Analiza los reportes trimestrales de resultados (EPS estimado vs real y sorpresa %)
    y mide la reacción del precio en cada fecha de balance.
    """
    if earnings_df is None or earnings_df.empty:
        return []

    norm_hist = _normalize_index_dates(hist)
    trading_days = list(norm_hist.index)
    records: list[dict[str, Any]] = []

    # Iterar sobre filas de earnings_df (usualmente ordenadas de más reciente a más antigua)
    for idx, row in earnings_df.iterrows():
        # Fecha puede venir como índice o columna
        date_val = idx if isinstance(idx, (pd.Timestamp, datetime)) else row.get("Date") or row.get("Earnings Date")
        if date_val is None:
            continue

        try:
            date_ts = pd.to_datetime(date_val)
            if hasattr(date_ts, "tz") and date_ts.tz is not None:
                date_ts = date_ts.tz_localize(None)
            date_norm = date_ts.normalize()
        except (ValueError, TypeError):
            continue

        reported_eps = row.get("Reported EPS")
        reported_eps_val = float(reported_eps) if reported_eps is not None and not pd.isna(reported_eps) else None

        eps_est = row.get("EPS Estimate")
        eps_est_val = float(eps_est) if eps_est is not None and not pd.isna(eps_est) else None

        surprise = row.get("Surprise(%)") or row.get("Surprise")
        surprise_val = float(surprise) if surprise is not None and not pd.isna(surprise) else None

        # Reacción de mercado
        price_reaction = None
        if not norm_hist.empty:
            matches = [d for d in trading_days if d >= date_norm]
            if matches:
                session_day = matches[0]
                pos = trading_days.index(session_day)
                curr = norm_hist.iloc[pos]
                prev = norm_hist.iloc[pos - 1] if pos > 0 else None
                close_val = float(curr["Close"])
                if prev is not None:
                    prev_close = float(prev["Close"])
                    reaction_pct = round(((close_val - prev_close) / prev_close) * 100, 2)
                else:
                    open_val = float(curr["Open"]) if "Open" in curr else close_val
                    reaction_pct = round(((close_val - open_val) / open_val) * 100, 2) if open_val else 0.0

                vol_ratio = 1.0
                if "Volume" in norm_hist.columns:
                    vol_s = norm_hist["Volume"].rolling(20, min_periods=5).mean()
                    mean_v = float(vol_s.iloc[pos]) if not pd.isna(vol_s.iloc[pos]) else 0.0
                    curr_v = float(curr["Volume"])
                    if mean_v > 0:
                        vol_ratio = round(curr_v / mean_v, 2)

                price_reaction = {
                    "session_date": session_day.strftime("%Y-%m-%d"),
                    "reaction_pct": reaction_pct,
                    "volume_ratio": vol_ratio,
                    "abnormal_volume": vol_ratio >= 1.5,
                }

        records.append({
            "date": date_norm.strftime("%Y-%m-%d"),
            "reported_eps": reported_eps_val,
            "eps_estimate": eps_est_val,
            "surprise_pct": round(surprise_val, 2) if surprise_val is not None else None,
            "market_reaction": price_reaction,
        })
        if len(records) >= limit:
            break

    return records


def parse_upcoming_events(calendar_data: Any) -> dict[str, Any]:
    """
    Normaliza el calendario corporativo entregado por yfinance (próximo reporte de utilidades,
    fechas de dividendos y previsiones de ingresos).
    """
    if not calendar_data:
        return {}

    parsed: dict[str, Any] = {
        "earnings_date": None,
        "ex_dividend_date": None,
        "dividend_date": None,
        "earnings_average": None,
        "revenue_average": None,
    }

    # Puede ser un dict o un DataFrame
    if isinstance(calendar_data, pd.DataFrame):
        data = calendar_data.to_dict()
    elif isinstance(calendar_data, dict):
        data = calendar_data
    else:
        return parsed

    # 1. Earnings Date
    ed = data.get("Earnings Date")
    if isinstance(ed, (list, tuple)) and ed:
        first = ed[0]
        parsed["earnings_date"] = str(first)
    elif ed is not None:
        parsed["earnings_date"] = str(ed)

    # 2. Ex-Dividend Date
    ex_div = data.get("Ex-Dividend Date")
    if ex_div is not None:
        parsed["ex_dividend_date"] = str(ex_div)

    # 3. Dividend Date
    div_date = data.get("Dividend Date")
    if div_date is not None:
        parsed["dividend_date"] = str(div_date)

    # 4. Averages
    ea = data.get("Earnings Average")
    if ea is not None and not (isinstance(ea, float) and np.isnan(ea)):
        try:
            parsed["earnings_average"] = round(float(ea), 2)
        except (ValueError, TypeError):
            pass

    ra = data.get("Revenue Average")
    if ra is not None and not (isinstance(ra, float) and np.isnan(ra)):
        try:
            parsed["revenue_average"] = float(ra)
        except (ValueError, TypeError):
            pass

    return parsed
