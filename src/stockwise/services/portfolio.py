"""
Servicio para la descarga sincronizada de precios, carga de cestas de inversión
y orquestación de optimización de carteras.
"""

from __future__ import annotations

import io

import pandas as pd
import yfinance as yf

from stockwise.analytics.portfolio import optimize_portfolio
from stockwise.domain.markets import resolve_ticker
from stockwise.domain.portfolio import OptimizationObjective, PortfolioOptimizationResult


def fetch_portfolio_price_history(
    tickers: list[str],
    period: str = "2y",
) -> pd.DataFrame:
    """
    Descarga y sincroniza las series temporales de cierre ajustado para una lista de tickers.
    Alinea las fechas comunes entre los activos.
    """
    clean_tickers = [resolve_ticker(t) for t in tickers if t.strip()]
    clean_tickers = list(dict.fromkeys(clean_tickers))

    if not clean_tickers:
        return pd.DataFrame()

    series_dict: dict[str, pd.Series] = {}
    for sym in clean_tickers:
        try:
            stock = yf.Ticker(sym)
            h = stock.history(period=period, interval="1d")
            if not h.empty and "Close" in h.columns:
                s = h["Close"].copy()
                if isinstance(s.index, pd.DatetimeIndex) and s.index.tz is not None:
                    s.index = s.index.tz_localize(None)
                s.index = pd.DatetimeIndex(s.index).normalize()
                series_dict[sym] = s[~s.index.duplicated(keep="last")]
        except Exception:
            continue

    if not series_dict:
        return pd.DataFrame()

    df = pd.DataFrame(series_dict)
    # Filtrar solo fechas donde todos los activos tengan cotización
    df = df.dropna(how="any").sort_index()
    return df


def parse_portfolio_basket_file(file_content: bytes | str) -> list[tuple[str, float]]:
    """
    Parsea un archivo CSV o TXT subido por el usuario con su cesta de activos.
    Formatos soportados:
    1. CSV con columnas: Ticker, Peso (o Symbol, Weight / Cantidad)
    2. Texto plano con lista de tickers separados por comas o saltos de línea.
    """
    if isinstance(file_content, bytes):
        text = file_content.decode("utf-8", errors="ignore")
    else:
        text = str(file_content)

    items: list[tuple[str, float]] = []

    # Probar lectura tabular CSV
    try:
        csv_df = pd.read_csv(io.StringIO(text))
        cols_lower = [str(c).lower().strip() for c in csv_df.columns]

        ticker_col = None
        weight_col = None

        for idx, c in enumerate(cols_lower):
            if c in ("ticker", "symbol", "simbolo", "activo", "asset"):
                ticker_col = csv_df.columns[idx]
            elif c in ("weight", "peso", "ponderacion", "shares", "monto", "value", "cantidad"):
                weight_col = csv_df.columns[idx]

        if ticker_col is not None:
            for _, row in csv_df.iterrows():
                t = str(row[ticker_col]).strip().upper()
                if not t or t == "NAN":
                    continue
                w = 1.0
                if weight_col is not None:
                    try:
                        w = float(row[weight_col])
                    except (ValueError, TypeError):
                        w = 1.0
                items.append((resolve_ticker(t), max(w, 0.0)))
            if items:
                return items
    except Exception:
        pass

    # Respaldo: lectura de texto plano línea a línea o por comas
    lines = text.replace(",", "\n").splitlines()
    for line in lines:
        cleaned = line.strip().upper()
        if cleaned and not cleaned.startswith("#"):
            parts = cleaned.split()
            sym = parts[0]
            val = float(parts[1]) if len(parts) > 1 and parts[1].replace(".", "", 1).isdigit() else 1.0
            items.append((resolve_ticker(sym), val))

    return items


def optimize_portfolio_basket(
    tickers: list[str],
    objective: str = "max_sharpe",
    period: str = "2y",
    risk_free_rate: float = 0.045,
    max_weight: float = 1.0,
    min_weight: float = 0.0,
    prices_df: pd.DataFrame | None = None,
    currency: str = "USD",
) -> PortfolioOptimizationResult:
    """
    Servicio de alto nivel para optimizar una cesta de activos bursátiles.
    Si prices_df no es provisto, descarga automáticamente las series sincronizadas.
    """
    if prices_df is None or prices_df.empty:
        prices_df = fetch_portfolio_price_history(tickers, period=period)

    if prices_df.empty or prices_df.shape[1] < 2:
        raise ValueError("Se requieren al menos 2 activos con cotizaciones históricas comunes para optimizar.")

    obj_enum = OptimizationObjective(objective.lower())

    return optimize_portfolio(
        prices=prices_df,
        objective=obj_enum,
        risk_free_rate=risk_free_rate,
        max_weight=max_weight,
        min_weight=min_weight,
        currency=currency,
    )
