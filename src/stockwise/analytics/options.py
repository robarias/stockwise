"""
Modelado analítico de opciones financieras: Black-Scholes-Merton, Griegas,
calibración de volatilidad implícita y construcción de superficies de volatilidad.
"""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd
from scipy.interpolate import griddata
from scipy.optimize import brentq
from scipy.stats import norm

from stockwise.domain.options import (
    BlackScholesResult,
    GreeksResult,
    IVSurfaceData,
    OptionType,
)


# ---------------------------------------------------------------------------
# Fórmulas Analíticas de Black-Scholes-Merton (1973)
# ---------------------------------------------------------------------------
def _compute_d1_d2(
    s: float | np.ndarray,
    k: float | np.ndarray,
    t: float | np.ndarray,
    r: float,
    sigma: float | np.ndarray,
    q: float = 0.0,
) -> tuple[float | np.ndarray, float | np.ndarray]:
    """Calcula d1 y d2 para las fórmulas de Black-Scholes."""
    sigma_adj = np.maximum(sigma, 1e-6)
    t_adj = np.maximum(t, 1e-6)
    sqrt_t = np.sqrt(t_adj)

    d1 = (np.log(s / k) + (r - q + 0.5 * sigma_adj**2) * t_adj) / (sigma_adj * sqrt_t)
    d2 = d1 - sigma_adj * sqrt_t
    return d1, d2


def black_scholes_price(
    spot: float | np.ndarray,
    strike: float | np.ndarray,
    time_years: float | np.ndarray,
    risk_free_rate: float,
    volatility: float | np.ndarray,
    dividend_yield: float = 0.0,
    option_type: OptionType | str = OptionType.CALL,
) -> float | np.ndarray:
    """
    Calcula el precio teórico de una opción europea usando Black-Scholes-Merton.
    Soporta entradas escalares y arreglos NumPy para vectorización de alto rendimiento.
    """
    s = np.asarray(spot, dtype=float)
    k = np.asarray(strike, dtype=float)
    t = np.asarray(time_years, dtype=float)
    sig = np.asarray(volatility, dtype=float)
    r = float(risk_free_rate)
    q = float(dividend_yield)

    is_call = OptionType(option_type) == OptionType.CALL

    # Caso límite de vencimiento inmediato (T <= 0)
    intrinsic = np.maximum(s - k, 0.0) if is_call else np.maximum(k - s, 0.0)
    mask_zero_t = t <= 1e-6

    d1, d2 = _compute_d1_d2(s, k, t, r, sig, q)

    df_q = np.exp(-q * t)
    df_r = np.exp(-r * t)

    if is_call:
        price = s * df_q * norm.cdf(d1) - k * df_r * norm.cdf(d2)
    else:
        price = k * df_r * norm.cdf(-d2) - s * df_q * norm.cdf(-d1)

    price = np.where(mask_zero_t, intrinsic, price)
    price = np.maximum(price, 0.0)

    if np.ndim(spot) == 0 and np.ndim(strike) == 0 and np.ndim(time_years) == 0 and np.ndim(volatility) == 0:
        return float(price)
    return price


def black_scholes_greeks(
    spot: float,
    strike: float,
    time_years: float,
    risk_free_rate: float,
    volatility: float,
    dividend_yield: float = 0.0,
    option_type: OptionType | str = OptionType.CALL,
) -> GreeksResult:
    """Calcula todas las griegas analíticas (Delta, Gamma, Theta, Vega, Rho)."""
    s = float(spot)
    k = float(strike)
    t = max(float(time_years), 1e-6)
    r = float(risk_free_rate)
    sig = max(float(volatility), 1e-6)
    q = float(dividend_yield)
    is_call = OptionType(option_type) == OptionType.CALL

    d1, d2 = _compute_d1_d2(s, k, t, r, sig, q)
    sqrt_t = np.sqrt(t)
    df_q = np.exp(-q * t)
    df_r = np.exp(-r * t)
    pdf_d1 = norm.pdf(d1)

    # 1. Delta
    if is_call:
        delta = float(df_q * norm.cdf(d1))
    else:
        delta = float(-df_q * norm.cdf(-d1))

    # 2. Gamma (idéntico para Call y Put)
    gamma = float((df_q * pdf_d1) / (s * sig * sqrt_t))

    # 3. Vega (idéntico para Call y Put, expresado anual y por 1% de volatilidad)
    vega_annual = float(s * df_q * pdf_d1 * sqrt_t)
    vega_1pct = vega_annual / 100.0

    # 4. Theta (expresado anual y diario dividiendo por 365)
    term1 = -(s * df_q * pdf_d1 * sig) / (2.0 * sqrt_t)
    if is_call:
        theta_annual = term1 + q * s * df_q * norm.cdf(d1) - r * k * df_r * norm.cdf(d2)
    else:
        theta_annual = term1 - q * s * df_q * norm.cdf(-d1) + r * k * df_r * norm.cdf(-d2)
    theta_daily = theta_annual / 365.0

    # 5. Rho (sensibilidad por 1% de tasa de interés)
    if is_call:
        rho_annual = k * t * df_r * norm.cdf(d2)
    else:
        rho_annual = -k * t * df_r * norm.cdf(-d2)
    rho_1pct = rho_annual / 100.0

    return GreeksResult(
        delta=delta,
        gamma=gamma,
        theta_daily=theta_daily,
        theta_annual=theta_annual,
        vega_1pct=vega_1pct,
        vega_annual=vega_annual,
        rho_1pct=rho_1pct,
    )


