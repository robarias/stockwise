"""
Métricas de riesgo y rendimiento: retorno acumulado, volatilidad anualizada, drawdown,
retornos por periodo y modelado heterocedástico GARCH con VaR/CVaR condicional.
"""

from typing import Any

import numpy as np
import pandas as pd

from stockwise.analytics.garch import calculate_garch_risk


def calculate_risk_metrics(df: pd.DataFrame) -> dict[str, Any]:
    """
    Calcula métricas de volatilidad y riesgo basadas en rendimientos diarios,
    complementadas con modelado condicional GARCH, VaR y Expected Shortfall.
    """
    if df.empty or len(df) < 5:
        raise ValueError("Se requieren más datos para calcular métricas de riesgo.")

    close = df["Close"]
    daily_returns = close.pct_change().dropna()

    if daily_returns.empty:
        return {}

    # Retorno acumulado en el periodo
    initial_price = float(close.iloc[0])
    final_price = float(close.iloc[-1])
    cumulative_return = ((final_price - initial_price) / initial_price) * 100

    # Volatilidad anualizada (asumiendo 252 días de trading al año)
    daily_std = daily_returns.std()
    annualized_volatility = float(daily_std * np.sqrt(252)) * 100

    # Máximo Drawdown (MDD)
    cummax = close.cummax()
    drawdown = (close - cummax) / cummax
    max_drawdown = float(drawdown.min()) * 100

    # Retornos periódicos
    def get_period_return(n_days: int) -> float | None:
        if len(close) > n_days:
            start_p = float(close.iloc[-(n_days + 1)])
            return round(((final_price - start_p) / start_p) * 100, 2)
        return None

    returns_breakdown = {
        "1_week_pct": get_period_return(5),
        "1_month_pct": get_period_return(21),
        "3_months_pct": get_period_return(63),
        "6_months_pct": get_period_return(126),
        "1_year_pct": get_period_return(252),
    }

    # Modelado GARCH / VaR condicional si hay suficiente historial
    conditional_risk: dict[str, Any] | None = None
    garch_full: dict[str, Any] | None = None
    if len(close.dropna()) >= 40:
        try:
            garch_full = calculate_garch_risk(df, horizon=30)
            conditional_risk = garch_full["summary"]
        except Exception:
            pass

    return {
        "period_start_price": round(initial_price, 2),
        "period_end_price": round(final_price, 2),
        "cumulative_return_pct": round(cumulative_return, 2),
        "annualized_volatility_pct": round(annualized_volatility, 2),
        "max_drawdown_pct": round(max_drawdown, 2),
        "returns_breakdown": returns_breakdown,
        "conditional_risk": conditional_risk,
        "_garch_full": garch_full,
    }
