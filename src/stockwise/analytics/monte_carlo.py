"""
Simulación Monte Carlo (Movimiento Browniano Geométrico - GBM) para series de precios.

Genera trayectorias probabilísticas para estimar percentiles de precio futuro,
probabilidades de ganancia/pérdida y probabilidades de toque de niveles clave de soporte
y resistencia a lo largo del horizonte proyectado.
"""

from typing import Any

import numpy as np
import pandas as pd

MIN_OBSERVATIONS_MC = 30


def _extract_close(data: pd.Series | pd.DataFrame) -> pd.Series:
    """Extrae y valida una serie de precios de cierre limpia y estrictamente positiva."""
    if isinstance(data, pd.DataFrame):
        if "Close" not in data.columns:
            raise ValueError("El DataFrame debe contener la columna 'Close'.")
        s = data["Close"].astype(float).dropna()
    elif isinstance(data, pd.Series):
        s = data.astype(float).dropna()
    else:
        raise TypeError("Los datos deben ser un pd.Series o pd.DataFrame.")

    s = s[s > 0]
    if isinstance(s.index, pd.DatetimeIndex) and s.index.tz is not None:
        s.index = s.index.tz_localize(None)
    s.index = pd.DatetimeIndex(s.index).normalize()
    s = s[~s.index.duplicated(keep="last")].sort_index()
    if len(s) < MIN_OBSERVATIONS_MC:
        raise ValueError(
            f"Se requieren al menos {MIN_OBSERVATIONS_MC} observaciones para Monte Carlo; hay {len(s)}."
        )
    return s


