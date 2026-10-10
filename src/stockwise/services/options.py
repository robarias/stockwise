"""
Servicio para la consulta de cadenas de opciones de mercado y orquestación
de análisis Black-Scholes y superficies de volatilidad.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

import pandas as pd
import yfinance as yf

from stockwise.analytics.options import (
    evaluate_contract,
    generate_parametric_iv_surface,
    generate_pricing_heatmap_matrix,
    interpolate_iv_surface,
)
from stockwise.domain.markets import is_colombian_ticker, resolve_ticker
from stockwise.domain.options import BlackScholesResult, IVSurfaceData, OptionType


def fetch_options_chain_data(
    symbol: str,
    max_expirations: int = 8,
) -> tuple[pd.DataFrame, float, bool]:
    """
    Obtiene las cadenas de opciones de mercado de Yahoo Finance.
    Devuelve (df_opciones, spot_price, tiene_opciones_reales).
    """
    clean_sym = resolve_ticker(symbol)

    # Si es acción colombiana, no tiene opciones cotizadas en Yahoo Finance
    if is_colombian_ticker(clean_sym):
        stock = yf.Ticker(clean_sym)
        spot = 0.0
        try:
            h = stock.history(period="5d")
            if not h.empty:
                spot = float(h["Close"].iloc[-1])
        except Exception:
            pass
        return pd.DataFrame(), spot, False

    stock = yf.Ticker(clean_sym)
    spot = 0.0
    try:
        info = stock.info or {}
        spot = float(info.get("currentPrice") or info.get("regularMarketPrice") or 0.0)
        if spot <= 0:
            h = stock.history(period="5d")
            if not h.empty:
                spot = float(h["Close"].iloc[-1])
    except Exception:
        pass

    try:
        expirations = stock.options or ()
    except Exception:
        expirations = ()

    if not expirations or spot <= 0:
        return pd.DataFrame(), spot, False

    today = datetime.now().date()
    rows: list[dict[str, Any]] = []

    # Recorrer expiraciones (máx max_expirations para mantener baja latencia)
    for exp_str in expirations[:max_expirations]:
        try:
            exp_date = datetime.strptime(exp_str, "%Y-%m-%d").date()
            dte = (exp_date - today).days
            if dte <= 0:
                continue

            chain = stock.option_chain(exp_str)

            # Calls
            if chain.calls is not None and not chain.calls.empty:
                for _, row in chain.calls.iterrows():
                    strike = float(row.get("strike", 0))
                    iv = float(row.get("impliedVolatility", 0))
                    if strike > 0 and iv > 0.01:
                        rows.append({
                            "contract_symbol": row.get("contractSymbol", ""),
                            "strike": strike,
                            "expiration": exp_str,
                            "dte": dte,
                            "option_type": "call",
                            "last_price": float(row.get("lastPrice", 0)),
                            "bid": float(row.get("bid", 0)),
                            "ask": float(row.get("ask", 0)),
                            "volume": int(row.get("volume", 0) or 0),
                            "open_interest": int(row.get("openInterest", 0) or 0),
                            "implied_volatility": iv,
                            "in_the_money": bool(row.get("inTheMoney", False)),
                        })

            # Puts
            if chain.puts is not None and not chain.puts.empty:
                for _, row in chain.puts.iterrows():
                    strike = float(row.get("strike", 0))
                    iv = float(row.get("impliedVolatility", 0))
                    if strike > 0 and iv > 0.01:
                        rows.append({
                            "contract_symbol": row.get("contractSymbol", ""),
                            "strike": strike,
                            "expiration": exp_str,
                            "dte": dte,
                            "option_type": "put",
                            "last_price": float(row.get("lastPrice", 0)),
                            "bid": float(row.get("bid", 0)),
                            "ask": float(row.get("ask", 0)),
                            "volume": int(row.get("volume", 0) or 0),
                            "open_interest": int(row.get("openInterest", 0) or 0),
                            "implied_volatility": iv,
                            "in_the_money": bool(row.get("inTheMoney", False)),
                        })
        except Exception:
            continue

    df = pd.DataFrame(rows)
    has_real = not df.empty and len(df) >= 10
    return df, spot, has_real


def get_options_surface_data(
    symbol: str,
    base_volatility: float | None = None,
) -> IVSurfaceData:
    """
    Obtiene los datos estructurados para renderizar la superficie 3D de volatilidad implícita.
    Si el activo tiene opciones en Yahoo Finance, interpola las cotizaciones reales;
    de lo contrario, recurre al modelo paramétrico con la volatilidad base indicada.
    """
    clean_sym = resolve_ticker(symbol)
    chain_df, spot, has_real = fetch_options_chain_data(clean_sym)

    if has_real and spot > 0:
        return interpolate_iv_surface(chain_df, spot_price=spot, symbol=clean_sym)

    # Fallback paramétrico para acciones colombianas o sin cadena de opciones
    if spot <= 0:
        spot = 100.0  # valor base de referencia
    vol = base_volatility if (base_volatility and base_volatility > 0) else 0.28
    return generate_parametric_iv_surface(spot_price=spot, base_vol=vol, symbol=clean_sym)


def get_pricing_heatmap_data(
    symbol: str,
    spot_price: float | None = None,
    dte_days: float = 30.0,
    volatility: float = 0.25,
    risk_free_rate: float = 0.045,
    dividend_yield: float = 0.0,
) -> dict[str, Any]:
    """Genera las matrices bidimensionales de precios teóricos y griegas para mapas de calor."""
    clean_sym = resolve_ticker(symbol)
    if spot_price is None or spot_price <= 0:
        _, s, _ = fetch_options_chain_data(clean_sym)
        spot_price = s if s > 0 else 100.0

    return generate_pricing_heatmap_matrix(
        spot_base=spot_price,
        dte_days=dte_days,
        volatility=volatility,
        risk_free_rate=risk_free_rate,
        dividend_yield=dividend_yield,
    )


def evaluate_option_scenario(
    symbol: str,
    strike: float,
    dte_days: float = 30.0,
    volatility: float = 0.25,
    option_type: str = "call",
    risk_free_rate: float = 0.045,
    spot_price: float | None = None,
) -> BlackScholesResult:
    """Evalúa un contrato específico y devuelve precios, valor intrínseco y griegas analíticas."""
    clean_sym = resolve_ticker(symbol)
    if spot_price is None or spot_price <= 0:
        _, s, _ = fetch_options_chain_data(clean_sym)
        spot_price = s if s > 0 else 100.0

    return evaluate_contract(
        spot=spot_price,
        strike=strike,
        dte_days=dte_days,
        volatility=volatility,
        risk_free_rate=risk_free_rate,
        option_type=OptionType(option_type.lower()),
    )