def evaluate_contract(
    spot: float,
    strike: float,
    dte_days: float,
    volatility: float,
    risk_free_rate: float = 0.045,
    dividend_yield: float = 0.0,
    option_type: OptionType | str = OptionType.CALL,
) -> BlackScholesResult:
    """Evalúa un contrato de opción completo devolviendo métricas de precio, valor temporal y griegas."""
    op_type = OptionType(option_type)
    t_years = max(float(dte_days), 0.0) / 365.0
    price = float(black_scholes_price(spot, strike, t_years, risk_free_rate, volatility, dividend_yield, op_type))

    # Valor intrínseco y temporal
    is_call = op_type == OptionType.CALL
    intrinsic = max(spot - strike, 0.0) if is_call else max(strike - spot, 0.0)
    time_val = max(price - intrinsic, 0.0)

    # Moneyness
    moneyness = strike / spot if spot > 0 else 1.0
    if is_call:
        if moneyness < 0.97:
            status = "ITM (In-The-Money)"
        elif moneyness <= 1.03:
            status = "ATM (At-The-Money)"
        else:
            status = "OTM (Out-of-The-Money)"
    else:
        if moneyness > 1.03:
            status = "ITM (In-The-Money)"
        elif moneyness >= 0.97:
            status = "ATM (At-The-Money)"
        else:
            status = "OTM (Out-of-The-Money)"

    greeks = black_scholes_greeks(spot, strike, t_years, risk_free_rate, volatility, dividend_yield, op_type)

    return BlackScholesResult(
        spot=spot,
        strike=strike,
        dte_days=dte_days,
        time_years=t_years,
        volatility_pct=volatility * 100.0,
        risk_free_rate_pct=risk_free_rate * 100.0,
        dividend_yield_pct=dividend_yield * 100.0,
        option_type=op_type,
        price=price,
        intrinsic_value=intrinsic,
        time_value=time_val,
        moneyness=moneyness,
        moneyness_status=status,
        greeks=greeks,
    )


# ---------------------------------------------------------------------------
# Calibración de Volatilidad Implícita (Inversión Numérica)
# ---------------------------------------------------------------------------
def implied_volatility(
    market_price: float,
    spot: float,
    strike: float,
    time_years: float,
    risk_free_rate: float,
    dividend_yield: float = 0.0,
    option_type: OptionType | str = OptionType.CALL,
) -> float | None:
    """
    Obtiene la volatilidad implícita dado el precio de mercado mediante Newton-Raphson
    con respaldo del método Brentq de SciPy.
    """
    if market_price <= 0.0001 or time_years <= 1e-5:
        return None

    op_type = OptionType(option_type)
    # Límite mínimo teórico (valor intrínseco descontado)
    df_q = np.exp(-dividend_yield * time_years)
    df_r = np.exp(-risk_free_rate * time_years)
    min_price = max(spot * df_q - strike * df_r, 0.0) if op_type == OptionType.CALL else max(strike * df_r - spot * df_q, 0.0)

    if market_price < min_price:
        return None

    def obj(sig: float) -> float:
        return float(black_scholes_price(spot, strike, time_years, risk_free_rate, sig, dividend_yield, op_type)) - market_price

    # 1. Newton-Raphson rápido (hasta 15 iteraciones)
    sigma = 0.25
    for _ in range(15):
        diff = obj(sigma)
        if abs(diff) < 1e-5:
            return round(sigma, 4)
        greeks = black_scholes_greeks(spot, strike, time_years, risk_free_rate, sigma, dividend_yield, op_type)
        vega = max(greeks.vega_annual, 1e-4)
        sigma -= diff / vega
        if sigma <= 0.001 or sigma >= 5.0:
            break

    # 2. Respaldo: Brentq robusto
    try:
        sol = brentq(obj, 0.001, 5.0, xtol=1e-5, maxiter=50)
        return round(float(sol), 4)
    except Exception:
        return None


