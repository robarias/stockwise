"""
Pruebas unitarias para el módulo de opciones: Black-Scholes, Griegas,
superficies 3D de volatilidad implícita y mapas de calor.
"""

import numpy as np
import pandas as pd

from stockwise.analytics.options import (
    black_scholes_greeks,
    black_scholes_price,
    evaluate_contract,
    generate_parametric_iv_surface,
    generate_pricing_heatmap_matrix,
    implied_volatility,
    interpolate_iv_surface,
)
from stockwise.domain.options import OptionType
from stockwise.viz.options import (
    build_black_scholes_heatmap_figure,
    build_iv_surface_3d_figure,
    build_option_payoff_figure,
)


def test_black_scholes_known_values_and_parity():
    """Verifica precios teóricos estándar de libro y la paridad Put-Call estricta."""
    s = 100.0
    k = 100.0
    t = 1.0
    r = 0.05
    sig = 0.20

    call_p = black_scholes_price(s, k, t, r, sig, option_type=OptionType.CALL)
    put_p = black_scholes_price(s, k, t, r, sig, option_type=OptionType.PUT)

    # Valores conocidos de referencia: Call ~ 10.45, Put ~ 5.57
    assert 10.40 <= call_p <= 10.50
    assert 5.50 <= put_p <= 5.65

    # Paridad Put-Call: C - P = S - K * exp(-r * T)
    parity_diff = (call_p - put_p) - (s - k * np.exp(-r * t))
    assert abs(parity_diff) < 1e-7


def test_black_scholes_boundary_expiration():
    """Verifica que a T=0 la opción converja exactamente a su valor intrínseco."""
    s = 115.0
    k = 100.0
    call_itm = black_scholes_price(s, k, time_years=0.0, risk_free_rate=0.05, volatility=0.20, option_type=OptionType.CALL)
    put_otm = black_scholes_price(s, k, time_years=0.0, risk_free_rate=0.05, volatility=0.20, option_type=OptionType.PUT)

    assert call_itm == 15.0
    assert put_otm == 0.0


def test_black_scholes_greeks_properties():
    """Verifica las propiedades matemáticas fundamentales de las griegas."""
    s = 150.0
    k = 150.0
    t = 0.5  # 6 meses
    r = 0.045
    sig = 0.25

    g_call = black_scholes_greeks(s, k, t, r, sig, option_type=OptionType.CALL)
    g_put = black_scholes_greeks(s, k, t, r, sig, option_type=OptionType.PUT)

    # Delta: Call en (0, 1), Put en (-1, 0)
    assert 0.0 < g_call.delta < 1.0
    assert -1.0 < g_put.delta < 0.0
    # Relación de Delta: Delta_Call - Delta_Put = 1 (para dividend_yield = 0)
    assert abs((g_call.delta - g_put.delta) - 1.0) < 1e-5

    # Gamma y Vega son idénticos y estrictamente positivos para Call y Put
    assert g_call.gamma > 0.0
    assert abs(g_call.gamma - g_put.gamma) < 1e-7
    assert g_call.vega_1pct > 0.0
    assert abs(g_call.vega_1pct - g_put.vega_1pct) < 1e-7

    # Theta de una opción comprada at-the-money es negativa (pérdida de valor temporal)
    assert g_call.theta_daily < 0.0


def test_implied_volatility_inversion():
    """Verifica que la inversión numérica recupere la volatilidad original con precisión."""
    s = 100.0
    k = 105.0
    t = 0.25  # 3 meses
    r = 0.04
    target_sigma = 0.32

    market_p = float(black_scholes_price(s, k, t, r, target_sigma, option_type=OptionType.CALL))
    recovered_sigma = implied_volatility(market_p, s, k, t, r, option_type=OptionType.CALL)

    assert recovered_sigma is not None
    assert abs(recovered_sigma - target_sigma) < 0.005


def test_evaluate_contract_structure():
    """Verifica el contrato completo evaluado."""
    res = evaluate_contract(spot=120.0, strike=100.0, dte_days=45.0, volatility=0.22, option_type="call")
    d = res.to_dict()

    assert d["moneyness_status"] == "ITM (In-The-Money)"
    assert d["intrinsic_value"] == 20.0
    assert d["price"] > 20.0
    assert d["time_value"] > 0.0
    assert "delta" in d["greeks"]


def test_heatmap_matrix_generation():
    """Verifica la generación de matrices 2D para mapas de calor."""
    data = generate_pricing_heatmap_matrix(spot_base=180.0, dte_days=30.0, volatility=0.25, n_points=10)

    assert len(data["spots"]) == 10
    assert len(data["strikes"]) == 10
    assert len(data["spot_vs_strike"]["call_prices"]) == 10
    assert len(data["spot_vs_strike"]["call_prices"][0]) == 10
    assert len(data["spot_vs_strike"]["delta_call"]) == 10


def test_parametric_and_interpolated_iv_surface():
    """Verifica superficies 3D tanto sintéticas como interpoladas desde datos de mercado."""
    # 1. Paramétrica
    synth_surf = generate_parametric_iv_surface(spot_price=200.0, base_vol=0.30, symbol="TEST")
    assert synth_surf.is_synthetic is True
    assert len(synth_surf.strikes) == 25
    assert len(synth_surf.dtes) == 20
    assert len(synth_surf.iv_matrix) == 20
    assert synth_surf.min_iv_pct > 0.0

    # 2. Interpolada con DataFrame sintético
    raw_df = pd.DataFrame({
        "strike": [180.0, 190.0, 200.0, 210.0, 220.0] * 4,
        "dte": [15, 15, 15, 15, 15, 30, 30, 30, 30, 30, 60, 60, 60, 60, 60, 90, 90, 90, 90, 90],
        "implied_volatility": [0.35, 0.32, 0.30, 0.31, 0.33, 0.33, 0.30, 0.28, 0.29, 0.31,
                               0.31, 0.29, 0.27, 0.28, 0.30, 0.30, 0.28, 0.26, 0.27, 0.29],
    })
    interp_surf = interpolate_iv_surface(raw_df, spot_price=200.0, symbol="REAL_TEST")
    assert interp_surf.is_synthetic is False
    assert len(interp_surf.strikes) > 0
    assert len(interp_surf.iv_matrix) > 0


def test_plotly_figures_creation():
    """Verifica que las figuras de Plotly se instancien sin errores."""
    surf_data = generate_parametric_iv_surface(spot_price=100.0, base_vol=0.25)
    fig_3d = build_iv_surface_3d_figure(surf_data)
    assert fig_3d is not None
    assert len(fig_3d.data) == 1

    h_data = generate_pricing_heatmap_matrix(spot_base=100.0, n_points=8)
    fig_heat = build_black_scholes_heatmap_figure(h_data, view_type="call_prices")
    assert fig_heat is not None
    assert len(fig_heat.data) == 1

    fig_payoff = build_option_payoff_figure(spot=100.0, strike=105.0, premium=3.5, option_type="call", position="long")
    assert fig_payoff is not None
    assert len(fig_payoff.data) == 1