def simulate_monte_carlo(
    data: pd.Series | pd.DataFrame,
    horizon: int = 30,
    n_simulations: int = 2000,
    support_price: float | None = None,
    resistance_price: float | None = None,
    seed: int | None = 42,
) -> dict[str, Any]:
    """
    Simula `n_simulations` trayectorias de precios usando Movimiento Browniano Geométrico (GBM).

    Args:
        data: Serie o DataFrame con precios de cierre históricos.
        horizon: Ruedas futuras a proyectar (1 a 252).
        n_simulations: Cantidad de trayectorias a simular (por defecto 2000).
        support_price: Precio de soporte a evaluar (si es None, usa el mínimo reciente).
        resistance_price: Precio de resistencia a evaluar (si es None, usa el máximo reciente).
        seed: Semilla aleatoria para resultados reproducibles (None para aleatorio).

    Returns:
        Diccionario con métricas agregadas, probabilidades de eventos, percentiles
        y un DataFrame 'fan_chart' con la evolución temporal de percentiles.
    """
    if not 1 <= horizon <= 252:
        raise ValueError("`horizon` debe estar entre 1 y 252 ruedas.")
    if n_simulations < 100:
        raise ValueError("`n_simulations` debe ser al menos 100.")

    close = _extract_close(data)
    s0 = float(close.iloc[-1])

    # Rendimientos logarítmicos diarios
    log_returns = np.diff(np.log(close.values))
    # Considera hasta las últimas 252 ruedas para capturar la volatilidad reciente
    recent_returns = log_returns[-252:] if len(log_returns) >= 252 else log_returns

    mu = float(np.mean(recent_returns))
    sigma = float(np.std(recent_returns, ddof=1))
    if sigma <= 1e-7:
        sigma = 1e-4

    # Corrección de Ito para deriva en GBM: nu = mu - 0.5 * sigma^2
    nu = mu - 0.5 * (sigma**2)

    # Simulación vectorizada de trayectorias
    rng = np.random.default_rng(seed)
    shocks = rng.normal(0.0, 1.0, size=(n_simulations, horizon))
    cum_shocks = np.cumsum(shocks, axis=1)
    time_steps = np.arange(1, horizon + 1)

    log_paths = np.log(s0) + nu * time_steps + sigma * cum_shocks
    sim_paths = np.exp(log_paths)  # shape: (n_simulations, horizon)
    full_paths = np.column_stack([np.full(n_simulations, s0), sim_paths])

    # Fechas futuras hábiles
    last_date = close.index[-1]
    future_dates = pd.bdate_range(start=last_date + pd.Timedelta(days=1), periods=horizon)

    # Niveles de soporte y resistencia (efectivos y marcados si son automáticos)
    lookback = min(len(close), 60)
    recent_window = close.iloc[-lookback:]
    support_is_auto = support_price is None
    resistance_is_auto = resistance_price is None

    effective_support = float(support_price) if support_price is not None else float(recent_window.min())
    effective_resistance = float(resistance_price) if resistance_price is not None else float(recent_window.max())

    # Trayectoria completa: tocar niveles durante la vigencia del horizonte
    min_along_path = np.min(full_paths, axis=1)
    max_along_path = np.max(full_paths, axis=1)
    prob_touch_support = float(np.mean(min_along_path <= effective_support) * 100)
    prob_touch_resistance = float(np.mean(max_along_path >= effective_resistance) * 100)

    # Precios al final del horizonte
    end_prices = sim_paths[:, -1]
    prob_gain = float(np.mean(end_prices > s0) * 100)
    prob_loss = float(np.mean(end_prices < s0) * 100)
    prob_gain_5pct = float(np.mean(end_prices >= s0 * 1.05) * 100)
    prob_gain_10pct = float(np.mean(end_prices >= s0 * 1.10) * 100)
    prob_loss_5pct = float(np.mean(end_prices <= s0 * 0.95) * 100)
    prob_loss_10pct = float(np.mean(end_prices <= s0 * 0.90) * 100)
    prob_end_below_support = float(np.mean(end_prices <= effective_support) * 100)
    prob_end_above_resistance = float(np.mean(end_prices >= effective_resistance) * 100)

    # Fan chart (evolución temporal de percentiles)
    fan_chart = pd.DataFrame(
        {
            "p5": np.percentile(sim_paths, 5, axis=0),
            "p10": np.percentile(sim_paths, 10, axis=0),
            "p25": np.percentile(sim_paths, 25, axis=0),
            "p50": np.percentile(sim_paths, 50, axis=0),
            "p75": np.percentile(sim_paths, 75, axis=0),
            "p90": np.percentile(sim_paths, 90, axis=0),
            "p95": np.percentile(sim_paths, 95, axis=0),
            "mean": np.mean(sim_paths, axis=0),
        },
        index=future_dates,
    )

    percentiles_end = {
        "p5": round(float(np.percentile(end_prices, 5)), 2),
        "p10": round(float(np.percentile(end_prices, 10)), 2),
        "p25": round(float(np.percentile(end_prices, 25)), 2),
        "p50": round(float(np.percentile(end_prices, 50)), 2),
        "p75": round(float(np.percentile(end_prices, 75)), 2),
        "p90": round(float(np.percentile(end_prices, 90)), 2),
        "p95": round(float(np.percentile(end_prices, 95)), 2),
    }

    summary = {
        "n_simulations": int(n_simulations),
        "horizon_days": int(horizon),
        "last_price": round(s0, 2),
        "drift_annualized_pct": round(float(mu * 252 * 100), 2),
        "volatility_annualized_pct": round(float(sigma * np.sqrt(252) * 100), 2),
        "expected_price_mean": round(float(np.mean(end_prices)), 2),
        "expected_price_median": round(float(np.median(end_prices)), 2),
        "percentiles_end": percentiles_end,
        "probabilities": {
            "prob_gain_pct": round(prob_gain, 1),
            "prob_loss_pct": round(prob_loss, 1),
            "prob_gain_5pct": round(prob_gain_5pct, 1),
            "prob_gain_10pct": round(prob_gain_10pct, 1),
            "prob_loss_5pct": round(prob_loss_5pct, 1),
            "prob_loss_10pct": round(prob_loss_10pct, 1),
        },
        "support_analysis": {
            "price": round(effective_support, 2),
            "is_auto": support_is_auto,
            "prob_touch_during_horizon_pct": round(prob_touch_support, 1),
            "prob_end_below_pct": round(prob_end_below_support, 1),
        },
        "resistance_analysis": {
            "price": round(effective_resistance, 2),
            "is_auto": resistance_is_auto,
            "prob_touch_during_horizon_pct": round(prob_touch_resistance, 1),
            "prob_end_above_pct": round(prob_end_above_resistance, 1),
        },
    }

    return {
        **summary,
        "fan_chart": fan_chart,
        "summary": summary,
    }
