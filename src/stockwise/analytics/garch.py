"""
Modelado de volatilidad heterocedástica condicional (GARCH / GJR-GARCH),
Value-at-Risk (VaR) paramétrico dinámico y Expected Shortfall (CVaR).
"""

import warnings
from typing import Any

import numpy as np
import pandas as pd
from arch import arch_model
from scipy.stats import norm

MIN_OBSERVATIONS_GARCH = 40


def _extract_returns(data: pd.Series | pd.DataFrame) -> tuple[pd.Series, pd.Series]:
    """
    Extrae serie de precios limpios y calcula rendimientos porcentuales diarios (100 * r_t).
    arch_model opera numéricamente mucho mejor con retornos en escala porcentual.
    """
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

    if len(s) < MIN_OBSERVATIONS_GARCH:
        raise ValueError(
            f"Se requieren al menos {MIN_OBSERVATIONS_GARCH} ruedas para modelado GARCH; hay {len(s)}."
        )

    # Retornos simples porcentuales
    returns_pct = (s.pct_change().dropna()) * 100.0
    return s, returns_pct


def calculate_garch_risk(
    data: pd.Series | pd.DataFrame,
    horizon: int = 30,
    leverage: bool = True,
) -> dict[str, Any]:
    """
    Ajusta un modelo GARCH(1,1) o GJR-GARCH(1,1,1) para estimar:
      - Volatilidad condicional histórica e instantánea (actual).
      - Régimen de volatilidad (Baja, Normal, Estrés).
      - Estructura temporal proyectada de volatilidad para `horizon` ruedas.
      - Value-at-Risk (VaR) condicional al 95% y 99% a 1 día y a horizonte completo.
      - Expected Shortfall (CVaR) condicional al 95% y 99%.
      - Bandas de precio condicionales heterocedásticas.

    Args:
        data: Precios de cierre históricos.
        horizon: Ruedas futuras a proyectar (1 a 252).
        leverage: Si es True, incluye término asimétrico GJR para capturar efecto apalancamiento.

    Returns:
        Diccionario con métricas agregadas, series temporales y resumen serializable.
    """
    if not 1 <= horizon <= 252:
        raise ValueError("`horizon` debe estar entre 1 y 252 ruedas.")

    close, ret_pct = _extract_returns(data)
    last_price = float(close.iloc[-1])

    # Intentar ajustar GJR-GARCH primero si leverage=True, o fallback a GARCH estándar
    configs = [(1, 1, "GJR-GARCH(1,1,1)")] if leverage else []
    configs.append((1, 0, "GARCH(1,1)"))

    res = None
    model_name = "GARCH(1,1)"

    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        for p, o, name in configs:
            try:
                am = arch_model(ret_pct, vol="Garch", p=p, o=o, q=1, mean="Constant", dist="normal")
                fitted = am.fit(disp="off", show_warning=False)
                if np.isfinite(fitted.aic) and np.isfinite(fitted.params.iloc[-1]):
                    res = fitted
                    model_name = name
                    break
            except Exception:
                continue

    if res is None:
        # Fallback analítico a volatilidad móvil empírica
        return _fallback_empirical_risk(close, ret_pct, horizon)

    # Volatilidad condicional en porcentaje diario y anualizado
    cond_vol_daily_pct = res.conditional_volatility  # escala en %
    cond_vol_annual_pct = cond_vol_daily_pct * np.sqrt(252)
    cond_vol_annual_pct.index = ret_pct.index

    current_vol_annual = float(cond_vol_annual_pct.iloc[-1])
    mean_vol_annual = float(cond_vol_annual_pct.mean())
    vol_ratio = current_vol_annual / mean_vol_annual if mean_vol_annual > 0 else 1.0

    # Clasificación de régimen
    if vol_ratio < 0.85:
        regime = "Baja volatilidad"
        regime_level = "low"
        regime_desc = "El activo se encuentra en un régimen de calma relativa o consolidación."
    elif vol_ratio <= 1.25:
        regime = "Volatilidad normal"
        regime_level = "normal"
        regime_desc = "El nivel de riesgo actual es coherente con su promedio histórico."
    else:
        regime = "Alta volatilidad / Estrés"
        regime_level = "high"
        regime_desc = "El activo experimenta turbulencia o presión de mercado superior a su media habitual."

    # Parámetros del modelo y persistencia
    params = {str(k): round(float(v), 6) for k, v in res.params.items()}
    alpha = float(params.get("alpha[1]", 0.0))
    beta = float(params.get("beta[1]", 0.0))
    gamma = float(params.get("gamma[1]", 0.0))
    persistence = alpha + beta + (0.5 * gamma)
    persistence = min(max(persistence, 0.0), 0.9999)

    half_life = float(np.log(0.5) / np.log(persistence)) if persistence < 1.0 else None

    # Pronóstico hacia adelante (multi-step forecast)
    fc = res.forecast(horizon=horizon)
    var_forecast_pct = fc.variance.dropna().values[0]  # varianzas en %^2
    vol_forecast_daily_pct = np.sqrt(var_forecast_pct)  # desv estándar diaria en %
    vol_forecast_annual_pct = vol_forecast_daily_pct * np.sqrt(252)

    projected_vol_mean_annual = float(np.mean(vol_forecast_annual_pct))

    # Pronóstico de media diaria
    mu_daily_pct = float(params.get("mu", 0.0))
    mu_daily_dec = mu_daily_pct / 100.0

    # 1-día adelante volatilidad (en escala decimal)
    sigma_1d_dec = float(vol_forecast_daily_pct[0]) / 100.0

    # Cuantiles normales estándar
    z95 = float(norm.ppf(0.05))  # ~ -1.6449
    z99 = float(norm.ppf(0.01))  # ~ -2.3263

    # VaR Condicional a 1 día (porcentaje de retorno; valor negativo representa pérdida)
    var_95_1d = (mu_daily_dec + z95 * sigma_1d_dec) * 100.0
    var_99_1d = (mu_daily_dec + z99 * sigma_1d_dec) * 100.0

    # Expected Shortfall (CVaR) a 1 día
    # ES = mu - sigma * (phi(z) / alpha)
    es_factor_95 = norm.pdf(z95) / 0.05
    es_factor_99 = norm.pdf(z99) / 0.01
    cvar_95_1d = (mu_daily_dec - sigma_1d_dec * es_factor_95) * 100.0
    cvar_99_1d = (mu_daily_dec - sigma_1d_dec * es_factor_99) * 100.0

    # VaR y CVaR sobre el horizonte acumulado
    cum_var_dec = float(np.sum(var_forecast_pct) / 10000.0)
    sigma_horizon_dec = np.sqrt(cum_var_dec)
    mu_horizon_dec = mu_daily_dec * horizon

    var_95_horizon = (mu_horizon_dec + z95 * sigma_horizon_dec) * 100.0
    var_99_horizon = (mu_horizon_dec + z99 * sigma_horizon_dec) * 100.0
    cvar_95_horizon = (mu_horizon_dec - sigma_horizon_dec * es_factor_95) * 100.0
    cvar_99_horizon = (mu_horizon_dec - sigma_horizon_dec * es_factor_99) * 100.0

    # Fechas futuras hábiles para series proyectadas
    future_dates = pd.bdate_range(start=close.index[-1] + pd.Timedelta(days=1), periods=horizon)
    vol_forecast_series = pd.Series(vol_forecast_annual_pct, index=future_dates)

    # Bandas de precio condicionales heterocedásticas GARCH (cono del 95%)
    cum_stds_dec = np.sqrt(np.cumsum(var_forecast_pct) / 10000.0)
    step_drifts = mu_daily_dec * np.arange(1, horizon + 1)
    upper_prices = last_price * np.exp(step_drifts + 1.96 * cum_stds_dec)
    lower_prices = last_price * np.exp(step_drifts - 1.96 * cum_stds_dec)
    mean_prices = last_price * np.exp(step_drifts)

    garch_bands = pd.DataFrame(
        {"mean": mean_prices, "lower": lower_prices, "upper": upper_prices},
        index=future_dates,
    )

    summary = {
        "converged": True,
        "model": model_name,
        "current_volatility_annualized_pct": round(current_vol_annual, 2),
        "historical_mean_volatility_annualized_pct": round(mean_vol_annual, 2),
        "volatility_ratio": round(vol_ratio, 2),
        "volatility_regime": regime,
        "regime_level": regime_level,
        "regime_description": regime_desc,
        "persistence": round(persistence, 4),
        "half_life_days": round(half_life, 1) if half_life is not None else None,
        "projected_volatility_30d_annualized_pct": round(projected_vol_mean_annual, 2),
        "var_metrics": {
            "var_95_1d_pct": round(var_95_1d, 2),
            "var_99_1d_pct": round(var_99_1d, 2),
            "cvar_95_1d_pct": round(cvar_95_1d, 2),
            "cvar_99_1d_pct": round(cvar_99_1d, 2),
            "var_95_horizon_pct": round(var_95_horizon, 2),
            "var_99_horizon_pct": round(var_99_horizon, 2),
            "cvar_95_horizon_pct": round(cvar_95_horizon, 2),
            "cvar_99_horizon_pct": round(cvar_99_horizon, 2),
            "horizon_days": int(horizon),
        },
        "parameters": params,
    }

    return {
        **summary,
        "conditional_volatility_series": cond_vol_annual_pct,
        "volatility_forecast_series": vol_forecast_series,
        "garch_bands": garch_bands,
        "summary": summary,
    }


