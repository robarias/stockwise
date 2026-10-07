"""
Indicadores técnicos (SMA, EMA, RSI, MACD, Bollinger) e interpretación de señales.
Funciones puras sobre DataFrames OHLCV: sin red ni E/S.
"""

from typing import Any

import numpy as np
import pandas as pd


def calculate_technical_indicators(df: pd.DataFrame) -> dict[str, Any]:
    """
    Calcula indicadores técnicos a partir de un DataFrame con velas históricas (OHLCV).
    Requiere al menos la columna 'Close'.
    """
    if df.empty or len(df) < 15:
        raise ValueError("Se requieren al menos 15 registros históricos para calcular indicadores técnicos.")

    close = df["Close"]
    latest_close = float(close.iloc[-1])

    # 1. Medias Móviles Simples (SMA) y Exponenciales (EMA)
    sma_20 = float(close.rolling(window=20).mean().iloc[-1]) if len(close) >= 20 else None
    sma_50 = float(close.rolling(window=50).mean().iloc[-1]) if len(close) >= 50 else None
    sma_200 = float(close.rolling(window=200).mean().iloc[-1]) if len(close) >= 200 else None
    ema_20 = float(close.ewm(span=20, adjust=False).mean().iloc[-1]) if len(close) >= 20 else None

    # 2. RSI (Relative Strength Index con suavizado Wilder, periodo 14)
    delta = close.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.ewm(alpha=1/14, min_periods=14, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1/14, min_periods=14, adjust=False).mean()
    rs = avg_gain / avg_loss.replace(0, np.nan)
    rsi_series = 100 - (100 / (1 + rs))
    # En tendencia alcista pura sin pérdidas, RSI es 100; si no hay variación, 50
    rsi_series = rsi_series.where(~((avg_loss == 0) & (avg_gain > 0)), 100.0)
    rsi_series = rsi_series.where(~((avg_loss == 0) & (avg_gain == 0)), 50.0)
    current_rsi = float(rsi_series.iloc[-1]) if not pd.isna(rsi_series.iloc[-1]) else 50.0

    # 3. MACD (12, 26, 9)
    ema_12 = close.ewm(span=12, adjust=False).mean()
    ema_26 = close.ewm(span=26, adjust=False).mean()
    macd_line = ema_12 - ema_26
    signal_line = macd_line.ewm(span=9, adjust=False).mean()
    macd_hist = macd_line - signal_line

    curr_macd = float(macd_line.iloc[-1])
    curr_signal = float(signal_line.iloc[-1])
    curr_hist = float(macd_hist.iloc[-1])

    # 4. Bandas de Bollinger (periodo 20, 2 desviaciones estándar)
    bb_sma20 = close.rolling(window=20).mean()
    bb_std20 = close.rolling(window=20).std()
    bb_upper = bb_sma20 + (2 * bb_std20)
    bb_lower = bb_sma20 - (2 * bb_std20)

    upper_val = float(bb_upper.iloc[-1]) if len(close) >= 20 else None
    lower_val = float(bb_lower.iloc[-1]) if len(close) >= 20 else None
    bb_pct_b = (
        float((latest_close - lower_val) / (upper_val - lower_val))
        if upper_val and lower_val and (upper_val != lower_val)
        else None
    )

    # 5. Interpretación de señales
    signals: list[str] = []

    # RSI
    if current_rsi >= 70:
        rsi_status = "SOBRECOMPRA (Posible corrección a la baja)"
        signals.append("RSI > 70 indica condición de sobrecompra.")
    elif current_rsi <= 30:
        rsi_status = "SOBREVENTA (Posible rebote al alza)"
        signals.append("RSI < 30 indica condición de sobreventa.")
    else:
        rsi_status = "NEUTRAL"

    # MACD
    if curr_macd > curr_signal:
        macd_status = "ALCISTA (Línea MACD por encima de Señal)"
    else:
        macd_status = "BAJISTA (Línea MACD por debajo de Señal)"

    # Tendencia vs Medias Móviles
    trend_signals = []
    if sma_50 and latest_close > sma_50:
        trend_signals.append("Precio sobre SMA 50 (Medio plazo alcista)")
    elif sma_50:
        trend_signals.append("Precio bajo SMA 50 (Medio plazo bajista)")

    if sma_200 and latest_close > sma_200:
        trend_signals.append("Precio sobre SMA 200 (Largo plazo alcista)")
    elif sma_200:
        trend_signals.append("Precio bajo SMA 200 (Largo plazo bajista)")

    # Cruce Dorado / de la Muerte
    if sma_50 and sma_200:
        if sma_50 > sma_200:
            trend_signals.append("Alineación alcista: SMA 50 > SMA 200")
        else:
            trend_signals.append("Alineación bajista: SMA 50 < SMA 200")

    return {
        "current_price": round(latest_close, 2),
        "rsi_14": {
            "value": round(current_rsi, 2),
            "status": rsi_status
        },
        "macd": {
            "macd_line": round(curr_macd, 4),
            "signal_line": round(curr_signal, 4),
            "histogram": round(curr_hist, 4),
            "status": macd_status
        },
        "bollinger_bands_20_2": {
            "upper": round(upper_val, 2) if upper_val else None,
            "middle": round(sma_20, 2) if sma_20 else None,
            "lower": round(lower_val, 2) if lower_val else None,
            "percent_b": round(bb_pct_b, 4) if bb_pct_b is not None else None
        },
        "moving_averages": {
            "sma_20": round(sma_20, 2) if sma_20 else None,
            "sma_50": round(sma_50, 2) if sma_50 else None,
            "sma_200": round(sma_200, 2) if sma_200 else None,
            "ema_20": round(ema_20, 2) if ema_20 else None
        },
        "analysis_notes": signals + trend_signals
    }


def compute_indicator_series(df: pd.DataFrame) -> pd.DataFrame:
    """
    Series completas de indicadores (para graficar), con las mismas fórmulas que
    `calculate_technical_indicators`: SMA 20/50/200, EMA 20, Bollinger (20, 2), RSI 14 y MACD (12, 26, 9).
    """
    if df.empty or "Close" not in df.columns:
        raise ValueError("Se requiere un DataFrame con la columna 'Close'.")

    close = df["Close"]
    out = pd.DataFrame(index=df.index)
    out["close"] = close
    for n in (20, 50, 200):
        out[f"sma_{n}"] = close.rolling(window=n).mean()
    out["ema_20"] = close.ewm(span=20, adjust=False).mean()

    std20 = close.rolling(window=20).std()
    out["bb_upper"] = out["sma_20"] + 2 * std20
    out["bb_lower"] = out["sma_20"] - 2 * std20

    delta = close.diff()
    avg_gain = delta.clip(lower=0).ewm(alpha=1 / 14, min_periods=14, adjust=False).mean()
    avg_loss = (-delta.clip(upper=0)).ewm(alpha=1 / 14, min_periods=14, adjust=False).mean()
    rsi_s = 100 - (100 / (1 + avg_gain / avg_loss.replace(0, np.nan)))
    rsi_s = rsi_s.where(~((avg_loss == 0) & (avg_gain > 0)), 100.0)
    rsi_s = rsi_s.where(~((avg_loss == 0) & (avg_gain == 0)), 50.0)
    out["rsi_14"] = rsi_s

    ema_12 = close.ewm(span=12, adjust=False).mean()
    ema_26 = close.ewm(span=26, adjust=False).mean()
    out["macd"] = ema_12 - ema_26
    out["macd_signal"] = out["macd"].ewm(span=9, adjust=False).mean()
    out["macd_hist"] = out["macd"] - out["macd_signal"]
    return out