# ---------------------------------------------------------------------------
# Matrices para Mapas de Calor 2D
# ---------------------------------------------------------------------------
def generate_pricing_heatmap_matrix(
    spot_base: float,
    dte_days: float = 30.0,
    volatility: float = 0.25,
    risk_free_rate: float = 0.045,
    dividend_yield: float = 0.0,
    n_points: int = 15,
    range_pct: float = 0.20,
) -> dict[str, Any]:
    """
    Genera matrices bidimensionales para mapas de calor:
    1. Spot vs Strike: Precio Call, Precio Put y Delta.
    2. Strike vs Volatilidad: Precio Call y Precio Put.
    """
    spot_min = spot_base * (1.0 - range_pct)
    spot_max = spot_base * (1.0 + range_pct)
    strike_min = spot_base * (1.0 - range_pct)
    strike_max = spot_base * (1.0 + range_pct)

    spots = np.linspace(spot_min, spot_max, n_points)
    strikes = np.linspace(strike_min, strike_max, n_points)
    vols = np.linspace(max(volatility * 0.5, 0.05), volatility * 2.0, n_points)

    t_years = max(float(dte_days), 1.0) / 365.0

    # 1. Matriz Spot vs Strike
    S_mesh, K_mesh = np.meshgrid(spots, strikes)
    calls_matrix = black_scholes_price(S_mesh, K_mesh, t_years, risk_free_rate, volatility, dividend_yield, OptionType.CALL)
    puts_matrix = black_scholes_price(S_mesh, K_mesh, t_years, risk_free_rate, volatility, dividend_yield, OptionType.PUT)

    # Delta Call mesh
    d1_mesh, _ = _compute_d1_d2(S_mesh, K_mesh, t_years, risk_free_rate, volatility, dividend_yield)
    delta_call_matrix = np.exp(-dividend_yield * t_years) * norm.cdf(d1_mesh)

    # 2. Matriz Strike vs Volatilidad
    Vol_mesh, K_vol_mesh = np.meshgrid(vols, strikes)
    calls_vol_matrix = black_scholes_price(spot_base, K_vol_mesh, t_years, risk_free_rate, Vol_mesh, dividend_yield, OptionType.CALL)
    puts_vol_matrix = black_scholes_price(spot_base, K_vol_mesh, t_years, risk_free_rate, Vol_mesh, dividend_yield, OptionType.PUT)

    return {
        "spots": [round(float(s), 2) for s in spots],
        "strikes": [round(float(k), 2) for k in strikes],
        "volatilities_pct": [round(float(v) * 100.0, 1) for v in vols],
        "spot_vs_strike": {
            "call_prices": np.round(calls_matrix, 2).tolist(),
            "put_prices": np.round(puts_matrix, 2).tolist(),
            "delta_call": np.round(delta_call_matrix, 3).tolist(),
        },
        "strike_vs_vol": {
            "call_prices": np.round(calls_vol_matrix, 2).tolist(),
            "put_prices": np.round(puts_vol_matrix, 2).tolist(),
        },
        "parameters": {
            "spot_base": round(spot_base, 2),
            "dte_days": round(dte_days, 1),
            "volatility_pct": round(volatility * 100.0, 1),
            "risk_free_rate_pct": round(risk_free_rate * 100.0, 2),
        },
    }