def _fallback_empirical_risk(
    close: pd.Series, ret_pct: pd.Series, horizon: int
) -> dict[str, Any]:
    """Fallback seguro si el estimador de máxima verosimilitud de GARCH no converge."""
    last_price = float(close.iloc[-1])
    # Volatilidad rodante de 20 ruedas
    roll_vol_annual = (ret_pct.rolling(window=min(len(ret_pct), 20), min_periods=5).std()) * np.sqrt(252)
    current_vol = float(roll_vol_annual.iloc[-1]) if not roll_vol_annual.dropna().empty else 20.0
    mean_vol = float(ret_pct.std() * np.sqrt(252))

    sigma_1d_dec = (current_vol / np.sqrt(252)) / 100.0
    mu_dec = float(ret_pct.mean()) / 100.0

    z95, z99 = float(norm.ppf(0.05)), float(norm.ppf(0.01))
    es95 = norm.pdf(z95) / 0.05
    es99 = norm.pdf(z99) / 0.01

    future_dates = pd.bdate_range(start=close.index[-1] + pd.Timedelta(days=1), periods=horizon)
    cum_std = sigma_1d_dec * np.sqrt(np.arange(1, horizon + 1))
    step_drifts = mu_dec * np.arange(1, horizon + 1)

    garch_bands = pd.DataFrame(
        {
            "mean": last_price * np.exp(step_drifts),
            "lower": last_price * np.exp(step_drifts - 1.96 * cum_std),
            "upper": last_price * np.exp(step_drifts + 1.96 * cum_std),
        },
        index=future_dates,
    )

    summary = {
        "converged": False,
        "model": "Empírico (Fallback)",
        "current_volatility_annualized_pct": round(current_vol, 2),
        "historical_mean_volatility_annualized_pct": round(mean_vol, 2),
        "volatility_ratio": round(current_vol / mean_vol, 2) if mean_vol > 0 else 1.0,
        "volatility_regime": "Volatilidad normal",
        "regime_level": "normal",
        "regime_description": "Estimación empírica rodante por falta de convergencia MLE.",
        "persistence": None,
        "half_life_days": None,
        "projected_volatility_30d_annualized_pct": round(current_vol, 2),
        "var_metrics": {
            "var_95_1d_pct": round((mu_dec + z95 * sigma_1d_dec) * 100.0, 2),
            "var_99_1d_pct": round((mu_dec + z99 * sigma_1d_dec) * 100.0, 2),
            "cvar_95_1d_pct": round((mu_dec - sigma_1d_dec * es95) * 100.0, 2),
            "cvar_99_1d_pct": round((mu_dec - sigma_1d_dec * es99) * 100.0, 2),
            "var_95_horizon_pct": round((mu_dec * horizon + z95 * sigma_1d_dec * np.sqrt(horizon)) * 100.0, 2),
            "var_99_horizon_pct": round((mu_dec * horizon + z99 * sigma_1d_dec * np.sqrt(horizon)) * 100.0, 2),
            "cvar_95_horizon_pct": round((mu_dec * horizon - sigma_1d_dec * np.sqrt(horizon) * es95) * 100.0, 2),
            "cvar_99_horizon_pct": round((mu_dec * horizon - sigma_1d_dec * np.sqrt(horizon) * es99) * 100.0, 2),
            "horizon_days": int(horizon),
        },
        "parameters": {},
    }

    return {
        **summary,
        "conditional_volatility_series": roll_vol_annual.dropna(),
        "volatility_forecast_series": pd.Series(current_vol, index=future_dates),
        "garch_bands": garch_bands,
        "summary": summary,
    }