# ---------------------------------------------------------------------------
# Construcción e Interpolación de Superficie 3D de Volatilidad
# ---------------------------------------------------------------------------
def interpolate_iv_surface(
    raw_df: pd.DataFrame,
    spot_price: float,
    symbol: str = "",
    n_strike_points: int = 25,
    n_dte_points: int = 20,
) -> IVSurfaceData:
    """
    Interpola puntos dispersos de (Strike, DTE, IV) de mercado sobre una cuadrícula
    regular 2D usando spline/cúbica de SciPy para visualización tridimensional fluida.
    """
    clean_df = raw_df.dropna(subset=["strike", "dte", "implied_volatility"]).copy()
    clean_df = clean_df[
        (clean_df["strike"] > 0)
        & (clean_df["dte"] > 0)
        & (clean_df["implied_volatility"] > 0.02)
        & (clean_df["implied_volatility"] < 3.0)
    ]

    # Filtrar extremos ilíquidos fuera de 0.6x a 1.5x spot
    clean_df = clean_df[
        (clean_df["strike"] >= spot_price * 0.6)
        & (clean_df["strike"] <= spot_price * 1.5)
    ]

    if len(clean_df) < 12:
        # Puntos insuficientes en mercado real -> recurrir a superficie paramétrica enriquecida
        base_vol = float(clean_df["implied_volatility"].median()) if not clean_df.empty else 0.25
        return generate_parametric_iv_surface(spot_price, base_vol=base_vol, symbol=symbol)

    points = clean_df[["strike", "dte"]].values
    values = clean_df["implied_volatility"].values * 100.0  # en porcentaje

    strikes_grid = np.linspace(clean_df["strike"].min(), clean_df["strike"].max(), n_strike_points)
    dtes_grid = np.linspace(clean_df["dte"].min(), clean_df["dte"].max(), n_dte_points)

    K_mesh, DTE_mesh = np.meshgrid(strikes_grid, dtes_grid)

    # Interpolación cúbica con fallback lineal y nearest para evitar NaNs en los bordes
    grid_z = griddata(points, values, (K_mesh, DTE_mesh), method="linear")
    grid_nearest = griddata(points, values, (K_mesh, DTE_mesh), method="nearest")
    grid_z = np.where(np.isnan(grid_z), grid_nearest, grid_z)

    # Suavizado leve
    grid_z = np.clip(grid_z, 5.0, 250.0)

    return IVSurfaceData(
        symbol=symbol,
        spot_price=spot_price,
        is_synthetic=False,
        strikes=[round(float(k), 2) for k in strikes_grid],
        dtes=[round(float(d), 1) for d in dtes_grid],
        iv_matrix=np.round(grid_z, 2).tolist(),
        raw_points_count=len(clean_df),
        min_iv_pct=round(float(np.min(grid_z)), 1),
        max_iv_pct=round(float(np.max(grid_z)), 1),
        metadata={"data_source": "Yahoo Finance Options Chain (Interpolated)"},
    )


def generate_parametric_iv_surface(
    spot_price: float,
    base_vol: float = 0.25,
    symbol: str = "SIM",
    n_strike_points: int = 25,
    n_dte_points: int = 20,
) -> IVSurfaceData:
    """
    Genera una superficie de volatilidad implícita paramétrica realista basada en
    la estructura de sonrisa (volatility smile/skew) y estructura temporal (term structure).
    Ideal para acciones colombianas (BVC) o simulaciones teóricas sin cadena en vivo.
    """
    strikes = np.linspace(spot_price * 0.75, spot_price * 1.35, n_strike_points)
    dtes = np.linspace(7.0, 365.0, n_dte_points)

    K_mesh, DTE_mesh = np.meshgrid(strikes, dtes)
    T_mesh = DTE_mesh / 365.0
    moneyness = np.log(K_mesh / spot_price)

    # Modelo paramétrico tipo SVI / SABR simplificado:
    # 1. Sonrisa / Skew: asimetría negativa para renta variable (más volatilidad a la baja)
    skew = -0.15 * moneyness + 0.35 * (moneyness**2)
    # 2. Estructura temporal: atenuación de la curvatura a plazos largos
    term_decay = 1.0 / np.sqrt(np.maximum(T_mesh, 0.05))
    # 3. Volatilidad base anualizada
    surface_z = (base_vol + skew * 0.4 * np.minimum(term_decay, 2.5)) * 100.0
    surface_z = np.clip(surface_z, 8.0, 180.0)

    return IVSurfaceData(
        symbol=symbol,
        spot_price=spot_price,
        is_synthetic=True,
        strikes=[round(float(k), 2) for k in strikes],
        dtes=[round(float(d), 1) for d in dtes],
        iv_matrix=np.round(surface_z, 2).tolist(),
        raw_points_count=n_strike_points * n_dte_points,
        min_iv_pct=round(float(np.min(surface_z)), 1),
        max_iv_pct=round(float(np.max(surface_z)), 1),
        metadata={"data_source": "Modelo Paramétrico de Sonrisa y Estructura Temporal"},
    )
